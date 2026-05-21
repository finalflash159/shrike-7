from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from shrike7.core.pipeline import VoicePipeline
from shrike7.tts import TTSResult


@dataclass(frozen=True)
class FakeASRResult:
    text: str
    rejection_reason: str = ""


@dataclass(frozen=True)
class FakeLLMResult:
    text: str


class FakeASR:
    def __init__(self, text: str, rejection_reason: str = "") -> None:
        self.text = text
        self.rejection_reason = rejection_reason
        self.calls = 0

    def transcribe(self, audio: np.ndarray) -> FakeASRResult:
        self.calls += 1
        return FakeASRResult(text=self.text, rejection_reason=self.rejection_reason)


class SpyLLM:
    def __init__(self, response: str = "Xin chao tu LLM") -> None:
        self.response = response
        self.calls: list[str] = []

    def generate(self, text: str) -> FakeLLMResult:
        self.calls.append(text)
        return FakeLLMResult(text=self.response)


class SpyTTS:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def synthesize(self, text: str, voice: str | None = None) -> TTSResult:
        self.calls.append(text)
        return TTSResult(
            text=text,
            audio=np.zeros(2400, dtype=np.float32),
            sample_rate=24000,
            latency_ms=10.0,
            audio_duration_ms=100.0,
            rtf=0.1,
            voice=voice or "NF",
            engine="fake",
        )


def test_voice_pipeline_happy_path_calls_llm_and_tts() -> None:
    asr = FakeASR("xin chao")
    llm = SpyLLM(response="chao ban")
    tts = SpyTTS()
    pipeline = VoicePipeline(asr=asr, llm=llm, tts=tts)

    result = pipeline.turn(np.zeros(16000, dtype=np.float32))

    assert result.rejected is False
    assert result.transcript == "xin chao"
    assert result.response_text == "chao ban"
    assert result.rejection_reason == ""
    assert result.tts is not None
    assert result.tts.text == "chao ban"
    assert asr.calls == 1
    assert llm.calls == ["xin chao"]
    assert tts.calls == ["chao ban"]
    assert set(result.stage_latencies_ms) == {"asr", "llm", "tts"}
    assert result.total_latency_ms >= sum(result.stage_latencies_ms.values())


def test_voice_pipeline_reject_path_skips_llm_and_tts() -> None:
    asr = FakeASR("", rejection_reason="no_speech")
    llm = SpyLLM()
    tts = SpyTTS()
    pipeline = VoicePipeline(asr=asr, llm=llm, tts=tts)

    result = pipeline.turn(np.zeros(16000, dtype=np.float32))

    assert result.rejected is True
    assert result.transcript == ""
    assert result.response_text == "Mình chưa nghe rõ, bạn nói lại nhé."
    assert result.rejection_reason == "no_speech"
    assert result.tts is None
    assert asr.calls == 1
    assert llm.calls == []
    assert tts.calls == []
    assert set(result.stage_latencies_ms) == {"asr"}


def test_voice_pipeline_empty_transcript_uses_default_rejection_reason() -> None:
    pipeline = VoicePipeline(asr=FakeASR("   "), llm=SpyLLM(), tts=SpyTTS())

    result = pipeline.turn(np.zeros(16000, dtype=np.float32))

    assert result.rejected is True
    assert result.rejection_reason == "empty_transcript"


def test_voice_pipeline_resets_metrics_between_turns() -> None:
    pipeline = VoicePipeline(asr=FakeASR("xin chao"), llm=SpyLLM(), tts=SpyTTS())

    first = pipeline.turn(np.zeros(16000, dtype=np.float32))
    second = pipeline.turn(np.zeros(16000, dtype=np.float32))

    assert set(first.stage_latencies_ms) == {"asr", "llm", "tts"}
    assert set(second.stage_latencies_ms) == {"asr", "llm", "tts"}
