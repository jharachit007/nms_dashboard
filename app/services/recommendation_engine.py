from app.services.ai_provider import AIProvider, AIProviderResponse
from app.services.alert_context_builder import AlertContext


class RecommendationEngine:
    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider

    def generate(self, context: AlertContext) -> AIProviderResponse:
        prompt = build_recommendation_prompt(context.sanitized_text)
        return self.provider.generate(prompt)


def build_recommendation_prompt(sanitized_context: str) -> str:
    return (
        "You are an advisory AI assistant for NOC engineers. "
        "Do not execute commands, restart services, modify infrastructure, or claim that remediation was performed. "
        "Use only the sanitized incident context below. "
        "Return JSON with keys: summary, probable_causes, troubleshooting_steps, confidence_score, "
        "suggested_next_checks, advisory_only. Confidence must be a number from 0 to 1. "
        "All recommendations must be advisory only.\\n\\n"
        f"Sanitized incident context:\\n{sanitized_context}"
    )
