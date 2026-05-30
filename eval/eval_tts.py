"""Benchmark local Vietnamese TTS engines on a fixed prompt set."""

from __future__ import annotations

import argparse
import json
import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean, median
from typing import Any

import numpy as np
from rich.console import Console
from rich.progress import track
from rich.table import Table

from shrike7.tts import (
    TIER_A_TTS_MODEL_KEYS,
    TIER_B_TTS_MODEL_KEYS,
    TTS_MODEL_REGISTRY,
    TTSRuntimeUnavailableError,
    create_tts_engine,
)
from shrike7.tts.registry import DEFAULT_TTS_MODEL_KEY, get_tts_model_config

console = Console(width=180)
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROMPT_PATH = REPO_ROOT / "eval" / "prompts" / "tts_bakeoff_vi.jsonl"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "eval" / "results"


@dataclass(frozen=True)
class TTSPrompt:
    prompt_id: str
    category: str
    text: str


def load_prompts(path: Path, limit: int | None = None) -> list[TTSPrompt]:
    prompts: list[TTSPrompt] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            try:
                prompts.append(
                    TTSPrompt(
                        prompt_id=str(payload["id"]),
                        category=str(payload["category"]),
                        text=str(payload["text"]),
                    )
                )
            except KeyError as exc:
                raise ValueError(f"{path}:{line_no} missing field: {exc}") from exc
            if limit is not None and len(prompts) >= limit:
                break

    if not prompts:
        raise ValueError(f"No TTS prompts loaded from {path}")
    return prompts


