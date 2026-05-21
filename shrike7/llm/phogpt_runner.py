from __future__ import annotations

import time
from collections.abc import Iterator
from dataclasses import asdict, dataclass
from pathlib import Path

from llama_cpp import Llama

# Official VinAI prompt template for PhoGPT-4B-Chat
PROMPT_TEMPLATE = "### Câu hỏi: {prompt}\n### Trả lời:"
STOP_SEQUENCES = ["### Câu hỏi:"]

# Persona injected into first turn
SHRIKE7_PERSONA = (
    "Bạn là Shrike-7, trợ lý ảo tiếng Việt thông minh, thân thiện. "
    "Trả lời súc tích dưới 50 từ. Nếu không biết, hãy nói rằng bạn không biết."
)


@dataclass
class LLMResult:
    text: str
    prompt: str
    n_prompt_tokens: int
    n_completion_tokens: int
    ttft_ms: float  # Time To First Token
    total_latency_ms: float
    tokens_per_second: float

    def to_dict(self) -> dict:
        return asdict(self)


class VietnameseLLM:
    """Wrapper around llama.cpp for PhoGPT-4B-Chat.

    Note: PhoGPT uses MPT (not Llama), llama.cpp supports MPT
    natively:
        - ALiBi positional encoding (no RoPE)
        - Vocab size 20480 (Vietnamese-optimized)
        - 8K context window
    """

    DEFAULT_MODEL_PATH = (
        Path(__file__).resolve().parents[2]
        / "models"
        / "phogpt-4b-chat-gguf"
        / "PhoGPT-4B-Chat-Q4_K_M.gguf"
    )

    def __init__(
        self,
        model_path: str | Path | None = None,
        n_ctx: int = 2048,
        n_threads: int = 4,
        n_gpu_layers: int = -1,  # -1 means all layers on GPU (if supported)
        seed: int = 42,
        verbose: bool = False,
    ):
        model_path = Path(model_path or self.DEFAULT_MODEL_PATH)
        if not model_path.exists():
            raise FileNotFoundError(
                f"Model file not found: {model_path}\n"
                "Run: uv run python scripts/download_phogpt.py"
            )

        self.model_path = model_path
        self.n_ctx = n_ctx
        self.llm = Llama(
            model_path=str(model_path),
            n_ctx=n_ctx,
            n_threads=n_threads,
            n_gpu_layers=n_gpu_layers,
            seed=seed,
            verbose=verbose,
            # MPT specific parameters tuning
            use_mlock=False,
        )

    @staticmethod
    def _build_prompt(user_msg: str, inject_persona: bool = True) -> str:
        if inject_persona:
            user_msg = f"{SHRIKE7_PERSONA}\n\nCâu hỏi của tôi: {user_msg}"
        return PROMPT_TEMPLATE.format(prompt=user_msg)

    @staticmethod
    def _validate_generation_args(
        user_msg: str,
        max_tokens: int,
        temperature: float,
        top_p: float,
    ) -> None:
        if not user_msg.strip():
            raise ValueError("user_msg must not be empty")
        if max_tokens <= 0:
            raise ValueError("max_tokens must be greater than 0")
        if temperature < 0:
            raise ValueError("temperature must be non-negative")
        if not 0 < top_p <= 1:
            raise ValueError("top_p must be in the range (0, 1]")

    @staticmethod
    def _chunk_text(chunk: dict) -> str:
        choices = chunk.get("choices", [])
        if not choices:
            return ""
        return choices[0].get("text", "")

    def generate(
        self,
        user_msg: str,
        max_tokens: int = 128,
        temperature: float = 0.7,
        top_p: float = 0.95,
        inject_persona: bool = True,
    ) -> LLMResult:
        self._validate_generation_args(user_msg, max_tokens, temperature, top_p)
        prompt = self._build_prompt(user_msg, inject_persona)
        t0 = time.perf_counter()
        first_token_time: float | None = None
        chunks: list[str] = []

        for chunk in self.llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=STOP_SEQUENCES,
            stream=True,
        ):
            tok_text = self._chunk_text(chunk)
            if first_token_time is None and tok_text:
                first_token_time = time.perf_counter()
            if tok_text:
                chunks.append(tok_text)

        t1 = time.perf_counter()

        n_prompt = len(self.llm.tokenize(prompt.encode("utf-8")))
        raw_completion = "".join(chunks)
        completion_text = raw_completion.strip()
        n_completion = len(self.llm.tokenize(raw_completion.encode("utf-8"), add_bos=False))
        total_latency_ms = (t1 - t0) * 1000
        ttft_ms = (first_token_time - t0) * 1000 if first_token_time else total_latency_ms

        # Approximate post-TTFT decode throughput; streaming chunks are not guaranteed token-sized.
        gen_time = (t1 - first_token_time) if first_token_time else (t1 - t0)
        tps_tokens = max(n_completion - 1, 0) if first_token_time else n_completion
        tps = tps_tokens / gen_time if gen_time > 0 else 0.0

        return LLMResult(
            text=completion_text,
            prompt=prompt,
            n_prompt_tokens=n_prompt,
            n_completion_tokens=n_completion,
            ttft_ms=ttft_ms,
            total_latency_ms=total_latency_ms,
            tokens_per_second=tps,
        )

    def generate_stream(
        self,
        user_msg: str,
        max_tokens: int = 128,
        temperature: float = 0.7,
        top_p: float = 0.95,
        inject_persona: bool = True,
    ) -> Iterator[str]:
        # Use for D7
        self._validate_generation_args(user_msg, max_tokens, temperature, top_p)
        prompt = self._build_prompt(user_msg, inject_persona=inject_persona)

        for chunk in self.llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=STOP_SEQUENCES,
            stream=True,
        ):
            tok_text = self._chunk_text(chunk)
            if tok_text:
                yield tok_text
