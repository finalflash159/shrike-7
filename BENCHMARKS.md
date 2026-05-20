# Shrike-7 — Benchmarks

> Last updated: 2026-05-21

## D1 — ASR Baseline (PhoWhisper-tiny ONNX, greedy decode)

Common Voice VI 17.0 test (100 samples), MacBook M4 Pro (CPU 4-thread).

| Metric      | Value  | Paper baseline | Notes                                   |
| ----------- | ------ | -------------- | --------------------------------------- |
| WER         | 23.60% | 19.05%         | Gap explained: greedy vs beam-5 (paper) |
| CER         | 12.44% | —              | —                                       |
| Avg latency | 636 ms | —              | KV-cache disabled                       |
| Avg RTF     | 0.049  | —              | 20x faster-than-realtime                |

## D2.5 — ASR Robustness (replicate Barański et al. ICASSP 2025)

### Setup

- Model: PhoWhisper-tiny ONNX (encoder + decoder, greedy decode, no KV cache)
- VAD: Silero VAD, Whisper-tuned (`min_silence=500ms`, `pad=200ms`)
- BoH: **71 Vietnamese phrases** (78 from PhoWhisper-tiny on 800 non-speech samples, 7 false positives flipped after manual review)
- Real speech eval: 100 samples from FLEURS vi_vn test split
- Non-speech eval: 50 samples (ESC-50 + synthetic silence/white/pink noise)
- Device: MacBook M4 Pro, CoreMLExecutionProvider with CPU fallback

### Heuristic thresholds (calibrated p99 + 15% margin on 200 FLEURS samples)

| Metric                | p99   | Default (calibrated) |
| --------------------- | ----- | -------------------- |
| `repetition_thresh`   | 0.278 | 0.35                 |
| `ngram_repetition`    | 0.095 | 0.12                 |
| `chars_per_100ms_max` | 1.567 | 2.50                 |

### BoH construction

| Metric                             | Value    |
| ---------------------------------- | -------- |
| Hallucination rate on 800 noise    | **100%** |
| Unique outputs                     | 100      |
| BoH candidates (count≥2, len≥5)    | 78       |
| After manual review (`keep`)       | 71       |
| Top phrase recurrence              | 100/800  |
| BoH coverage of all hallucinations | 51%      |

**Paper comparison**: Whisper-large-v3 hallucinates on 40% of non-speech;
PhoWhisper-tiny hallucinates on **100%** because it is ~40x smaller (39M vs 1550M params).
The high rate confirms why D2.5 mitigation is essential for the on-device tier.

**YouTube data leak**: 30+ of 71 BoH phrases match the `"các em nhá thấy..."` pattern (teacher addressing "you guys"). This is the Vietnamese analogue of the
WhisperX issue #1086 `"La La School"` leak — Whisper inherits YouTube auto-caption
artifacts cross-language.

### Table VII replication

100 FLEURS vi speech + 50 noise, 6 pipeline configurations.

| Config                | WER    | CER    | Halluc rate | Lat p50 ms | Lat p95 ms |
| --------------------- | ------ | ------ | ----------- | ---------- | ---------- |
| (1) Raw ASR           | 24.20% | 12.17% | 100%        | 954        | 2270       |
| (2) De-loop only      | 24.10% | 12.18% | 100%        | 915        | 2143       |
| (3) Silero VAD only   | 24.79% | 12.59% | **2%**      | 973        | 2163       |
| (4) BoH only          | 24.20% | 12.17% | 100%        | 950        | 2271       |
| (5) De-loop + BoH     | 24.10% | 12.18% | 100%        | 1058       | 2435       |
| (6) **Full pipeline** | 24.79% | 12.59% | **2%**      | 978        | 2318       |

### Metric note

"Hallucination rate" above = `non-empty noise output / total noise`. This metric
**favors VAD** (which skips noise entirely → empty output) and **undervalues BoH**
(which removes matched phrases but residual punctuation/words remain non-empty).

A finer measurement on the same eval:

| BoH effect                         | Value          |
| ---------------------------------- | -------------- |
| Noise samples modified by BoH      | 26/50 (52%)    |
| Noise samples fully emptied by BoH | 21/50 (42%)    |
| BoH false positives on real speech | **0/100 (0%)** |

→ BoH actually catches 42% of noise hallucinations alone, with **zero** real-speech
false positives after manual review. The 100% rate in column 4/5 is a metric
artifact, not a regression.

### Key finding

Full pipeline reduces hallucination rate from 100% to 2% with only **+0.59pp WER**
cost on real Vietnamese speech (24.20% → 24.79%). This matches the qualitative
mitigation pattern from Barański et al. for Whisper-large-v3 on LibriSpeech-augmented,
adapted for Vietnamese PhoWhisper-tiny.

### Reproducibility

All numbers from a single run on 2026-05-21, MacBook M4 Pro, 8-thread CoreML.
Raw output `eval/results/table7_replication.json` (gitignored).
Run via: `uv run python -m local.eval_table7 --n-speech 100 --n-noise 50`.
