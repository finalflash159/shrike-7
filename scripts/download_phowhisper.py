from pathlib import Path
from huggingface_hub import snapshot_download

MODEL_REPO = "huuquyet/PhoWhisper-tiny"
LOCAL_DIR = Path(__file__).parent.parent / "models" / "phowhisper-tiny-onnx"

print(f"Downloading {MODEL_REPO} -> {LOCAL_DIR}")
LOCAL_DIR.mkdir(parents=True, exist_ok=True)

snapshot_download(
    repo_id=MODEL_REPO,
    local_dir=str(LOCAL_DIR),
)
print("Done.")
