# Shrike-7 Colab Notebooks

This folder contains Colab notebooks for Shrike-7 research, data collection, training, calibration, and export work.

Keep the boundary clear:

- Commit notebooks, small config files, and explanations.
- Do not commit downloaded datasets, generated audio, checkpoints, ONNX/GGUF exports, or benchmark outputs.
- Store heavy artifacts in Google Drive or Hugging Face, then copy them into ignored local folders only when needed.

## Recommended Notebook Order

```text
00_colab_setup.ipynb
01_noise_data_collection.ipynb
02_build_vietnamese_boh.ipynb
03_threshold_calibration.ipynb
04_table7_replication.ipynb
05_asr_finetune_phowhisper_lora.ipynb
06_export_onnx_quantize.ipynb
```

## Standard Colab Header

```python
PROJECT = "shrike-7"
RUN_NAME = "d2_5_asr_robustness"
SEED = 42
```

```python
from pathlib import Path

GITHUB_REPO_URL = "https://github.com/finalflash159/shrike-7.git"
REPO_DIR = Path("/content/shrike-7")
DRIVE_ROOT = Path("/content/drive/MyDrive/shrike-7")
```

```python
from google.colab import drive
drive.mount("/content/drive")
```

Then run `notebooks/00_colab_setup.ipynb` to clone/pull the repo, create the Drive layout, and install D2.5 dependencies.

## Artifact Layout

Use this layout on Google Drive:

```text
/content/drive/MyDrive/shrike-7/
├── datasets/
├── checkpoints/
├── exports/
└── logs/
```

Ignored local destinations:

```text
data/
models/
eval/results/
notebooks/outputs/
notebooks/runs/
notebooks/artifacts/
```

## Notes

Notebook code should gradually move into importable Python modules or scripts once it stabilizes. Notebooks should orchestrate experiments; they should not be the only place where core logic lives.
