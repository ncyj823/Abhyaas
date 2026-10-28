"""Groq LLM wrapper with retry and backoff."""

import json
import os
import time
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from groq import Groq, APIError, RateLimitError

load_dotenv()

_client: Optional[Groq] = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not set. Copy .env.example to .env and fill it in.")
        _client = Groq(api_key=api_key)
    return _client


def get_model() -> str:
    return os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")


def chat_json(
    system: str,
    messages: list[Dict[str, str]],
    max_retries: int = 2,
) -> Dict[str, Any]:
    """Send a chat request expecting a JSON response. Retries on rate-limit.

    Returns the parsed JSON dict from the assistant's reply.
    Raises ValueError if the response isn't valid JSON after retries.
    """
    client = _get_client()
    model = get_model()

    all_messages = [{"role": "system", "content": system}] + messages

    last_error: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=all_messages,
                temperature=0.7,
                max_tokens=512,
                response_format={"type": "json_object"},
            )
            text = resp.choices[0].message.content.strip()
            return json.loads(text)
        except RateLimitError as e:
            last_error = e
            wait = 2 ** attempt
            time.sleep(wait)
        except APIError as e:
            raise RuntimeError(f"Groq API error: {e}") from e
        except json.JSONDecodeError as e:
            last_error = e
            # Retry once for bad JSON
            if attempt < max_retries:
                continue
            raise ValueError(f"LLM returned invalid JSON after {max_retries + 1} attempts") from e

    raise RuntimeError(f"Rate limited after {max_retries + 1} attempts: {last_error}")


def chat_text(
    system: str,
    messages: list[Dict[str, str]],
    max_retries: int = 2,
) -> str:
    """Send a chat request expecting a plain text response. Retries on rate-limit."""
    client = _get_client()
    model = get_model()

    all_messages = [{"role": "system", "content": system}] + messages

    last_error: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=all_messages,
                temperature=0.7,
                max_tokens=512,
            )
            return resp.choices[0].message.content.strip()
        except RateLimitError as e:
            last_error = e
            wait = 2 ** attempt
            time.sleep(wait)
        except APIError as e:
            raise RuntimeError(f"Groq API error: {e}") from e

    raise RuntimeError(f"Rate limited after {max_retries + 1} attempts: {last_error}")
