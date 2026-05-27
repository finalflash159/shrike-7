from __future__ import annotations

import pytest

from eval.eval_asr import parse_model_list, select_model_keys


def test_select_model_keys_defaults_to_tiny() -> None:
    assert select_model_keys([], None) == ["phowhisper_tiny"]


def test_select_model_keys_combines_profile_and_explicit_without_duplicates() -> None:
    assert select_model_keys(["phowhisper_tiny", "phowhisper_medium"], "bakeoff") == [
        "phowhisper_tiny",
        "phowhisper_base",
        "phowhisper_small",
        "phowhisper_medium",
    ]


def test_parse_model_list_accepts_commas_and_rejects_unknown() -> None:
    assert parse_model_list(["phowhisper_base,phowhisper_small"]) == [
        "phowhisper_base",
        "phowhisper_small",
    ]

    with pytest.raises(ValueError, match="Unknown ASR model key"):
        parse_model_list(["not_real"])
