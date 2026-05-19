"""Benchmark PhoGPT-4B-Chat on a fixed Vietnamese prompt set.

Reports: TTFT distribution, tok/s distribution, peak memory.
"""
import json
import time
from pathlib import Path
from statistics import mean, median, stdev

import psutil
from rich.console import Console
from rich.progress import track
from rich.table import Table

from shrike7.llm import VietnameseLLM

console = Console()

EVAL_PROMPTS = [
    # Short factual
    "Thủ đô của Pháp là gì?",
    "Bao nhiêu giây trong một giờ?",
    "Ai là chủ tịch nước Việt Nam hiện tại?",
    # Medium reasoning
    "Tại sao bầu trời có màu xanh?",
    "Giải thích sự khác nhau giữa CPU và GPU.",
    "Làm thế nào để học tốt một ngôn ngữ mới?",
    # Longer instruction
    "Viết một đoạn văn 3 câu về mùa thu Hà Nội.",
    "Liệt kê 5 mẹo nấu phở bò ngon.",
    "Tóm tắt ngắn gọn về cuộc cách mạng công nghiệp lần thứ 4.",
    # Command-like (typical voice assistant)
    "Đặt báo thức lúc 7 giờ sáng mai.",
    "Cho tôi biết thời tiết hôm nay.",
    "Mở ứng dụng Zalo.",
    # Edge cases
    "Bạn có thể giúp tôi viết một bài thơ về tình bạn?",
    "Kể cho tôi một câu chuyện cười ngắn.",
    "Bạn nghĩ gì về tương lai của AI tại Việt Nam?",
]

console.print("[bold]Loading PhoGPT-4B-Chat Q4_K_M...[/bold]")
llm = VietnameseLLM(n_threads=8, n_gpu_layers=-1, verbose=False)
console.print("[green]✓ Loaded[/green]\n")

proc = psutil.Process()
mem_before_mb = proc.memory_info().rss / (1024 * 1024)

# Warm-up
_ = llm.generate("Hôm nay là thứ mấy?", max_tokens=20)

ttfts, totals, tps_list, n_completions = [], [], [], []
peak_mem_mb = mem_before_mb
results = []

for prompt in track(EVAL_PROMPTS, description="Benchmarking..."):
    r = llm.generate(prompt, max_tokens=128, temperature=0.7)
    ttfts.append(r.ttft_ms)
    totals.append(r.total_latency_ms)
    tps_list.append(r.tokens_per_second)
    n_completions.append(r.n_completion_tokens)
    peak_mem_mb = max(peak_mem_mb, proc.memory_info().rss / (1024 * 1024))
    results.append({
        "prompt": prompt,
        "response": r.text,
        "ttft_ms": r.ttft_ms,
        "total_ms": r.total_latency_ms,
        "tok_per_s": r.tokens_per_second,
        "n_completion": r.n_completion_tokens,
    })

# Report
def summary(vals):
    return {
        "mean": mean(vals),
        "median": median(vals),
        "p95": sorted(vals)[int(len(vals) * 0.95)],
        "stdev": stdev(vals) if len(vals) > 1 else 0,
        "min": min(vals),
        "max": max(vals),
    }

ttft_s = summary(ttfts)
total_s = summary(totals)
tps_s = summary(tps_list)

table = Table(title="LLM Benchmark — PhoGPT-4B-Chat Q4_K_M")
table.add_column("Metric", style="cyan")
table.add_column("Mean", justify="right", style="yellow")
table.add_column("Median", justify="right")
table.add_column("P95", justify="right", style="magenta")
table.add_column("Min", justify="right", style="green")
table.add_column("Max", justify="right", style="red")

table.add_row("TTFT (ms)",
              f"{ttft_s['mean']:.0f}", f"{ttft_s['median']:.0f}",
              f"{ttft_s['p95']:.0f}", f"{ttft_s['min']:.0f}", f"{ttft_s['max']:.0f}")
table.add_row("Total latency (ms)",
              f"{total_s['mean']:.0f}", f"{total_s['median']:.0f}",
              f"{total_s['p95']:.0f}", f"{total_s['min']:.0f}", f"{total_s['max']:.0f}")
table.add_row("Throughput (tok/s)",
              f"{tps_s['mean']:.1f}", f"{tps_s['median']:.1f}",
              f"{tps_s['p95']:.1f}", f"{tps_s['min']:.1f}", f"{tps_s['max']:.1f}")
table.add_row("Avg completion tokens",
              f"{mean(n_completions):.0f}", "", "", "", "")
table.add_row("Peak memory (MB)", f"{peak_mem_mb:.0f}", "", "", "", "")

console.print(table)

# Save
out_dir = Path(__file__).parent / "results"
out_dir.mkdir(exist_ok=True)
out_file = out_dir / "llm_d2_baseline_mac_m4.json"
out_file.write_text(json.dumps({
    "model": "PhoGPT-4B-Chat-Q4_K_M",
    "device": "Mac 4 (Metal)",
    "n_prompts": len(EVAL_PROMPTS),
    "ttft_ms": ttft_s,
    "total_latency_ms": total_s,
    "tokens_per_second": tps_s,
    "peak_memory_mb": peak_mem_mb,
    "samples": results,
}, ensure_ascii=False, indent=2))
console.print(f"\n[green]✓ Saved → {out_file}[/green]")
