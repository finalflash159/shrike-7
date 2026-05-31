from __future__ import annotations

from scripts.demo_voice_loop import build_parser, resolve_runtime_args


def parse_args(argv: list[str]):
    return resolve_runtime_args(build_parser().parse_args(argv))


def test_quality_profile_resolves_omnivoice_voice() -> None:
    args = parse_args(["--profile", "quality"])

    assert args.asr_model == "phowhisper_small"
    assert args.llm_model == "arcee_vylinh_3b_q4_k_m"
    assert args.tts_model == "omnivoice"
    assert args.voice == "emgai_dangiu"


def test_tts_model_override_uses_overridden_model_default_voice() -> None:
    args = parse_args(["--profile", "quality", "--tts-model", "valtec_multispeaker"])

    assert args.asr_model == "phowhisper_small"
    assert args.llm_model == "arcee_vylinh_3b_q4_k_m"
    assert args.tts_model == "valtec_multispeaker"
    assert args.voice == "NF"


def test_explicit_voice_override_wins() -> None:
    args = parse_args(["--profile", "baseline", "--voice", "SF"])

    assert args.tts_model == "valtec_multispeaker"
    assert args.voice == "SF"


def test_explicit_model_overrides_win_over_profile() -> None:
    args = parse_args(
        [
            "--profile",
            "quality",
            "--asr-model",
            "phowhisper_base",
            "--llm-model",
            "phogpt_4b_q4_k_m",
            "--tts-model",
            "mms_tts_vie",
        ]
    )

    assert args.asr_model == "phowhisper_base"
    assert args.llm_model == "phogpt_4b_q4_k_m"
    assert args.tts_model == "mms_tts_vie"
    assert args.voice == "default"


def test_profile_runtime_options_resolve() -> None:
    args = parse_args(["--profile", "quality"])

    assert args.endpoint_silence_ms == 700
    assert args.max_record_ms == 10000
    assert args.max_tokens == 160
    assert args.temperature == 0.2
    assert args.top_p == 0.95


def test_runtime_option_overrides_win() -> None:
    args = parse_args(
        [
            "--profile",
            "quality",
            "--endpoint-silence-ms",
            "900",
            "--max-record-ms",
            "12000",
            "--max-tokens",
            "96",
            "--temperature",
            "0.1",
            "--top-p",
            "0.9",
        ]
    )

    assert args.endpoint_silence_ms == 900
    assert args.max_record_ms == 12000
    assert args.max_tokens == 96
    assert args.temperature == 0.1
    assert args.top_p == 0.9
