"""PhoWhisper-tiny ONNX"""
from pathlib import Path

from rich.console import Console
from rich.table import Table

from shrike7.asr import VietnameseASR

console = Console()
test_dir = Path(__file__).parent.parent / "data" / "test_audio"
test_files = sorted(test_dir.glob("sample_*.wav"))

if not test_files:
    console.print("[red]No test audio. Please run:[/red] [green]uv run python scripts/record_test_audio.py[/green]")
    raise SystemExit(1)

console.print("[bold]Loading PhoWhisper-tiny ONNX ...[/bold]")
asr = VietnameseASR()
console.print("[green]Loaded[/green]")

# Warm-up run
_ = asr.transcribe_file(test_files[0])

table = Table(title="ASR Smoke Test Results")
table.add_column("File", style="cyan")
table.add_column("Audio (ms)", justify="right")
table.add_column("Latency (ms)", justify="right", style="yellow")
table.add_column("RTF", justify="right", style="magenta")
table.add_column("Transcript", style="white")

for f in test_files:
    result = asr.transcribe_file(f)
    table.add_row(
        f.name,
        f"{result.audio_duration_ms:.0f}",
        f"{result.latency_ms:.0f}",
        f"{result.rtf:.2f}",
        result.text,
    )

console.print(table)
