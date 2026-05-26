from __future__ import annotations

import re
from typing import TypedDict

from .registry import LLMModelConfig

COMPLETION_PROMPT_TEMPLATES = {
    "phogpt_completion": "### Câu hỏi: {prompt}\n### Trả lời:",
}

SHRIKE7_SYSTEM_PROMPT = (
    "Bạn là Shrike-7, trợ lý ảo tiếng Việt thông minh, thân thiện. "
    "Trả lời súc tích dưới 50 từ. Nếu không biết, hãy nói rằng bạn không biết."
)

QWEN_NO_THINK_MARKER = "/no_think"
THINK_BLOCK_RE = re.compile(r"<think>.*?</think>", flags=re.DOTALL | re.IGNORECASE)


class ChatMessage(TypedDict):
    role: str
    content: str


def build_completion_prompt(
    user_msg: str,
    config: LLMModelConfig,
    inject_persona: bool = True,
) -> str:
    try:
        prompt_template = COMPLETION_PROMPT_TEMPLATES[config.prompt_style]
    except KeyError as exc:
        raise ValueError(f"Model does not use completion prompts: {config.model_key}") from exc

    user_msg = user_msg.strip()
    if inject_persona:
        user_msg = f"{SHRIKE7_SYSTEM_PROMPT}\n\nCâu hỏi của tôi: {user_msg}"

    return prompt_template.format(prompt=user_msg)


def build_chat_messages(
    user_msg: str,
    config: LLMModelConfig,
    inject_persona: bool = True,
) -> list[ChatMessage]:
    if config.prompt_style == "phogpt_completion":
        raise ValueError("Completion-style models use completion prompts, not chat messages.")

    user_msg = user_msg.strip()
    if config.append_no_think and QWEN_NO_THINK_MARKER not in user_msg:
        user_msg = f"{user_msg}\n{QWEN_NO_THINK_MARKER}"

    messages: list[ChatMessage] = []
    if inject_persona:
        messages.append({"role": "system", "content": SHRIKE7_SYSTEM_PROMPT})
    messages.append({"role": "user", "content": user_msg})
    return messages


def clean_model_output(text: str, config: LLMModelConfig) -> str:
    text = text.strip()
    if config.strip_reasoning:
        text = THINK_BLOCK_RE.sub("", text).strip()
    return text


def uses_completion_prompt(config: LLMModelConfig) -> bool:
    return config.prompt_style == "phogpt_completion"
