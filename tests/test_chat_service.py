from types import SimpleNamespace

from app.core.config import Settings
from app.core.constants import UserRole
from app.services.ai_provider import AIProviderResponse
from app.services.chat_context_retrieval import RetrievedChatContext
from app.services.chat_service import ChatRequest, ChatService
from app.services.rbac import AuthorizationError


class FakeDB:
    def __init__(self) -> None:
        self.commits = 0

    def commit(self) -> None:
        self.commits += 1


class FakeProvider:
    provider_name = "fake"
    model_name = "fake-model"

    def __init__(self) -> None:
        self.prompt = None

    def generate(self, prompt: str) -> AIProviderResponse:
        self.prompt = prompt
        return AIProviderResponse(
            provider="fake",
            model_name="fake-model",
            response_text='{"summary": "Check [IP]", "confidence_score": 0.5}',
            recommendation={"summary": "Check [IP]", "confidence_score": 0.5},
            confidence_score=0.5,
        )


class FakeAlertRepository:
    def get(self, alert_id: int):
        return SimpleNamespace(id=alert_id)


class FakeRecommendationRepository:
    def get_by_alert_id(self, alert_id: int):
        return SimpleNamespace(id=50)


class FakeSessionRepository:
    def __init__(self) -> None:
        self.created = []

    def create(self, alert_id: int, user_id: str, title: str | None = None):
        session = SimpleNamespace(id=300, alert_id=alert_id, user_id=user_id, title=title)
        self.created.append(session)
        return session

    def get_for_user(self, session_id: int, user_id: str):
        return SimpleNamespace(id=session_id, alert_id=1, user_id=user_id)


class FakeMessageRepository:
    def __init__(self) -> None:
        self.messages = []

    def create_message(self, values: dict):
        message = SimpleNamespace(id=len(self.messages) + 1, **values)
        self.messages.append(message)
        return message


class FakeContextEngine:
    def retrieve(self, alert_id: int, user_question: str) -> RetrievedChatContext:
        assert "10.20.30.40" not in user_question
        return RetrievedChatContext(
            alert_id=alert_id,
            context={},
            sanitized_text='{"question": "What happened to [IP]?"}',
            sanitized_context={"sanitized_json": "{}", "truncated": False},
            truncated=False,
        )


class FakeAuditService:
    def __init__(self) -> None:
        self.entries = []

    def record(self, **kwargs) -> None:
        self.entries.append(kwargs)


def _service() -> ChatService:
    service = ChatService.__new__(ChatService)
    service.db = FakeDB()
    service.settings = Settings(llm_max_input_chars=10_000)
    service.provider = FakeProvider()
    service.alert_repository = FakeAlertRepository()
    service.recommendation_repository = FakeRecommendationRepository()
    service.session_repository = FakeSessionRepository()
    service.message_repository = FakeMessageRepository()
    service.context_engine = FakeContextEngine()
    service.audit_service = FakeAuditService()
    return service


def test_chat_service_sanitizes_input_and_stores_advisory_messages() -> None:
    service = _service()
    response = service.ask(
        ChatRequest(
            alert_id=1,
            user_id="operator",
            question="What happened to 10.20.30.40 token=abc?",
            user_roles=(UserRole.NOC_OPERATOR,),
        )
    )

    assert response.session_id == 300
    assert response.advisory_only is True
    assert service.message_repository.messages[0].sanitized_message == "What happened to [IP] token=[REDACTED]?"
    assert service.message_repository.messages[0].message != service.message_repository.messages[0].sanitized_message
    assert service.message_repository.messages[1].role == "assistant"
    assert service.message_repository.messages[1].advisory_only is True
    assert "10.20.30.40" not in service.provider.prompt
    assert service.audit_service.entries[0]["action"] == "chat_interaction"
    assert service.db.commits == 1


def test_chat_service_rejects_viewer_role() -> None:
    service = _service()
    try:
        service.ask(
            ChatRequest(
                alert_id=1,
                user_id="viewer",
                question="What happened?",
                user_roles=(UserRole.NOC_VIEWER,),
            )
        )
    except AuthorizationError:
        pass
    else:
        raise AssertionError("viewer chat should be rejected")
