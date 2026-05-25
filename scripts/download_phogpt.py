import subprocess
from pathlib import Path

from huggingface_hub import hf_hub_download

MODEL_REPO = "vinai/PhoGPT-4B-Chat-gguf"
LOCAL_DIR = Path(__file__).parent.parent / "models" / "phogpt-4b-chat-gguf"
LOCAL_DIR.mkdir(parents=True, exist_ok=True)

# Primary: Q4_K_M
print(f"Downloading {MODEL_REPO} (Q4_K_M) -> {LOCAL_DIR}")
hf_hub_download(
    repo_id=MODEL_REPO,
    filename="PhoGPT-4B-Chat-Q4_K_M.gguf",
    local_dir=str(LOCAL_DIR),
)

print("Done. ")
subprocess.run(["du", "-h", str(LOCAL_DIR)])
