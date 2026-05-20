# Shrike-7

Trợ lý giọng nói tiếng Việt theo hướng offline-first, tối ưu cho inference cục bộ trên thiết bị edge.

Hướng pipeline hiện tại:

```text
Mic/audio -> VAD -> PhoWhisper ASR -> intent/LLM -> response
```

## Trọng Tâm Hiện Tại

- D1: PhoWhisper-tiny ONNX ASR baseline.
- D2: PhoGPT GGUF local LLM baseline.
- D2.5: tăng độ robust cho ASR, giảm hallucination khi gặp silence/noise.

## Workflow Research Trên Colab

Shrike-7 tách rõ research và runtime:

- **Colab**: thu thập data, xử lý audio, xây dựng Vietnamese Bag of Hallucinations, calibrate threshold, và tùy chọn fine-tune/export model.
- **Local repo**: chạy offline inference, demo, benchmark, và production pipeline code.
- **Google Drive/Hugging Face**: lưu artifact nặng như dataset, checkpoint, file ONNX/GGUF, và benchmark output.

Xem thêm:

- [Plan D2.5 ASR robustness theo hướng Colab](zplan/asr_robustness_colab_plan.md)
- [Workflow notebook](notebooks/README.md)

## Chính Sách Artifact

Repo chỉ commit code, config, docs, script, và notebook. Không commit generated data, model weights, hoặc benchmark output.

Các folder artifact local đang được ignore:

```text
data/
models/
eval/results/
notebooks/outputs/
notebooks/runs/
notebooks/artifacts/
```
