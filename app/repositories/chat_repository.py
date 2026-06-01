from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chat import ChatMessage, ChatSession
from app.repositories.base import BaseRepository


class ChatSessionRepository(BaseRepository[ChatSession]):
    model = ChatSession

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def create(self, alert_id: int, user_id: str, title: str | None = None) -> ChatSession:
        session = ChatSession(alert_id=alert_id, user_id=user_id, title=title)
        self.db.add(session)
        self.db.flush()
        return session

    def get_for_user(self, session_id: int, user_id: str) -> ChatSession | None:
        statement = select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
        )
        return self.db.scalar(statement)


class ChatMessageRepository(BaseRepository[ChatMessage]):
    model = ChatMessage

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def create_message(self, values: dict) -> ChatMessage:
        message = ChatMessage(**values)
        self.db.add(message)
        self.db.flush()
        return message

    def list_session_messages(self, session_id: int, limit: int = 20) -> list[ChatMessage]:
        statement = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())
