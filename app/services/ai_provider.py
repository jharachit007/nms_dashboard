import json
from dataclasses import dataclass
from typing import Protocol

import requests

from app.core.config import Settings


class AIProviderError(Exception):
    """Raised when an AI provider cannot generate a recommendation."""


@dataclass(frozen=True)
class AIProviderResponse:
    provider: str
    model_name: str | None
    response_text: str
    recommendation: dict
    confidence_score: float | None


class AIProvider(Protocol):
    provider_name: str
    model_name: str | None

    def generate(self, prompt: str) -> AIProviderResponse:
        ...


class MockAIProvider:
    provider_name = "mock"
    model_name = "mcp-deterministic-advisory"

    def generate(self, prompt: str) -> AIProviderResponse:
        recommendation = {
            "summary": "Critical OpenNMS alert requires NOC review.",
            "probable_causes": [
                "Recent service or interface degradation on the affected node.",
                "Resource saturation, dependency failure, or network reachability issue.",
            ],
            "troubleshooting_steps": [
                "Review the sanitized alert message and UEI for the failure domain.",
                "Check recent related events for the same node.",
                "Validate service health and dependency reachability using approved NOC runbooks.",
                "Escalate if the alert persists after standard checks.",
            ],
            "confidence_score": 0.55,
            "suggested_next_checks": [
                "Correlate with recent events and outages for this node.",
                "Check whether the alert has already been acknowledged or cleared.",
                "Confirm if similar critical alerts are active in the same circle/operator group.",
            ],
            "advisory_only": True,
        }
        return AIProviderResponse(
            provider=self.provider_name,
            model_name=self.model_name,
            response_text=json.dumps(recommendation, sort_keys=True),
            recommendation=recommendation,
            confidence_score=0.55,
        )


class OllamaProvider:
    provider_name = "ollama"

    def __init__(self, settings: Settings) -> None:
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model_name = settings.llm_model_name or "llama3.1"
        self.timeout_seconds = settings.llm_timeout_seconds

    def generate(self, prompt: str) -> AIProviderResponse:
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "format": "json",
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        text = payload.get("response", "")
        recommendation = parse_recommendation_text(text)
        return AIProviderResponse(
            provider=self.provider_name,
            model_name=self.model_name,
            response_text=text,
            recommendation=recommendation,
            confidence_score=_confidence_from_recommendation(recommendation),
        )


class OpenAIProvider:
    provider_name = "openai"

    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise AIProviderError("openai_api_key is required for OpenAI provider")
        self.base_url = settings.openai_base_url.rstrip("/")
        self.api_key = settings.openai_api_key
        self.model_name = settings.llm_model_name or "gpt-4o-mini"
        self.timeout_seconds = settings.llm_timeout_seconds

    def generate(self, prompt: str) -> AIProviderResponse:
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        text = response.json()["choices"][0]["message"]["content"]
        recommendation = parse_recommendation_text(text)
        return AIProviderResponse(
            provider=self.provider_name,
            model_name=self.model_name,
            response_text=text,
            recommendation=recommendation,
            confidence_score=_confidence_from_recommendation(recommendation),
        )


class AnthropicProvider:
    provider_name = "anthropic"

    def __init__(self, settings: Settings) -> None:
        if not settings.anthropic_api_key:
            raise AIProviderError("anthropic_api_key is required for Anthropic provider")
        self.base_url = settings.anthropic_base_url.rstrip("/")
        self.api_key = settings.anthropic_api_key
        self.model_name = settings.llm_model_name or "claude-3-5-haiku-latest"
        self.timeout_seconds = settings.llm_timeout_seconds

    def generate(self, prompt: str) -> AIProviderResponse:
        response = requests.post(
            f"{self.base_url}/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": self.model_name,
                "max_tokens": 1200,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        content = response.json().get("content", [])
        text = "".join(part.get("text", "") for part in content if part.get("type") == "text")
        recommendation = parse_recommendation_text(text)
        return AIProviderResponse(
            provider=self.provider_name,
            model_name=self.model_name,
            response_text=text,
            recommendation=recommendation,
            confidence_score=_confidence_from_recommendation(recommendation),
        )


def build_ai_provider(settings: Settings) -> AIProvider:
    provider = settings.llm_provider.lower()
    if provider == "mock":
        return MockAIProvider()
    if provider == "ollama":
        return OllamaProvider(settings)
    if provider == "openai":
        return OpenAIProvider(settings)
    if provider == "anthropic":
        return AnthropicProvider(settings)
    raise AIProviderError(f"unsupported LLM provider: {settings.llm_provider}")


def parse_recommendation_text(text: str) -> dict:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = {"summary": text.strip() or "No recommendation returned."}
    if not isinstance(parsed, dict):
        parsed = {"summary": str(parsed)}

    recommendation = {
        "summary": str(parsed.get("summary", "Critical alert requires review.")),
        "probable_causes": _list_value(parsed.get("probable_causes")),
        "troubleshooting_steps": _list_value(parsed.get("troubleshooting_steps")),
        "confidence_score": _clamp_confidence(parsed.get("confidence_score")),
        "suggested_next_checks": _list_value(parsed.get("suggested_next_checks")),
        "advisory_only": True,
    }
    return recommendation


def _list_value(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _clamp_confidence(value) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, min(1.0, parsed))


def _confidence_from_recommendation(recommendation: dict) -> float | None:
    return _clamp_confidence(recommendation.get("confidence_score"))
