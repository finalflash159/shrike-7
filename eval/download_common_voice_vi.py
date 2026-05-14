"""Download a small Vietnamese ASR eval slice.

Common Voice 17 on Hugging Face no longer exposes loadable data files for the
current `datasets` loader, so D1 uses the public Vietnamese split of FLEURS.
"""

from __future__ import annotations

import csv
import json
import shutil
import tarfile
from pathlib import Path

from huggingface_hub import hf_hub_download

DATASET_REPO = "google/fleurs"
LANGUAGE = "vi_vn"
SPLIT = "test"
NUM_SAMPLES = 100
OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "fleurs_vi"


def read_manifest_rows(tsv_path: str, limit: int) -> list[dict[str, str]]:
    """Read FLEURS TSV rows and keep the normalized transcript for WER."""
    manifest = []

    with Path(tsv_path).open(encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if len(row) < 4:
                continue

            filename = Path(row[1]).name
            manifest.append(
                {
                    "filename": filename,
                    "ground_truth": row[3],
                    "raw_transcription": row[2],
                    "source_dataset": DATASET_REPO,
                    "source_split": SPLIT,
                    "source_language": LANGUAGE,
                }
            )

            if len(manifest) >= limit:
                break

    return manifest


def extract_audio_files(tar_path: str, manifest: list[dict[str, str]], out_dir: Path) -> None:
    wanted = {f"{SPLIT}/{entry['filename']}" for entry in manifest}

    with tarfile.open(tar_path, "r:gz") as tar:
        members = {member.name: member for member in tar.getmembers() if member.name in wanted}

        missing = wanted - set(members)
        if missing:
            missing_preview = "\n".join(sorted(missing)[:10])
            raise FileNotFoundError(f"Missing audio files in FLEURS archive:\n{missing_preview}")

        for entry in manifest:
            source_name = f"{SPLIT}/{entry['filename']}"
            source = tar.extractfile(members[source_name])
            if source is None:
                raise FileNotFoundError(f"Could not read archive member: {source_name}")

            with source, (out_dir / entry["filename"]).open("wb") as dest:
                shutil.copyfileobj(source, dest)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    tsv_path = hf_hub_download(
        repo_id=DATASET_REPO,
        repo_type="dataset",
        filename=f"data/{LANGUAGE}/{SPLIT}.tsv",
    )
    tar_path = hf_hub_download(
        repo_id=DATASET_REPO,
        repo_type="dataset",
        filename=f"data/{LANGUAGE}/audio/{SPLIT}.tar.gz",
    )

    manifest = read_manifest_rows(tsv_path, NUM_SAMPLES)
    extract_audio_files(tar_path, manifest, OUT_DIR)

    (OUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Downloaded {len(manifest)} samples from {DATASET_REPO}/{LANGUAGE} to {OUT_DIR}")


if __name__ == "__main__":
    main()