def dedupe_model_keys(model_keys: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for model_key in model_keys:
        if model_key in seen:
            continue
        seen.add(model_key)
        result.append(model_key)
    return result


def parse_model_list(values: Sequence[str]) -> list[str]:
    model_keys: list[str] = []
    for value in values:
        model_keys.extend(part.strip() for part in value.split(",") if part.strip())

    unknown = sorted(set(model_keys) - set(TTS_MODEL_REGISTRY))
    if unknown:
        valid = ", ".join(sorted(TTS_MODEL_REGISTRY))
        raise ValueError(f"Unknown TTS model key(s): {', '.join(unknown)}. Valid keys: {valid}")
    return model_keys


def select_model_keys(model_keys: Sequence[str], tier_a: bool, tier_b: bool = False) -> list[str]:
    selected: list[str] = []
    if tier_a:
        selected.extend(TIER_A_TTS_MODEL_KEYS)
    if tier_b:
        selected.extend(TIER_B_TTS_MODEL_KEYS)
    selected.extend(model_keys)
    if not selected:
        selected.append(DEFAULT_TTS_MODEL_KEY)
    return dedupe_model_keys(selected)


def summarize(values: Sequence[float]) -> dict[str, float]:
    sorted_values = sorted(values)
    p95_index = min(int(len(sorted_values) * 0.95), len(sorted_values) - 1)
    return {
        "mean": mean(values),
        "median": median(values),
        "p95": sorted_values[p95_index],
        "min": min(values),
        "max": max(values),
    }


def get_current_memory_mb() -> float | None:
    try:
        import psutil
    except ImportError:
        return None
    return psutil.Process().memory_info().rss / (1024 * 1024)


def clipping_ratio(audio: np.ndarray, threshold: float = 0.995) -> float:
    if audio.size == 0:
        return 0.0
    return float(np.mean(np.abs(audio) >= threshold))


def run_model_eval(
    model_key: str,
    prompts: Sequence[TTSPrompt],
    *,
    voice: str | None,
    skip_unimplemented: bool,
) -> dict[str, Any] | None:
    config = get_tts_model_config(model_key)

    console.print(f"\n[bold]Loading[/bold] {model_key} ({config.runner})")
    load_start = time.perf_counter()
    try:
        engine = create_tts_engine(model_key, voice=voice, lazy=False)
    except (NotImplementedError, TTSRuntimeUnavailableError) as exc:
        message = f"{model_key}: {exc}"
        if skip_unimplemented:
            console.print(f"[yellow]Skipping[/yellow] {message}")
            return {
                "model": model_key,
                "role": config.role,
                "runner": config.runner,
                "status": "skipped",
                "skip_reason": str(exc),
                "source_url": config.source_url,
            }
        raise
    load_ms = (time.perf_counter() - load_start) * 1000

    rows: list[dict[str, Any]] = []
    peak_memory_mb = get_current_memory_mb()

    for prompt in track(prompts, description=f"Benchmarking {model_key}..."):
        try:
            result = engine.synthesize(prompt.text, voice=voice)
            audio = result.audio
            row = {
                "id": prompt.prompt_id,
                "category": prompt.category,
                "text": prompt.text,
                "status": "ok",
                "sample_rate": result.sample_rate,
                "n_samples": int(len(audio)),
                "latency_ms": result.latency_ms,
                "audio_duration_ms": result.audio_duration_ms,
                "rtf": result.rtf,
                "voice": result.voice,
                "engine": result.engine,
                "peak_abs": float(np.max(np.abs(audio))) if audio.size else 0.0,
                "clipping_ratio": clipping_ratio(audio),
            }
        except Exception as exc:
            row = {
                "id": prompt.prompt_id,
                "category": prompt.category,
                "text": prompt.text,
                "status": "error",
                "error": f"{type(exc).__name__}: {exc}",
            }
        rows.append(row)
        current_memory_mb = get_current_memory_mb()
        if current_memory_mb is not None:
            peak_memory_mb = max(peak_memory_mb or current_memory_mb, current_memory_mb)

    ok_rows = [row for row in rows if row["status"] == "ok"]
    error_rows = [row for row in rows if row["status"] != "ok"]
    if not ok_rows:
        return {
            "model": model_key,
            "role": config.role,
            "runner": config.runner,
            "status": "failed",
            "load_ms": load_ms,
            "errors": rows,
            "source_url": config.source_url,
        }

    latencies = [float(row["latency_ms"]) for row in ok_rows]
    rtfs = [float(row["rtf"]) for row in ok_rows]
    durations = [float(row["audio_duration_ms"]) for row in ok_rows]
    clipping = [float(row["clipping_ratio"]) for row in ok_rows]

    return {
        "model": model_key,
        "role": config.role,
        "runner": config.runner,
        "status": "ok" if not error_rows else "partial",
        "license": config.license,
        "source_url": config.source_url,
        "load_ms": load_ms,
        "latency_ms": summarize(latencies),
        "rtf": summarize(rtfs),
        "audio_duration_ms": summarize(durations),
        "mean_clipping_ratio": mean(clipping),
        "non_empty_rate": sum(row["n_samples"] > 0 for row in ok_rows) / len(rows),
        "error_rate": len(error_rows) / len(rows),
        "peak_memory_mb": peak_memory_mb,
        "rows": rows,
    }


def render_summary(results: Sequence[dict[str, Any]]) -> None:
    table = Table(title="Shrike-7 TTS Bakeoff", show_lines=True)
    table.add_column("Model", style="cyan")
    table.add_column("Role")
    table.add_column("Status")
    table.add_column("Load ms", justify="right")
    table.add_column("Lat p50", justify="right")
    table.add_column("Lat p95", justify="right")
    table.add_column("RTF p50", justify="right")
    table.add_column("RTF p95", justify="right")
    table.add_column("Non-empty", justify="right")
    table.add_column("Err", justify="right")
    table.add_column("Peak MB", justify="right")

    for result in results:
        if result["status"] == "skipped":
            table.add_row(
                result["model"],
                result["role"],
                "skipped",
                "n/a",
                "n/a",
                "n/a",
                "n/a",
                "n/a",
                "n/a",
                "n/a",
                "n/a",
            )
            continue

        latency = result.get("latency_ms", {})
        rtf = result.get("rtf", {})
        peak_memory = result.get("peak_memory_mb")
        table.add_row(
            result["model"],
            result["role"],
            result["status"],
            f"{result.get('load_ms', 0):.0f}",
            f"{latency.get('median', 0):.0f}",
            f"{latency.get('p95', 0):.0f}",
            f"{rtf.get('median', 0):.2f}",
            f"{rtf.get('p95', 0):.2f}",
            f"{result.get('non_empty_rate', 0):.1%}",
            f"{result.get('error_rate', 0):.1%}",
            "n/a" if peak_memory is None else f"{peak_memory:.0f}",
        )

    console.print(table)


def write_outputs(results: Sequence[dict[str, Any]], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"tts_bakeoff_{stamp}.json"
    md_path = output_dir / f"tts_bakeoff_{stamp}.md"

    json_path.write_text(
        json.dumps({"created_at": stamp, "results": list(results)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# Shrike-7 TTS Bakeoff",
        "",
        "| Model | Role | Status | Load ms | Lat p50 | Lat p95 | RTF p50 | RTF p95 | Non-empty | Err | Peak MB |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for result in results:
        if result["status"] == "skipped":
            lines.append(
                f"| {result['model']} | {result['role']} | skipped | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |"
            )
            continue
        latency = result.get("latency_ms", {})
        rtf = result.get("rtf", {})
        peak_memory = result.get("peak_memory_mb")
        lines.append(
            f"| {result['model']} | {result['role']} | {result['status']} | "
            f"{result.get('load_ms', 0):.0f} | "
            f"{latency.get('median', 0):.0f} | {latency.get('p95', 0):.0f} | "
            f"{rtf.get('median', 0):.2f} | {rtf.get('p95', 0):.2f} | "
            f"{result.get('non_empty_rate', 0):.1%} | {result.get('error_rate', 0):.1%} | "
            f"{'n/a' if peak_memory is None else f'{peak_memory:.0f}'} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Shrike-7 TTS bakeoff.")
    parser.add_argument("--model", action="append", default=[], help="TTS model key. Can be comma-separated.")
    parser.add_argument("--tier-a", action="store_true", help="Run all Tier A registry candidates.")
    parser.add_argument("--tier-b", action="store_true", help="Run all Tier B quality baseline candidates.")
    parser.add_argument("--voice", default=None, help="Voice/speaker id where supported.")
    parser.add_argument("--prompts", type=Path, default=DEFAULT_PROMPT_PATH)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--no-skip-unimplemented",
        action="store_true",
        help="Raise instead of skipping registry entries whose runner is not implemented.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    prompts = load_prompts(args.prompts, limit=args.limit)
    model_keys = select_model_keys(parse_model_list(args.model), tier_a=args.tier_a, tier_b=args.tier_b)

    results: list[dict[str, Any]] = []
    for model_key in model_keys:
        result = run_model_eval(
            model_key,
            prompts,
            voice=args.voice,
            skip_unimplemented=not args.no_skip_unimplemented,
        )
        if result is not None:
            results.append(result)

    render_summary(results)
    json_path, md_path = write_outputs(results, args.output_dir)
    console.print(f"\n[green]Saved[/green] {json_path}")
    console.print(f"[green]Saved[/green] {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
