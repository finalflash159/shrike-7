"""Integration-style tests for RobustASR using dependency injection.

These tests intentionally avoid loading PhoWhisper or Silero. They verify
pipeline behavior and rejection ordering with small mocks.
"""

from __future__ import annotations

import numpy as np

from shrike7.asr.boh import BoHMatch
from shrike7.asr.robust_asr import RobustASR
from shrike7.asr.vad import VADResult
from shrike7.asr.whisper_onnx import ASRResult


DUMMY_AUDIO = np.zeros(16000, dtype=np.float32)


class MockASR:
    def __init__(self, text: str, avg_logprob: float = 0.0):
        self.text = text
        self.avg_logprob = avg_logprob
        self.calls = 0

    def transcribe(self, audio: np.ndarray) -> ASRResult:
        self.calls += 1
        return ASRResult(
            text=self.text,
            latency_ms=0.0,
            audio_duration_ms=len(audio) / 16_000 * 1000,
            rtf=0.0,
            avg_logprob=self.avg_logprob,
        )


class MockVAD:
    def __init__(self, has_speech: bool = True):
        self.has_speech = has_speech

    def detect(self, audio: np.ndarray) -> VADResult:
        speech_audio = audio if self.has_speech else np.array([], dtype=np.float32)
        duration_ms = len(audio) / 16_000 * 1000
        speech_duration_ms = len(speech_audio) / 16_000 * 1000
        return VADResult(
            has_speech=self.has_speech,
            speech_audio=speech_audio,
            speech_duration_ms=speech_duration_ms,
            original_duration_ms=duration_ms,
            speech_ratio=1.0 if self.has_speech else 0.0,
            vad_latency_ms=0.0,
            n_speech_segments=1 if self.has_speech else 0,
        )


class MockBoH:
    def __init__(self, phrase: str):
        self.phrase = phrase

    def match_and_clean(self, text: str) -> BoHMatch:
        if self.phrase not in text:
            return BoHMatch(matched_phrases=(), cleaned_text=text, n_chars_removed=0)
        cleaned = " ".join(text.replace(self.phrase, "").split())
        return BoHMatch(
            matched_phrases=(self.phrase,),
            cleaned_text=cleaned,
            n_chars_removed=len(text) - len(cleaned),
        )


def test_no_speech_skips_asr():
    asr = MockASR("xin chào", avg_logprob=0.0)
    pipeline = RobustASR(asr=asr, vad=MockVAD(has_speech=False), boh=None)

    result = pipeline.transcribe(DUMMY_AUDIO)

    assert result.text == ""
    assert result.rejection_reason == "no_speech"
    assert result.has_speech is False
    assert result.asr is None
    assert asr.calls == 0


def test_low_confidence_rejected_before_text_filters():
    pipeline = RobustASR(
        asr=MockASR("thôi.", avg_logprob=-0.90),
        vad=MockVAD(),
        boh=MockBoH("thôi."),
        min_avg_logprob=-0.25,
    )

    result = pipeline.transcribe(DUMMY_AUDIO)

    assert result.text == ""
    assert result.rejection_reason == "low_confidence:-0.90"
    assert result.text_after_deloop == "thôi."
    assert result.text_after_boh == "thôi."
    assert result.boh_matches == ()


def test_high_compression_rejected():
    repeated = "xin chào " * 80
    pipeline = RobustASR(
        asr=MockASR(repeated, avg_logprob=0.0),
        vad=MockVAD(),
        boh=None,
        max_compression_ratio=0.5,
    )

    result = pipeline.transcribe(DUMMY_AUDIO)

    assert result.text == ""
    assert result.rejection_reason.startswith("high_compression:")
    assert result.compression_ratio > 0.5


def test_deloop_then_clean_passes():
    pipeline = RobustASR(
        asr=MockASR("xin chào xin chào", avg_logprob=0.0),
        vad=MockVAD(),
        boh=None,
    )

    result = pipeline.transcribe(DUMMY_AUDIO)

    assert result.text == "xin chào"
    assert result.text_after_deloop == "xin chào"
    assert result.was_looping is True
    assert result.rejection_reason == ""


def test_boh_phrase_removed_to_empty():
    pipeline = RobustASR(
        asr=MockASR("cảm ơn các bạn đã xem video", avg_logprob=0.0),
        vad=MockVAD(),
        boh=MockBoH("cảm ơn các bạn đã xem video"),
    )

    result = pipeline.transcribe(DUMMY_AUDIO)

    assert result.text == ""
    assert result.text_after_boh == ""
    assert result.boh_matches == ("cảm ơn các bạn đã xem video",)
    assert result.rejection_reason == "empty_after_boh"


def test_filler_only_rejected_by_heuristic():
    pipeline = RobustASR(
        asr=MockASR("ờ ừm", avg_logprob=0.0),
        vad=MockVAD(),
        boh=None,
    )

    result = pipeline.transcribe(DUMMY_AUDIO)

    assert result.text == ""
    assert result.rejection_reason == "heuristic:filler_only"

