from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.constants import ChatRole, UserRole
from app.repositories.ai_recommendation_repository import AIRecommendationRepository
from app.repositories.alert_repository import AlertRepository
from app.repositories.chat_repository import ChatMessageRepository, ChatSessionRepository
from app.services.ai_provider import AIProvider, build_ai_provider
from app.services.audit_service import AuditService
from app.services.chat_context_retrieval import ChatContextRetrievalEngine
from app.services.rbac import ensure_role
from app.services.sanitization import sanitize_for_llm


@dataclass(frozen=True)
class ChatRequest:
    alert_id: int
    user_id: str
    question: str
    user_roles: tuple[UserRole, ...]
    session_id: int | None = None


@dataclass(frozen=True)
class ChatResponse:
    session_id: int
    user_message_id: int
    assistant_message_id: int
    response_text: str
    provider: str
    advisory_only: bool


class ChatService:
    def __init__(
        self,
        db: Session,
        settings: Settings,
        provider: AIProvider | None = None,
    ) -> None:
        self.db = db
        self.settings = settings
        self.provider = provider or build_ai_provider(settings)
        self.alert_repository = AlertRepository(db)
        self.recommendation_repository = AIRecommendationRepository(db)
        self.session_repository = ChatSessionRepository(db)
        self.message_repository = ChatMessageRepository(db)
        self.context_engine = ChatContextRetrievalEngine(db, settings.llm_max_input_chars)
        self.audit_service = AuditService(db)

    def ask(self, request: ChatRequest) -> ChatResponse:
        ensure_role(request.user_roles, UserRole.NOC_OPERATOR)

        alert = self.alert_repository.get(request.alert_id)
        if alert is None:
            raise ValueError(f"alert not found: {request.alert_id}")

        session = self._get_or_create_session(request)
        recommendation = self.recommendation_repository.get_by_alert_id(request.alert_id)
        sanitized_question = sanitize_for_llm(request.question, self.settings.llm_max_input_chars)
        retrieved_context = self.context_engine.retrieve(request.alert_id, sanitized_question.text)
        prompt = build_chat_prompt(retrieved_context.sanitized_text)
        provider_response = self.provider.generate(prompt)
        sanitized_response = sanitize_for_llm(provider_response.response_text, self.settings.llm_max_input_chars)

        user_message = self.message_repository.create_message(
            {
                "session_id": session.id,
                "alert_id": request.alert_id,
                "ai_recommendation_id": recommendation.id if recommendation else None,
                "user_id": request.user_id,
                "role": ChatRole.USER.value,
                "message": request.question,
                "sanitized_message": sanitized_question.text,
                "context_snapshot": retrieved_context.sanitized_context,
                "advisory_only": True,
            }
        )
        assistant_message = self.message_repository.create_message(
            {
                "session_id": session.id,
                "alert_id": request.alert_id,
                "ai_recommendation_id": recommendation.id if recommendation else None,
                "user_id": "assistant",
                "role": ChatRole.ASSISTANT.value,
                "message": sanitized_response.text,
                "sanitized_message": sanitized_response.text,
                "context_snapshot": retrieved_context.sanitized_context,
                "provider": provider_response.provider,
                "model_name": provider_response.model_name,
                "advisory_only": True,
            }
        )
        self.audit_service.record(
            action="chat_interaction",
            user_id=request.user_id,
            resource_type="alert",
            resource_id=str(request.alert_id),
            details={
                "session_id": session.id,
                "user_message_id": user_message.id,
                "assistant_message_id": assistant_message.id,
                "provider": provider_response.provider,
                "context_truncated": retrieved_context.truncated,
            },
        )
        self.db.commit()
        return ChatResponse(
            session_id=session.id,
            user_message_id=user_message.id,
            assistant_message_id=assistant_message.id,
            response_text=sanitized_response.text,
            provider=provider_response.provider,
            advisory_only=True,
        )

    def _get_or_create_session(self, request: ChatRequest):
        if request.session_id is not None:
            session = self.session_repository.get_for_user(request.session_id, request.user_id)
            if session is None:
                raise ValueError("chat session not found for user")
            if session.alert_id != request.alert_id:
                raise ValueError("chat session does not belong to alert")
            return session

        title = request.question[:120] if request.question else None
        return self.session_repository.create(
            alert_id=request.alert_id,
            user_id=request.user_id,
            title=title,
        )


def build_chat_prompt(sanitized_context: str) -> str:
    return (
        "You are an advisory incident assistant for NOC operators. "
        "Use only the sanitized incident context. "
        "Do not execute commands, restart services, modify infrastructure, or claim remediation. "
        "Answer as JSON with keys summary, probable_causes, troubleshooting_steps, confidence_score, "
        "suggested_next_checks, advisory_only. Include similar incident observations when present.\\n\\n"
        f"Sanitized chat context:\\n{sanitized_context}"
    )
