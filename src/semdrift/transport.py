"""Transport boundary. SDKs and networking are never loaded by fake runs."""

import copy
import json
import os
import threading
import time
from collections import deque
from collections.abc import Callable
from pathlib import Path
from typing import Any


class FakeTransport:
    def __init__(self, responses: list[dict[str, Any]] | None = None) -> None:
        self.responses = deque(responses or [])
        self.calls = 0

    def send(self, model: dict[str, Any], body: dict[str, Any]) -> dict[str, Any]:
        self.calls += 1
        if self.responses:
            return copy.deepcopy(self.responses.popleft())
        # Scripted abstention, deliberately independent of gold labels.
        if model["provider"] == "anthropic":
            return {
                "model": "FAKE-" + model["api_id"],
                "content": [{"type": "text", "text": "Human input needed."}],
                "stop_reason": "end_turn",
                "usage": {},
            }
        return {
            "model": "FAKE-" + model["api_id"],
            "provider": "FAKE",
            "choices": [{"message": {"content": "Human input needed."}, "finish_reason": "stop"}],
            "usage": {},
        }


ENDPOINTS = {
    "openai": "https://api.openai.com/v1/responses",
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
    "deepseek": "https://api.deepseek.com/chat/completions",
    "anthropic": "https://api.anthropic.com/v1/messages",
}
KEY_NAMES = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}
REQUEST_TIMEOUT_SECONDS = 120
MAX_BACKOFF_SECONDS = 30
ERROR_EXCERPT_CHARS = 400


class TransportError(RuntimeError):
    def __init__(self, message: str, status: int | None) -> None:
        super().__init__(message)
        self.status = status


def _retryable(status: int | None) -> bool:
    """Rate limits, server errors and network failures (status None) are worth retrying."""
    return status is None or status == 429 or 500 <= status < 600


class RealTransport:
    """Plain HTTPS JSON calls (standard library only): the body is sent exactly as logged."""

    def __init__(
        self,
        retries: int = 4,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.retries, self.sleep, self.clock = retries, sleep, clock
        self.states = {}
        self.lock = threading.Lock()

    def send(self, model: dict[str, Any], body: dict[str, Any]) -> dict[str, Any]:
        name = model["api_id"]
        with self.lock:
            if name not in self.states:
                self.states[name] = (
                    threading.Semaphore(model["concurrency"]),
                    threading.Lock(),
                    deque(),
                )
            sem, rate_lock, timestamps = self.states[name]
        with sem:
            for attempt in range(self.retries + 1):
                self._respect_rate_limit(model["rpm"], rate_lock, timestamps)
                try:
                    return self._request(model, body)
                except TransportError as exc:
                    if attempt == self.retries or not _retryable(exc.status):
                        raise RuntimeError(f"Transport failed for {name}: {exc}") from None
                    self.sleep(min(2**attempt, MAX_BACKOFF_SECONDS))
        raise AssertionError("unreachable")

    def _respect_rate_limit(self, rpm: int, rate_lock: threading.Lock, timestamps: deque) -> None:
        with rate_lock:
            now = self.clock()
            while timestamps and now - timestamps[0] >= 60:
                timestamps.popleft()
            if len(timestamps) >= rpm:
                self.sleep(max(0, 60 - (now - timestamps[0])))
                now = self.clock()
                while timestamps and now - timestamps[0] >= 60:
                    timestamps.popleft()
            timestamps.append(now)

    @staticmethod
    def _request(model: dict[str, Any], body: dict[str, Any]) -> dict[str, Any]:
        import urllib.error
        import urllib.request

        provider = model["provider"]
        key = os.environ.get(KEY_NAMES[provider])
        if not key:
            raise ValueError(f"Missing environment variable {KEY_NAMES[provider]}")
        headers = {"Content-Type": "application/json"}
        if provider == "anthropic":
            headers |= {"x-api-key": key, "anthropic-version": "2023-06-01"}
        else:
            headers["Authorization"] = f"Bearer {key}"
        if provider == "openrouter":
            # Opt in to routing metadata so the serving host is recorded with each response.
            headers["X-OpenRouter-Metadata"] = "enabled"
        request = urllib.request.Request(
            ENDPOINTS[provider], data=json.dumps(body).encode(), headers=headers, method="POST"
        )
        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            raise TransportError(
                f"HTTP {exc.code}: {sanitize(detail)[:ERROR_EXCERPT_CHARS]}", exc.code
            ) from None
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            raise TransportError(f"network error: {type(exc).__name__}", None) from None


def load_env_file(path: Path) -> list[str]:
    """Set KEY=VALUE pairs from a .env file without overriding the real environment.

    Returns the names that were set (never the values).
    """
    if not path.is_file():
        return []
    loaded = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name, value = name.strip(), value.strip().strip('"').strip("'")
        if name and value and name not in os.environ:
            os.environ[name] = value
            loaded.append(name)
    return loaded


def sanitize(value: Any) -> Any:
    """Defensive redaction of credentials/headers from persisted provider objects."""
    secrets = [
        os.environ[k]
        for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "DEEPSEEK_API_KEY", "OPENROUTER_API_KEY")
        if os.environ.get(k)
    ]

    def walk(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {
                k: (
                    "[REDACTED]"
                    if k.lower()
                    in {"headers", "request_headers", "authorization", "api_key", "x-api-key"}
                    else walk(v)
                )
                for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [walk(v) for v in obj]
        if isinstance(obj, str):
            for secret in secrets:
                obj = obj.replace(secret, "[REDACTED]")
        return obj

    return walk(value)
