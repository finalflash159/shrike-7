from __future__ import annotations

import argparse
from pathlib import Path


MODEL_REGISTRY = {
    "phowhisper_tiny": {
        "repo_id": "huuquyet/PhoWhisper-tiny",
        "local_subdir": "phowhisper-tiny-onnx",
        "params_m": 39,
    },
    "phowhisper_base": {
        "repo_id": "huuquyet/PhoWhisper-base",
        "local_subdir": "phowhisper-base-onnx",
        "params_m": 74,
    },
    "phowhisper_small": {
        "repo_id": "huuquyet/PhoWhisper-small",
        "local_subdir": "phowhisper-small-onnx",
        "params_m": 244,
    },
    "phowhisper_medium": {
        "repo_id": "huuquyet/PhoWhisper-medium",
        "local_subdir": "phowhisper-medium-onnx",
        "params_m": 769,
    },
}

MODEL_ALLOW_PATTERNS = [
    "onnx/encoder_model.onnx",
    "onnx/decoder_model.onnx",
    "config.json",
    "generation_config.json",
    "preprocessor_config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "vocab.json",
    "merges.txt",
    "normalizer.json",
    "added_tokens.json",
    "special_tokens_map.json",
    "quantize_config.json",
]


def download_model(model_key: str, models_dir: Path) -> Path:
    from huggingface_hub import snapshot_download

    config = MODEL_REGISTRY[model_key]
    local_dir = models_dir / config["local_subdir"]
    local_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {model_key}: {config['repo_id']} -> {local_dir}")
    snapshot_download(
        repo_id=config["repo_id"],
        local_dir=str(local_dir),
        allow_patterns=MODEL_ALLOW_PATTERNS,
    )
    return local_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download PhoWhisper ONNX model files.")
    parser.add_argument(
        "--model",
        choices=sorted(MODEL_REGISTRY),
        default="phowhisper_tiny",
        help="Model key to download. Default: phowhisper_tiny.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Download every registered model.",
    )
    parser.add_argument(
        "--models-dir",
        type=Path,
        default=None,
        help="Directory where model folders are stored. Overrides --storage.",
    )
    parser.add_argument(
        "--storage",
        choices=["local", "drive"],
        default="local",
        help="Default storage target when --models-dir is not provided.",
    )
    parser.add_argument(
        "--drive-root",
        type=Path,
        default=Path("/content/drive/MyDrive/shrike-7"),
        help="Google Drive project root used when --storage=drive.",
    )
    return parser.parse_args()


def resolve_models_dir(args: argparse.Namespace) -> Path:
    if args.models_dir is not None:
        return args.models_dir
    if args.storage == "drive":
        return args.drive_root / "models"
    return Path(__file__).resolve().parents[1] / "models"


def main() -> None:
    args = parse_args()
    model_keys = sorted(MODEL_REGISTRY) if args.all else [args.model]
    models_dir = resolve_models_dir(args)

    downloaded = []
    for model_key in model_keys:
        downloaded.append(download_model(model_key, models_dir))

    print("Done.")
    for path in downloaded:
        print(f"- {path}")


if __name__ == "__main__":
    main()
