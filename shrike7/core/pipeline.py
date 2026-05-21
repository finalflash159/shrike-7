from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import numpy as np

from shrike7.core.metrics import MetricsLogger
from shrike7.tts import TTSResult


@dataclass(frozen=True)
class PipelineResult:
    transcript: str
    response_text: str
    rejected: bool
    rejection_reason: str
    tts: TTSResult | None
    stage_latencies_ms: dict[str, float]
    total_latency_ms: float
    asr_result: Any | None = None
    llm_result: Any | None = None


class VoicePipeline:
    def __init__(
        self,
        asr: Any,
        llm: Any,
        tts: Any,
        metrics: MetricsLogger | None = None,
        reject_response: str = "Mình chưa nghe rõ, bạn nói lại nhé.",
    ) -> None:
        self.asr = asr
        self.llm = llm
        self.tts = tts
        self.metrics = metrics or MetricsLogger()
        self.reject_response = reject_response

    def turn(self, audio: np.ndarray) -> PipelineResult:
        self.metrics.reset()
        t0 = time.perf_counter()

        with self.metrics.stage("asr"):
            asr_result = self.asr.transcribe(audio)

        transcript = getattr(asr_result, "text", "").strip()
        rejection_reason = getattr(asr_result, "rejection_reason", "")

        if not transcript:
            return PipelineResult(
                transcript="",
                response_text=self.reject_response,
                rejected=True,
                rejection_reason=rejection_reason or "empty_transcript",
                tts=None,
                stage_latencies_ms=self.metrics.snapshot(),
                total_latency_ms=(time.perf_counter() - t0) * 1000,
                asr_result=asr_result,
            )

        with self.metrics.stage("llm"):
            llm_result = self.llm.generate(transcript)

        response_text = getattr(llm_result, "text", "").strip()

        with self.metrics.stage("tts"):
            tts_result = self.tts.synthesize(response_text)

        return PipelineResult(
            transcript=transcript,
            response_text=response_text,
            rejected=False,
            rejection_reason="",
            tts=tts_result,
            stage_latencies_ms=self.metrics.snapshot(),
            total_latency_ms=(time.perf_counter() - t0) * 1000,
            asr_result=asr_result,
            llm_result=llm_result,
        )
