# backend/service/llm_client.py
import json
from dataclasses import dataclass, field
from typing import Callable

import requests


class LlmError(Exception):
    """Base class for LLM client errors."""


class AuthError(LlmError):
    """401/403 from upstream — non-retryable."""


class RetryExhausted(LlmError):
    """Retry budget exhausted after retryable failures."""


_BACKOFF = [1, 2, 4, 8, 16, 30]


def _make_openai(base_url: str, api_key: str):
    from openai import OpenAI
    return OpenAI(api_key=api_key, base_url=base_url, timeout=120)


@dataclass
class LlmClient:
    base_url: str
    api_key: str
    model_name: str
    api_type: str   # "openai" | "raw"
    max_retries: int = 5
    sleep: Callable[[float], None] = field(default=__import__("time").sleep)

    def call(self, prompt: str) -> str:
        if self.api_type == "openai":
            return self._call_openai(prompt)
        return self._call_raw(prompt)

    # ---- openai path ----
    def _call_openai(self, prompt: str) -> str:
        from openai import (
            AuthenticationError, PermissionDeniedError,
            RateLimitError, APIStatusError, APIConnectionError, APITimeoutError,
        )
        client = _make_openai(self.base_url, self.api_key)
        for attempt in range(self.max_retries):
            try:
                rsp = client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                )
                return rsp.choices[0].message.content or ""
            except (AuthenticationError, PermissionDeniedError) as e:
                raise AuthError(str(e)) from e
            except (RateLimitError, APIStatusError,
                    APIConnectionError, APITimeoutError) as e:
                if attempt >= self.max_retries - 1:
                    raise RetryExhausted(str(e)) from e
                self.sleep(_BACKOFF[min(attempt, len(_BACKOFF) - 1)])
        raise RetryExhausted("budget exhausted")

    # ---- raw path ----
    def _call_raw(self, prompt: str) -> str:
        url = f"{self.base_url.rstrip('/')}/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}",
                   "Content-Type": "application/json"}
        payload = {"model": self.model_name, "stream": False,
                   "messages": [{"role": "user", "content": prompt}]}
        for attempt in range(self.max_retries):
            try:
                rsp = requests.post(url, headers=headers,
                                    json=payload, timeout=120)
                if rsp.status_code in (401, 403):
                    raise AuthError(f"HTTP {rsp.status_code}")
                if rsp.status_code == 429 or 500 <= rsp.status_code < 600:
                    if attempt >= self.max_retries - 1:
                        raise RetryExhausted(f"HTTP {rsp.status_code}")
                    self.sleep(_BACKOFF[min(attempt, len(_BACKOFF) - 1)])
                    continue
                rsp.raise_for_status()
                return rsp.json()["choices"][0]["message"]["content"] or ""
            except AuthError:
                raise
            except (requests.ConnectionError, requests.Timeout) as e:
                if attempt >= self.max_retries - 1:
                    raise RetryExhausted(str(e)) from e
                self.sleep(_BACKOFF[min(attempt, len(_BACKOFF) - 1)])
        raise RetryExhausted("budget exhausted")
