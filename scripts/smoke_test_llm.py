"""Smoke test: load PhoGPT-4B-Chat Q4_K_M and run 5 Vietnamese prompts."""
from rich.console import Console
from rich.table import Table

from shrike7.llm import VietnameseLLM

console = Console()

TEST_PROMPTS = [
    "Thủ đô của Việt Nam là gì?",
    "Hãy giới thiệu ngắn về bản thân bạn.",
    "Mấy giờ rồi?",
    "Làm sao để đặt một báo thức?",
    "Kể cho tôi một câu chuyện cười ngắn về lập trình viên.",
]

console.print("[bold]Loading PhoGPT-4B-Chat Q4_K_M...[/bold]")
llm = VietnameseLLM(n_threads=8, n_gpu_layers=-1)  # all on Metal
console.print("[green]✓ Model loaded[/green]\n")

# Warm-up (first call is slower due to KV cache init)
console.print("[dim]Warming up...[/dim]")
_ = llm.generate("Xin chào", max_tokens=20)
console.print("[dim]Warm-up done.[/dim]\n")

table = Table(title="LLM Smoke Test — PhoGPT-4B-Chat Q4_K_M", show_lines=True)
table.add_column("Prompt", style="cyan", width=30)
table.add_column("Response", style="white", width=50)
table.add_column("TTFT (ms)", justify="right", style="yellow")
table.add_column("Total (ms)", justify="right", style="yellow")
table.add_column("tok/s", justify="right", style="magenta")
table.add_column("# tok", justify="right")

for prompt in TEST_PROMPTS:
    r = llm.generate(prompt, max_tokens=120, temperature=0.7)
    table.add_row(
        prompt,
        r.text[:200] + ("..." if len(r.text) > 200 else ""),
        f"{r.ttft_ms:.0f}",
        f"{r.total_latency_ms:.0f}",
        f"{r.tokens_per_second:.1f}",
        str(r.n_completion_tokens),
    )

console.print(table)
