"""Talks to the local Ollama server and turns its reply into a validated AIResult.

Failure handling:
  * Ollama not running / timeout / HTTP error  -> AIUnavailableError (router returns 503)
  * Model replies with junk or invalid values  -> one retry, then AIInvalidResponseError
Nothing here touches the database, so it is easy to unit-test with a mocked httpx.
"""
import json
import logging
import os
import re
from typing import Optional

import httpx
from pydantic import ValidationError

from app.schemas.ai import AIResult
from app.services.ai.prompt import (
    build_messages,
    contains_secret,
    looks_like_injection,
    redact_secrets,
)

logger = logging.getLogger(__name__)

DEFAULT_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5:3b"
DEFAULT_TIMEOUT = 60.0

_VALID_CATEGORIES = {"hardware": "Hardware", "software": "Software", "network": "Network",
                     "access": "Access", "other": "Other"}
_VALID_PRIORITIES = {"low": "Low", "medium": "Medium", "high": "High"}


class AIError(Exception):
    """Base class for AI failures."""


class AIUnavailableError(AIError):
    """Ollama could not be reached, timed out, or returned an HTTP error."""


class AIInvalidResponseError(AIError):
    """Ollama answered, but not with valid triage JSON."""


def _settings() -> tuple[str, str, float]:
    """Read OLLAMA_* from the app settings (.env), else from plain env vars.

    Falls back when settings can't load (e.g. DATABASE_URL missing in a unit test).
    """
    try:
        from app.core.config import get_settings

        s = get_settings()
        return s.ollama_url, s.ollama_model, float(s.ollama_timeout)
    except Exception:
        pass
    return (
        os.getenv("OLLAMA_URL", DEFAULT_URL),
        os.getenv("OLLAMA_MODEL", DEFAULT_MODEL),
        float(os.getenv("OLLAMA_TIMEOUT", DEFAULT_TIMEOUT)),
    )


def extract_json(text: str) -> dict:
    """Pull the first JSON object out of the model's text.

    Small models sometimes wrap JSON in ```json fences or add a sentence before it.
    """
    if not text or not text.strip():
        raise ValueError("empty response")
    cleaned = re.sub(r"```(?:json)?", "", text).strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start == -1 or end <= start:
            raise ValueError("no JSON object found")
        data = json.loads(cleaned[start:end + 1])
    if not isinstance(data, dict):
        raise ValueError("JSON is not an object")
    return data


def _match_label(value: str, allowed: dict) -> str:
    """'hardware' or 'Hardware: physical devices' -> 'Hardware'. Unknown values are
    returned unchanged so validation rejects them."""
    v = value.strip().lower()
    if v in allowed:
        return allowed[v]
    first = re.split(r"[\s:\-/(,]+", v, maxsplit=1)[0]
    return allowed.get(first, value)


def normalize(data: dict) -> dict:
    """Fix harmless differences (case, 'troubleshooting_steps' key, string steps)."""
    out = dict(data)
    if "steps" not in out and "troubleshooting_steps" in out:
        out["steps"] = out.pop("troubleshooting_steps")
    if isinstance(out.get("category"), str):
        out["category"] = _match_label(out["category"], _VALID_CATEGORIES)
    if isinstance(out.get("priority"), str):
        out["priority"] = _match_label(out["priority"], _VALID_PRIORITIES)
    if isinstance(out.get("steps"), str):
        out["steps"] = [s for s in re.split(r"\n+|;\s*", out["steps"]) if s.strip()]
    return out


def parse_response(text: str) -> AIResult:
    """Text from the model -> validated AIResult, or ValueError/ValidationError.

    reason/steps are passed through redact_secrets as a second safety net, so a
    secret the model repeats is never stored or shown to staff.
    """
    result = AIResult.model_validate(normalize(extract_json(text)))
    result.reason = redact_secrets(result.reason)
    result.steps = [redact_secrets(s) for s in result.steps]
    return result


class OllamaClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
        transport: Optional[httpx.BaseTransport] = None,
        max_attempts: int = 2,
    ):
        url, mdl, tmo = _settings()
        self.base_url = (base_url or url).rstrip("/")
        self.model = model or mdl
        self.timeout = timeout if timeout is not None else tmo
        self.max_attempts = max_attempts
        self._transport = transport  # tests pass httpx.MockTransport here

    def _client(self) -> httpx.Client:
        return httpx.Client(base_url=self.base_url, timeout=self.timeout, transport=self._transport)

    def _chat(self, messages: list[dict]) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "format": "json",  # ask Ollama to constrain output to JSON
            "options": {"temperature": 0},
        }
        try:
            with self._client() as client:
                resp = client.post("/api/chat", json=payload)
                resp.raise_for_status()
                return resp.json().get("message", {}).get("content", "")
        except httpx.TimeoutException as e:
            raise AIUnavailableError(f"AI model timed out after {self.timeout}s") from e
        except httpx.HTTPStatusError as e:
            raise AIUnavailableError(f"AI service returned HTTP {e.response.status_code}") from e
        except (httpx.HTTPError, ValueError) as e:
            raise AIUnavailableError("AI service is not reachable") from e

    def is_available(self) -> bool:
        try:
            with self._client() as client:
                return client.get("/api/tags").status_code == 200
        except httpx.HTTPError:
            return False

    def analyze(self, title: str, description: str, ticket_id: Optional[int] = None) -> AIResult:
        """Classify a ticket. Logs the ticket ID only, never the description."""
        if looks_like_injection(title, description):
            logger.warning("Possible prompt injection in ticket_id=%s", ticket_id)
        if contains_secret(title, description):
            logger.warning("Secret-like text redacted from prompt for ticket_id=%s", ticket_id)

        messages = build_messages(title, description)
        last_error: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            text = self._chat(messages)
            try:
                result = parse_response(text)
                logger.info("AI analyzed ticket_id=%s attempt=%d category=%s priority=%s",
                            ticket_id, attempt, result.category, result.priority)
                return result
            except (ValueError, ValidationError) as e:
                last_error = e
                logger.warning("AI returned invalid output for ticket_id=%s attempt=%d",
                               ticket_id, attempt)
        raise AIInvalidResponseError("AI returned an invalid response") from last_error


def get_ollama_client() -> OllamaClient:
    """FastAPI dependency (override it in tests)."""
    return OllamaClient()
