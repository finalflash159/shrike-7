from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from shrike7.tts import TTSResult, VietnameseTTS


def test_tts_result_is_frozen():
    result = TTSResult(
        text="xin chào",
        audio=np.zeros(10, dtype=np.float32),
        sample_rate=24000,
        latency_ms=1.0,
        audio_duration_ms=10.0,
        rtf=0.1,
        voice="NF",
        engine="test",
    )

    with pytest.raises(FrozenInstanceError):
        result.text = "changed"


def test_empty_text_returns_empty_audio_without_loading_model():
    tts = VietnameseTTS(lazy=True)

    result = tts.synthesize("   ")

    assert result.text == ""
    assert result.audio.size == 0
    assert result.sample_rate == 24000
    assert result.rtf == 0.0


def test_vietnamese_tts_wraps_existing_model_without_importing_valtec():
    class FakeModel:
        def list_speakers(self):
            return ["NF", "SM"]

        def synthesize(self, text, speaker):
            assert text == "Xin chào"
            assert speaker == "NF"
            return np.ones(2400, dtype=np.float32) * 0.1, 24000

    tts = VietnameseTTS(lazy=True)
    tts._model = FakeModel()

    result = tts.synthesize("Xin chào", voice="NF")

    assert result.text == "Xin chào"
    assert result.voice == "NF"
    assert result.engine == "valtec-tts"
    assert result.audio.dtype == np.float32
    assert result.audio.shape == (2400,)
    assert result.sample_rate == 24000
    assert result.audio_duration_ms == pytest.approx(100.0)


def test_vietnamese_tts_rejects_invalid_source_dir(tmp_path):
    with pytest.raises(FileNotFoundError, match="infer.py and src"):
        VietnameseTTS(source_dir=tmp_path)


def test_vietnamese_tts_accepts_valid_source_dir_without_loading(tmp_path):
    (tmp_path / "infer.py").write_text("", encoding="utf-8")
    (tmp_path / "src").mkdir()

    tts = VietnameseTTS(source_dir=tmp_path, lazy=True)

    assert tts.source_dir == tmp_path.resolve()
