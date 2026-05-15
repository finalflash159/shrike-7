# Shrike-7 - Benchmarks

> Last updated: 2026-05-15

## D1 Baseline - ASR (PhoWhisper-tiny ONNX, greedy decoding)

### Common Voice VI 17.0 test (100 samples), Macbook M4 Pro (CPU 4-thread)

| Metric | Value | Paper baseline  | Notes |
|--------|-------|-----------------|-------|
| WER    | 23.60% | 19.05% | Gap explained: greedy vs beam-5 (paper) |
| CER   | 12.44% | - | _ |
| Avg latency | 636 ms | - | KV-cache disabled |
| Avg RTF | 0.049 | - | - |
