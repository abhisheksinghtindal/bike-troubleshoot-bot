"""Wrapper around the Anthropic Claude API."""
from __future__ import annotations

import base64
import re
from typing import Optional

import anthropic

from ..config import settings
from ..prompts import SYSTEM_PROMPT
from ..store import Manual


_client: Optional[anthropic.Anthropic] = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        if not settings.anthropic_api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Create a .env file from .env.example "
                "and set your key from https://console.anthropic.com/."
            )
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


def _trim_history(history: list[dict]) -> list[dict]:
    """Keep only the last N user+assistant pairs to avoid context overflow."""
    max_messages = settings.max_history_turns * 2
    if len(history) > max_messages:
        history = history[-max_messages:]
    # Always start with a user turn (Anthropic requires alternating roles)
    while history and history[0]["role"] != "user":
        history = history[1:]
    return history


def _build_user_content(
    question: str,
    image_bytes: Optional[bytes],
    image_media_type: Optional[str],
) -> list[dict]:
    content: list[dict] = []
    if image_bytes:
        b64 = base64.standard_b64encode(image_bytes).decode("ascii")
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": image_media_type or "image/jpeg",
                    "data": b64,
                },
            }
        )
    content.append({"type": "text", "text": question})
    return content


def _invalid_citations(answer: str, page_count: int) -> list[int]:
    """Return page numbers cited in the answer that don't exist in the manual."""
    cited = re.findall(r"\(p+\.\s*(\d+)", answer)
    return sorted({int(p) for p in cited if int(p) < 1 or int(p) > page_count})


def ask(
    manual: Manual,
    question: str,
    image_bytes: Optional[bytes] = None,
    image_media_type: Optional[str] = None,
    history: Optional[list[dict]] = None,
) -> dict:
    """Ask a grounded question against a manual. Returns answer + token usage."""
    client = _get_client()

    system_blocks = [
        {"type": "text", "text": SYSTEM_PROMPT},
        {
            "type": "text",
            "text": (
                f"<manual filename=\"{manual.filename}\">\n"
                f"{manual.full_text}\n"
                f"</manual>"
            ),
            "cache_control": {"type": "ephemeral"},
        },
    ]

    trimmed = _trim_history(list(history or []))
    messages = [{"role": t["role"], "content": t["text"]} for t in trimmed]
    messages.append({"role": "user", "content": _build_user_content(question, image_bytes, image_media_type)})

    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=1024,
        temperature=0,
        system=system_blocks,
        messages=messages,
        timeout=60.0,
    )

    text_parts = [block.text for block in response.content if block.type == "text"]
    answer = "\n".join(text_parts).strip()
    usage = response.usage

    return {
        "answer": answer,
        "invalid_citations": _invalid_citations(answer, manual.page_count),
        "usage": {
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "cache_creation_input_tokens": getattr(usage, "cache_creation_input_tokens", 0),
            "cache_read_input_tokens": getattr(usage, "cache_read_input_tokens", 0),
        },
        "model": response.model,
        "stop_reason": response.stop_reason,
    }
