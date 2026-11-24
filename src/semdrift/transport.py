"""Transport boundary. SDKs and networking are never loaded by fake runs."""

import copy
import os
import threading
import time
from collections import deque
from collections.abc import Callable
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


class RealTransport:
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
                with rate_lock:
                    now = self.clock()
                    while timestamps and now - timestamps[0] >= 60:
                        timestamps.popleft()
                    if len(timestamps) >= model["rpm"]:
                        self.sleep(max(0, 60 - (now - timestamps[0])))
                        now = self.clock()
                        while timestamps and now - timestamps[0] >= 60:
                            timestamps.popleft()
                    timestamps.append(now)
                try:
                    return self._request(model, body)
                except Exception as exc:
                    status = getattr(exc, "status_code", None)
                    if attempt == self.retries or not (
                        status == 429 or isinstance(status, int) and 500 <= status < 600
                    ):
                        # Do not leak SDK errors (which may contain request headers or credentials).
                        raise RuntimeError(
                            f"Transport failed for {name}; status={status}; response not logged"
                        ) from None
                    self.sleep(min(2**attempt, 30))

    @staticmethod
    def _request(model: dict[str, Any], body: dict[str, Any]) -> dict[str, Any]:
        provider = model["provider"]
        key_name = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
        }[provider]
        key = os.environ.get(key_name)
        if not key:
            raise ValueError(f"Missing environment variable {key_name}")
        if provider == "anthropic":
            import anthropic

            with anthropic.Anthropic(api_key=key, max_retries=0, timeout=120) as client:
                return client.messages.create(**body).model_dump(mode="json")
        import openai

        urls = {
            "deepseek": "https://api.deepseek.com",
            "openrouter": "https://openrouter.ai/api/v1",
        }
        kwargs = {"base_url": urls[provider]} if provider in urls else {}
        payload = dict(body)
        extra = {k: payload.pop(k) for k in ("thinking", "provider") if k in payload}
        with openai.OpenAI(api_key=key, max_retries=0, timeout=120, **kwargs) as client:
            return client.chat.completions.create(**payload, extra_body=extra or None).model_dump(
                mode="json"
            )


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
