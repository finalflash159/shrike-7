import sys
import time
from shrike7.llm import VietnameseLLM
from rich.console import Console

console = Console()
llm = VietnameseLLM(n_threads=8, n_gpu_layers=-1)
console.print("[green]✓ Model ready[/green]\n")

PROMPT = "Giải thích ngắn gọn về trí tuệ nhân tạo cho tôi học sinh cấp 2."

console.print(f"[bold cyan]Câu hỏi: [/bold cyan] {PROMPT}\n")
console.print(f"[bold yellow]Shrike-7: [/bold yellow] ", end="")

t0 = time.perf_counter()
first_token_time = None
n_tokens = 0

for chunk in llm.generate_stream(PROMPT, max_tokens=200, temperature=0.7):
    if first_token_time is None:
        first_token_time = time.perf_counter()

    print(chunk, end="", flush=True)
    n_tokens +=1

t1 = time.perf_counter()
ttft = (first_token_time - t0) * 1000
total_latency = (t1 - t0) * 1000
gen = (t1 - first_token_time) * 1000

console.print(f"\n\n[dim]TTFT: {ttft:.0f} ms | Total latency: {total_latency:.0f} ms | Gen time: {gen:.0f} ms | Tokens: {n_tokens}[/dim]")
