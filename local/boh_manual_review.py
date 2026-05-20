"""CLI: apply manual-review decisions to BoH artifact.

Plan v3 explicitly requires a manual review step between BoH construction
and runtime use. This CLI codifies the obvious false positives that should
be marked `keep: false` so the Aho-Corasick matcher skips them.

Usage:
    uv run python -m local.boh_manual_review
    uv run python -m local.boh_manual_review --boh-path data/asr/boh/other.json
    uv run python -m local.boh_manual_review --add-skip "phrase to skip"

The default skip list contains phrases that are clearly legitimate
Vietnamese speech that PhoWhisper-tiny happens to emit on noise. These
should NOT block real transcripts.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import click
from rich.console import Console

from local import config as cfg

console = Console()

# Phrases that are clearly legitimate Vietnamese speech and should NOT be
# blocked even if they appear in noise hallucinations. Curated by manual
# review of the 800-sample run on 2026-05-21.
DEFAULT_FALSE_POSITIVES: frozenset[str] = frozenset(
    {
        # Confirmation / response
        "đúng rồi",
        # Common time/topic openers
        "hôm nay",
        # Pronouns / partial pronouns that could be start of valid speech
        "các em",
        "chúng",
        # Common discourse markers
        "để tôi tìm ra",
        "chúng ta sẽ thấy",
        "chúng ta sẽ thấy rằng",
    }
)


@click.command()
@click.option(
    "--boh-path", default=str(cfg.RUNTIME_BOH_PATH), type=click.Path(),
    help="BoH JSON file to update.",
)
@click.option(
    "--add-skip", multiple=True,
    help="Additional phrases to mark keep=false. Repeat flag for multiple.",
)
@click.option(
    "--also-update", default=None,
    help="Also update a second copy of the BoH (e.g. data/asr/boh/*.json).",
)
def main(boh_path: str, add_skip: tuple[str, ...], also_update: str | None) -> None:
    path = Path(boh_path)
    if not path.exists():
        raise click.ClickException(f"BoH file not found: {path}")

    skip_phrases = set(DEFAULT_FALSE_POSITIVES) | set(add_skip)
    console.print(f"Manual-review skip list ({len(skip_phrases)} phrases):")
    for phrase in sorted(skip_phrases):
        console.print(f"  - {phrase!r}")
    console.print()

    paths_to_update = [path]
    if also_update:
        paths_to_update.append(Path(also_update))

    # Default behavior: also update the per-model BoH file in data/asr/boh/
    # so model-specific consumers stay consistent with the runtime alias.
    if also_update is None and path == cfg.RUNTIME_BOH_PATH:
        per_model = cfg.BOH_DIR / "phowhisper_tiny_vi_boh_v1.json"
        if per_model.exists() and per_model != path:
            paths_to_update.append(per_model)

    for target_path in paths_to_update:
        # Backup before overwriting
        backup = target_path.with_suffix(target_path.suffix + ".bak")
        shutil.copy2(target_path, backup)

        data = json.loads(target_path.read_text(encoding="utf-8"))
        n_flipped = 0
        for item in data.get("boh", []):
            if item["phrase"] in skip_phrases and item.get("keep", True):
                item["keep"] = False
                n_flipped += 1

        # Note the review in metadata
        meta = data.setdefault("metadata", {})
        review_log = meta.setdefault("manual_review", [])
        review_log.append(
            {
                "applied_at_utc": datetime.now(timezone.utc).isoformat(),
                "applied_by": "local.boh_manual_review",
                "skip_list_size": len(skip_phrases),
                "n_phrases_flipped": n_flipped,
            }
        )

        target_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        kept = sum(1 for item in data["boh"] if item.get("keep", True))
        console.print(
            f"[green]✓[/green] {target_path.name}: "
            f"flipped {n_flipped}/{len(data['boh'])} phrases → {kept} kept "
            f"(backup: {backup.name})"
        )


if __name__ == "__main__":
    main()
