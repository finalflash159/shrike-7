"""ASR subpackage: Vietnamese speech-to-text with Whisper hallucination mitigation.

Public pipeline:
    audio → VAD → ASR → de-loop → BoH match → heuristics → clean text

References:
    - Barański et al. (ICASSP 2025) — Bag of Hallucinations approach
    - Le et al. (ICLR 2024 Tiny Papers) — PhoWhisper Vietnamese fine-tune
"""

from .boh import BoHMatch, VietnameseBoH
from .deloop import has_excessive_repetition, remove_consecutive_repeats
from .hallucination_heuristics import (
    HeuristicCheck,
    check_heuristics,
    is_filler_only,
    n_gram_repetition,
    repetition_ratio,
)
from .robust_asr import RobustASR, RobustASRResult
from .vad import SpeechDetector, VADResult
from .whisper_onnx import ASRResult, VietnameseASR

__all__ = [
    "ASRResult",
    "BoHMatch",
    "HeuristicCheck",
    "RobustASR",
    "RobustASRResult",
    "SpeechDetector",
    "VADResult",
    "VietnameseASR",
    "VietnameseBoH",
    "check_heuristics",
    "has_excessive_repetition",
    "is_filler_only",
    "n_gram_repetition",
    "remove_consecutive_repeats",
    "repetition_ratio",
]
