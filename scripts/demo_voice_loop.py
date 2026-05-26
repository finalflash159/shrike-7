from __future__ import annotations

import argparse
from collections.abc import Sequence

from rich.console import Console
from rich.panel import Panel

from shrike7.asr import SpeechDetector
from shrike7.asr.robust_asr import RobustASR
from shrike7.asr.whisper_onnx import VietnameseASR
from shrike7.core import EndpointConfig, SoundDevicePlayer, record_until_silence
from shrike7.core.pipeline import VoicePipeline
from shrike7.llm import LocalLlamaCppLLM
from shrike7.llm.registry import DEFAULT_LLM_MODEL_KEY, LLM_MODEL_REGISTRY
from shrike7.tts import VietnameseTTS

console = Console()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the local Shrike-7 voice loop.")
    parser.add_argument(
        "--llm-model",
        default=DEFAULT_LLM_MODEL_KEY,
        choices=sorted(LLM_MODEL_REGISTRY),
        help="LLM registry key to load.",
    )
    parser.add_argument("--voice", default="NF", help="TTS voice/speaker id.")
    parser.add_argument("--endpoint-silence-ms", type=int, default=700)
    parser.add_argument("--max-record-ms", type=int, default=10000)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    detector = SpeechDetector()
    asr = RobustASR(asr=VietnameseASR(), vad=detector)
    llm = LocalLlamaCppLLM(model_key=args.llm_model, n_threads=8, n_gpu_layers=-1)
    tts = VietnameseTTS(voice=args.voice)
    player = SoundDevicePlayer()

    pipeline = VoicePipeline(asr=asr, llm=llm, tts=tts)
    config = EndpointConfig(
        endpoint_silence_ms=args.endpoint_silence_ms,
        max_record_ms=args.max_record_ms,
    )

    console.print(f"[green]Voice loop ready[/green] LLM={args.llm_model} voice={args.voice}")

    while True:
        input("\nPress ENTER and speak. Ctrl+C to quit.")
        audio = record_until_silence(detector, config=config)

        for event in pipeline.turn_streaming(audio, audio_sink=player):
            if event.type == "asr":
                console.print(Panel(event.text or "<empty>", title="ASR"))
            elif event.type == "audio":
                console.print(f"[dim]Played chunk:[/dim] {event.text}")
            elif event.type == "tts":
                ttfa_ms = event.metadata.get("ttfa_ms") if event.metadata else None
                suffix = f" ({ttfa_ms:.0f} ms TTFA)" if ttfa_ms is not None else ""
                console.print(f"[green]Speaking chunk:[/green] {event.text}{suffix}")
            elif event.type == "error":
                console.print(f"[red]Streaming error:[/red] {event.text}")
            elif event.type == "done":
                console.print(f"\n[dim]Done in {event.latency_ms:.0f} ms[/dim]")


if __name__ == "__main__":
    raise SystemExit(main())
