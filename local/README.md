# Local D2.5 Pipeline — Mac M-series CLI

Phiên bản chạy thẳng trên Mac không cần Colab. Logic giống `notebooks/01` + `notebooks/02` nhưng đóng gói thành CLI để chạy tuần tự, không lệ thuộc Google Drive.

## Khi nào dùng `local/` thay vì `notebooks/`

| Tình huống                                    | Dùng         |
| --------------------------------------------- | ------------ |
| Colab Free hết quota                          | `local/`     |
| Dataset cần lưu local Mac để rerun nhanh      | `local/`     |
| Cần benchmark tốc độ trên M4 Pro vs Colab CPU | `local/`     |
| Cần GPU lớn (Colab T4/A100) cho model >tiny   | `notebooks/` |

## Setup một lần

Đã có repo + `.venv` từ `uv sync`. Nếu chưa:

```bash
uv sync --extra dev --extra eval
```

`silero-vad` và `llama-cpp-python` đã trong base deps.

## Pipeline 2 bước

### Bước 1: Thu thập noise (~3-10 phút)

```bash
uv run python -m local.collect_noise
```

Mặc định:

- 500 sample từ ESC-50 (stream, loại các category có voice).
- 300 synthetic (100 silence + 100 white + 100 pink).
- Tổng target 800.

Output:

```
data/noise_for_boh/wav/*.wav
data/noise_for_boh/manifest.jsonl
data/noise_for_boh/noise_collection_config.json
```

Options:

```bash
uv run python -m local.collect_noise --target 200      # smoke
uv run python -m local.collect_noise --force            # rebuild even if manifest exists
uv run python -m local.collect_noise --seed 7           # different RNG
```

### Bước 2: Build BoH (~15-40 phút trên M4 Pro)

```bash
uv run python -m local.build_boh
```

Mặc định:

- Model: `phowhisper_tiny` (cache vào `models/phowhisper-tiny-onnx/` nếu chưa có).
- Providers: CoreML + CPU fallback.
- Max files: all (tất cả file trong manifest).

Output:

```
data/asr/boh/phowhisper_tiny_vi_boh_v1.json     # BoH model-specific
data/asr/vi_boh_v1.json                          # alias cho runtime model
notebooks/outputs/{RUN_ID}/logs/boh_runs/phowhisper_tiny/phowhisper_noise_outputs.jsonl
notebooks/outputs/{RUN_ID}/config_snapshot.json
```

Options thường dùng:

```bash
# Smoke run 20 file để verify pipeline trước khi đốt 40 phút
uv run python -m local.build_boh --max-files 20

# Force CPU only (debug khi nghi ngờ CoreML provider lỗi)
uv run python -m local.build_boh --providers cpu

# Multi-model run để dựng cross_model_consensus
uv run python -m local.build_boh --model phowhisper_tiny --model phowhisper_base \
    --runtime-model phowhisper_tiny
```

## GPU trên Mac M4 Pro

ONNX Runtime trên macOS arm64 có 3 provider khả dụng:

```
['CoreMLExecutionProvider', 'AzureExecutionProvider', 'CPUExecutionProvider']
```

`local/build_boh.py` ưu tiên `CoreMLExecutionProvider` (dùng Apple Neural Engine + GPU), fallback `CPUExecutionProvider`. Nếu một node ONNX không support CoreML, runtime tự fallback node đó về CPU — không crash.

So sánh ước lượng trên 800 sample noise (~3-5s mỗi file):

| Provider              | Latency/sample | Tổng        |
| --------------------- | -------------- | ----------- |
| CPU 4-thread          | ~150-200 ms    | ~30-40 phút |
| CoreML + CPU fallback | ~60-100 ms     | ~15-25 phút |

Silero VAD trong `shrike7/asr/vad.py` dùng PyTorch, sẽ tự pick MPS trên M-series nếu code dùng `torch.from_numpy(...).to("mps")` — hiện tại để CPU cho VAD vì 1.8M params trên 5s audio chỉ ~30ms CPU, không cần GPU.

## Sanity checklist sau khi BoH chạy xong

```bash
# Số file output
ls data/asr/boh/

# Inspect top 20
uv run python -c "
import json
data = json.load(open('data/asr/boh/phowhisper_tiny_vi_boh_v1.json'))
print(f\"Hallucination rate: {data['metadata']['hallucination_rate']:.2%}\")
print(f\"BoH size: {len(data['boh'])}\")
print('Top 10:')
for item in data['boh'][:10]:
    print(f\"  count={item['count']:3d}  '{item['phrase'][:80]}'\")
"
```

Kỳ vọng:

- Hallucination rate trên non-speech: **30-50%** (paper BoH báo 40.3% cho Whisper-large-v3 trên 301k file).
- Top 30 cover ~70-77% tổng hallucinations.
- BoH size sau filter count≥2, len≥5: **30-100 phrase** cho 800 sample.

Nếu rate <10% hoặc BoH size <5: pipeline có bug, đừng scale.

## Quan hệ với `notebooks/`

`local/` và `notebooks/02` cùng config (model registry, MIN_COUNT, MIN_CHARS, normalization), output JSON cùng schema. BoH file từ `local/` và `notebooks/02` có thể swap được cho nhau ở runtime — chỉ khác metadata field `execution_mode` (`"local"` vs `"colab"`).

Notebook là canonical workflow theo plan v3 (`zplan/asr_robustness_colab_plan.md`). `local/` là fallback CLI khi Colab không khả dụng.
