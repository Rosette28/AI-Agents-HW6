"""Thin Anthropic wrapper — the only module in this codebase allowed to
import an LLM SDK (per docs/PROMPTS.md separation-of-concerns: engine, MCP
servers, and strategy modules never call an LLM directly).

Two call shapes only: free-text generation (NL messages) and JSON-structured
generation (belief parsing). No game logic lives here — callers in
`src/agents/dialogue.py` and `src/agents/belief.py` build the prompts and
interpret the results.
"""

import json
import os

from anthropic import Anthropic, APIError


class LLMClient:
    """Wraps one Anthropic client bound to one model.

    `api_key`/`model` are passed in explicitly (read from `.env`/config by
    the caller) rather than read from the environment here, so this class
    stays trivially mockable in tests.
    """

    def __init__(self, api_key: str, model: str):
        # Explicit timeout — the SDK's own default (10 minutes) is far too
        # long for a per-turn call in a real-time game loop; a stuck/slow
        # request should fail fast and let the turn loop fall back to the
        # fixed-template message, not hang the whole series.
        self._client = Anthropic(api_key=api_key, timeout=30.0)
        self._model = model

    def generate_text(self, system_prompt: str, user_prompt: str, max_tokens: int = 100) -> str | None:
        """One free-text completion. Returns None on a hard API failure
        (one retry already attempted) so callers can degrade gracefully
        instead of crashing the turn loop. `max_tokens` is kept small —
        messages are meant to be one short sentence.
        """
        for attempt in range(2):
            try:
                response = self._client.messages.create(
                    model=self._model,
                    max_tokens=max_tokens,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                text = response.content[0].text.strip()
                if text:
                    return text
                return None
            except APIError:
                if attempt == 1:
                    return None
        return None

    def generate_json(self, system_prompt: str, user_prompt: str, max_tokens: int = 150) -> dict | None:
        """One completion, parsed as JSON. Returns None if the API call
        fails outright or the model's output isn't valid JSON — both are
        "no reliable information" cases for the caller, not crashes.
        """
        text = self.generate_text(system_prompt, user_prompt, max_tokens)
        if text is None:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None


def build_llm_client(config: dict) -> LLMClient:
    """Construct an `LLMClient` from the loaded config dict + `ANTHROPIC_API_KEY`
    in the environment (populate via `dotenv.load_dotenv()` before calling).
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    model = config["llm"]["model"]
    return LLMClient(api_key=api_key, model=model)
