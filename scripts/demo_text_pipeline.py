"""ASR + LLM text-only pipeline demo.

Records your voice, transcribes, gets PhoGPT response.
"""
import time
from pathlib import Path

import sounddevice as sd
import soundfile as sf
from rich.console import Console
from rich.panel import Panel

from shrike7.asr import VietnameseASR
from shrike7.llm import VietnameseLLM

console = Console()
SAMPLE_RATE = 16000
RECORD_DURATION = 5

console.print("[bold]Loading models...[/bold]")
asr = VietnameseASR(num_threads=4)
llm = VietnameseLLM(n_threads=8, n_gpu_layers=-1)
console.print("[green]✓ Both models loaded[/green]\n")

while True:
    input("\n>>> Press ENTER to record (5 seconds), or Ctrl+C to quit...")
    console.print(f"[yellow]🎙️  Recording {RECORD_DURATION}s...[/yellow]")
    audio = sd.rec(int(RECORD_DURATION * SAMPLE_RATE),
                   samplerate=SAMPLE_RATE, channels=1, dtype="float32")
    sd.wait()
    audio = audio.flatten()

    # Save for debug
    tmp_path = Path("/tmp/shrike7_last.wav")
    sf.write(str(tmp_path), audio, SAMPLE_RATE)
    console.print(f"[dim]Saved to {tmp_path}[/dim]")

    # 1. ASR
    t0 = time.perf_counter()
    asr_result = asr.transcribe(audio)
    t_asr = (time.perf_counter() - t0) * 1000

    console.print(Panel(
        f"[cyan]{asr_result.text}[/cyan]\n\n"
        f"[dim]ASR latency: {t_asr:.0f} ms[/dim]",
        title="🎤 Bạn nói",
        border_style="cyan",
    ))

    if not asr_result.text.strip():
        console.print("[red]Empty transcript — speak louder?[/red]")
        continue

    # 2. LLM
    t0 = time.perf_counter()
    llm_result = llm.generate(asr_result.text, max_tokens=120, temperature=0.7)
    t_llm = (time.perf_counter() - t0) * 1000

    console.print(Panel(
        f"[yellow]{llm_result.text}[/yellow]\n\n"
        f"[dim]LLM TTFT: {llm_result.ttft_ms:.0f} ms | "
        f"Total: {t_llm:.0f} ms | {llm_result.tokens_per_second:.1f} tok/s[/dim]",
        title="🤖 Shrike-7 trả lời",
        border_style="yellow",
    ))

    total = t_asr + t_llm
    console.print(f"\n[bold]End-to-end (text): {total:.0f} ms[/bold]")
