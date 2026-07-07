"""Thin LLM client for the VidMak pipeline.

Every agent layer talks to the model through this module, never through the
openai SDK directly -- so the endpoint/model/key live in exactly one place and
can be swapped without touching agent code. Per DECISIONS.md D009 the pipeline
is plain Python (no LangGraph/CrewAI/Agent SDK) pointed at a local
OpenAI-compatible proxy.

Config is read from the environment, with defaults that target the user's
local proxy (see STATE.md env table) so it runs out of the box:

    VIDMAK_LLM_BASE_URL   default http://localhost:20128/v1
    VIDMAK_LLM_MODEL      default cx/gpt-5.5
    VIDMAK_LLM_API_KEY    default sk-local  (the proxy ignores the value)
"""

from __future__ import annotations

import os

from openai import OpenAI

DEFAULT_BASE_URL = "http://localhost:20128/v1"
DEFAULT_MODEL = "cx/gpt-5.5"
DEFAULT_API_KEY = "sk-local"  # proxy does not check it; kept non-empty for the SDK


def model_name() -> str:
    return os.getenv("VIDMAK_LLM_MODEL", DEFAULT_MODEL)


def _client() -> OpenAI:
    return OpenAI(
        base_url=os.getenv("VIDMAK_LLM_BASE_URL", DEFAULT_BASE_URL),
        api_key=os.getenv("VIDMAK_LLM_API_KEY", DEFAULT_API_KEY),
    )


def complete(system: str, user: str, *, max_tokens: int = 8000) -> str:
    """Single-turn completion; returns the assistant text.

    `system` carries the layer's role/instructions -- it overrides the codex
    persona the proxy injects ahead of our messages. `user` carries the
    concrete task input. Temperature is left at the server default because the
    gpt-5.x backend rejects non-default values.
    """
    resp = _client().chat.completions.create(
        model=model_name(),
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content or ""
