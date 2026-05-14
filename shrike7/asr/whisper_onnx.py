from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import onnxruntime as ort
from transformers import WhisperProcessor


@dataclass
class ASRResult:
    text: str
    latency_ms: float
    audio_duration_ms: float
    rtf: float  # Real-Time Factor: latency / audio_duration

    def to_dict(self) -> dict:
        return asdict(self)


class VietnameseASR:
    DEFAULT_MODEL_DIR = Path(__file__).resolve().parents[2] / "models" / "phowhisper-tiny-onnx"
    SAMPLING_RATE = 16000

    def __init__(
        self,
        model_dir: Path | None = None,
        num_threads: int = 4,
        providers: list[str] | None = None,
    ):
        self.model_dir = Path(model_dir or self.DEFAULT_MODEL_DIR)
        if not self.model_dir.exists():
            raise FileNotFoundError(
                f"Model directory not found: {self.model_dir}\n"
                "Run: uv run python scripts/download_phowhisper.py"
            )

        sess_opts = ort.SessionOptions()
        sess_opts.intra_op_num_threads = num_threads
        sess_opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

        # CPU only for now, can add CUDA/DirectML/CoreML providers later.
        self.providers = providers or ["CPUExecutionProvider"]

        self.onnx_dir = self.model_dir / "onnx"
        encoder_path = self.onnx_dir / "encoder_model.onnx"
        decoder_path = self.onnx_dir / "decoder_model.onnx"

        missing = [path for path in (encoder_path, decoder_path) if not path.exists()]
        if missing:
            missing_list = "\n".join(str(path) for path in missing)
            raise FileNotFoundError(f"ONNX model files not found:\n{missing_list}")

        self.encoder = ort.InferenceSession(
            str(encoder_path),
            sess_options=sess_opts,
            providers=self.providers,
        )
        self.decoder = ort.InferenceSession(
            str(decoder_path),
            sess_options=sess_opts,
            providers=self.providers,
        )
        self.processor = WhisperProcessor.from_pretrained(
            str(self.model_dir),
            local_files_only=True,
        )

        # Special token IDs used to tell Whisper what task to perform.
        self.decoder_start_token = self.processor.tokenizer.convert_tokens_to_ids(
            "<|startoftranscript|>"
        )
        self.eos_token = self.processor.tokenizer.eos_token_id
        self.lang_token = self.processor.tokenizer.convert_tokens_to_ids("<|vi|>")
        self.transcribe_token = self.processor.tokenizer.convert_tokens_to_ids("<|transcribe|>")
        self.notimestamps_token = self.processor.tokenizer.convert_tokens_to_ids("<|notimestamps|>")
        self.suppress_tokens, self.begin_suppress_tokens = self._load_suppression_tokens()

    def _load_suppression_tokens(self) -> tuple[set[int], set[int]]:
        config_path = self.model_dir / "generation_config.json"
        if not config_path.exists():
            return set(), set()

        with config_path.open() as f:
            config = json.load(f)

        suppress_tokens = {
            token_id
            for token_id in config.get("suppress_tokens", [])
            if isinstance(token_id, int) and token_id >= 0
        }
        begin_suppress_tokens = {
            token_id
            for token_id in config.get("begin_suppress_tokens", [])
            if isinstance(token_id, int) and token_id >= 0
        }
        return suppress_tokens, begin_suppress_tokens

    def _preprocess(self, audio: np.ndarray) -> np.ndarray:
        """Convert 1D float32 16kHz audio into Whisper log-mel input features."""
        features = self.processor.feature_extractor(
            audio,
            sampling_rate=self.SAMPLING_RATE,
            return_tensors="np",
        ).input_features
        return features.astype(np.float32)

    def _decode_greedy(self, encoder_hidden: np.ndarray, max_new_tokens: int = 128) -> list[int]:
        """Decode with greedy search for the D1 smoke test."""
        decoder_ids = np.array(
            [
                [
                    self.decoder_start_token,
                    self.lang_token,
                    self.transcribe_token,
                    self.notimestamps_token,
                ]
            ],
            dtype=np.int64,
        )
        initial_length = decoder_ids.shape[1]

        for _ in range(max_new_tokens):
            outputs = self.decoder.run(
                None,
                {
                    "input_ids": decoder_ids,
                    "encoder_hidden_states": encoder_hidden,
                },
            )
            logits = outputs[0]  # (1, seq_len, vocab_size)
            next_token_logits = logits[0, -1].copy()

            if self.suppress_tokens:
                next_token_logits[list(self.suppress_tokens)] = -np.inf
            if decoder_ids.shape[1] == initial_length and self.begin_suppress_tokens:
                next_token_logits[list(self.begin_suppress_tokens)] = -np.inf

            next_token_id = int(np.argmax(next_token_logits))

            decoder_ids = np.concatenate(
                [decoder_ids, np.array([[next_token_id]], dtype=np.int64)],
                axis=1,
            )

            if next_token_id == self.eos_token:
                break

        return decoder_ids[0].tolist()

    def transcribe(self, audio: np.ndarray) -> ASRResult:
        if audio.ndim != 1:
            raise ValueError(f"Audio must be 1D mono, got shape {audio.shape}")

        audio = audio.astype(np.float32, copy=False)
        audio_duration_ms = len(audio) / self.SAMPLING_RATE * 1000
        start = time.perf_counter()

        input_features = self._preprocess(audio)
        encoder_out = self.encoder.run(None, {"input_features": input_features})
        encoder_hidden = encoder_out[0]

        token_ids = self._decode_greedy(encoder_hidden)
        text = self.processor.tokenizer.decode(
            token_ids,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        ).strip()

        latency_ms = (time.perf_counter() - start) * 1000
        rtf = latency_ms / max(audio_duration_ms, 1.0)

        return ASRResult(
            text=text,
            latency_ms=latency_ms,
            audio_duration_ms=audio_duration_ms,
            rtf=rtf,
        )

    def transcribe_file(self, path: str | Path) -> ASRResult:
        """Load an audio file and transcribe it."""
        import librosa

        audio, _sample_rate = librosa.load(str(path), sr=self.SAMPLING_RATE, mono=True)
        return self.transcribe(audio)
