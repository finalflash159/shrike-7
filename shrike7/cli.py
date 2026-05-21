from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

console = Console()
REPO_ROOT = Path(__file__).resolve().parents[1]


def run_module(module: str, *args: str) -> None:
    """Run a Python module using the current interpreter."""
    cmd = [sys.executable, "-m", module, *args]
    raise SystemExit(subprocess.call(cmd, cwd=REPO_ROOT))


def run_script(script: str, *args: str) -> None:
    """Run a script file using the current interpreter."""
    cmd = [sys.executable, script, *args]
    raise SystemExit(subprocess.call(cmd, cwd=REPO_ROOT))


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(package_name="shrike7")
def main() -> None:
    """Shrike-7 local Vietnamese voice assistant toolkit."""


@main.command()
def status() -> None:
    """Show local artifact status."""
    paths = {
        "PhoWhisper ONNX": REPO_ROOT / "models" / "phowhisper-tiny-onnx",
        "PhoGPT GGUF": REPO_ROOT / "models" / "phogpt-4b-chat-gguf" / "PhoGPT-4B-Chat-Q4_K_M.gguf",
        "Noise manifest": REPO_ROOT / "data" / "noise_for_boh" / "manifest.jsonl",
        "FLEURS manifest": REPO_ROOT / "data" / "fleurs_vi" / "manifest.jsonl",
        "Runtime BoH": REPO_ROOT / "data" / "asr" / "vi_boh_v1.json",
        "Threshold calibration": REPO_ROOT / "data" / "asr" / "threshold_calibration.json",
    }

    table = Table(title="Shrike-7 Local Status")
    table.add_column("Artifact", style="cyan")
    table.add_column("Exists", justify="center")
    table.add_column("Path")

    for name, path in paths.items():
        table.add_row(name, "yes" if path.exists() else "no", str(path))

    console.print(table)


@main.command("asr-smoke")
def asr_smoke() -> None:
    """Run the local ASR smoke test on recorded sample audio."""
    run_script(str(REPO_ROOT / "scripts" / "smoke_test_asr.py"))


@main.command("llm-smoke")
def llm_smoke() -> None:
    """Run the local PhoGPT smoke test."""
    run_script(str(REPO_ROOT / "scripts" / "smoke_test_llm.py"))


@main.command("benchmark-asr")
@click.option("--n-speech", default=50, type=int, show_default=True)
@click.option("--n-noise", default=20, type=int, show_default=True)
@click.option(
    "--providers",
    default="auto",
    type=click.Choice(["auto", "cpu"]),
    show_default=True,
)
def benchmark_asr(n_speech: int, n_noise: int, providers: str) -> None:
    """Run the Table VII-style ASR robustness benchmark."""
    run_module(
        "local.eval_table7",
        "--n-speech",
        str(n_speech),
        "--n-noise",
        str(n_noise),
        "--providers",
        providers,
    )


@main.command("calibrate-asr")
@click.option("--n-speech", default=200, type=int, show_default=True)
@click.option("--n-noise", default=50, type=int, show_default=True)
@click.option(
    "--providers",
    default="auto",
    type=click.Choice(["auto", "cpu"]),
    show_default=True,
)
def calibrate_asr(n_speech: int, n_noise: int, providers: str) -> None:
    """Calibrate ASR confidence thresholds."""
    run_module(
        "local.calibrate_asr_confidence",
        "--n-speech",
        str(n_speech),
        "--n-noise",
        str(n_noise),
        "--providers",
        providers,
    )
