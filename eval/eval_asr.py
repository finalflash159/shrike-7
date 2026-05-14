"""Compute WER on the Vietnamese ASR eval slice."""
import json
from pathlib import Path

from jiwer import cer, wer
from rich.console import Console
from rich.progress import track

from shrike7.asr import VietnameseASR

console = Console()
DATA_DIR = Path(__file__).parent.parent / "data" / "fleurs_vi"

manifest = json.loads((DATA_DIR / "manifest.json").read_text())
console.print(f"Loaded manifest with {len(manifest)} samples\n")

asr = VietnameseASR(num_threads=4)
console.print("[green]✓ ASR ready[/green]\n")

results = []
total_audio = 0.0
total_latency = 0.0

# Warmup
_ = asr.transcribe_file(DATA_DIR / manifest[0]["filename"])

for entry in track(manifest, description="Transcribing..."):
    r = asr.transcribe_file(DATA_DIR / entry["filename"])
    results.append({
        "filename": entry["filename"],
        "ground_truth": entry["ground_truth"],
        "prediction": r.text,
        "latency_ms": r.latency_ms,
        "audio_ms": r.audio_duration_ms,
    })
    total_audio += r.audio_duration_ms
    total_latency += r.latency_ms

refs = [r["ground_truth"].lower().strip() for r in results]
hyps = [r["prediction"].lower().strip() for r in results]

overall_wer = wer(refs, hyps)
overall_cer = cer(refs, hyps)
avg_rtf = total_latency / max(total_audio, 1.0)

console.print("\n[bold]=== Results ===[/bold]")
console.print(f"WER: [yellow]{overall_wer*100:.2f}%[/yellow]")
console.print(f"CER: [yellow]{overall_cer*100:.2f}%[/yellow]")
console.print(f"Avg latency/sample: {total_latency/len(results):.0f} ms")
console.print(f"Avg RTF: {avg_rtf:.3f}")

# Save detailed results
out_dir = Path(__file__).parent / "results"
out_dir.mkdir(exist_ok=True)
(out_dir / "asr_d1_baseline.json").write_text(
    json.dumps({
        "wer": overall_wer,
        "cer": overall_cer,
        "avg_rtf": avg_rtf,
        "num_samples": len(results),
        "samples": results,
    }, ensure_ascii=False, indent=2)
)
console.print("\n[green]Saved -> eval/results/asr_d1_baseline.json[/green]")
