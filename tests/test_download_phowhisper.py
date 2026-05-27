from __future__ import annotations

from scripts.download_phowhisper import select_configs


def test_select_configs_defaults_to_tiny() -> None:
    configs = select_configs([], None)

    assert [config.model_key for config in configs] == ["phowhisper_tiny"]


def test_select_configs_combines_profile_and_explicit_models_without_duplicates() -> None:
    configs = select_configs(["phowhisper_tiny", "phowhisper_medium"], "bakeoff")

    assert [config.model_key for config in configs] == [
        "phowhisper_tiny",
        "phowhisper_base",
        "phowhisper_small",
        "phowhisper_medium",
    ]
