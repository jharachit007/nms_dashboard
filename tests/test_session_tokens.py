import pytest

from app.core.config import Settings
from app.core.constants import UserRole
from app.services.auth_service import AuthenticatedUser
from app.services.session_tokens import SessionTokenError, create_session_token, parse_session_token


def test_session_token_round_trip_preserves_user_and_roles() -> None:
    settings = Settings(session_token_secret="test-secret")
    token = create_session_token(
        AuthenticatedUser(username="noc-user", roles=[UserRole.NOC_OPERATOR]),
        settings,
    )

    user = parse_session_token(token, settings)

    assert user.username == "noc-user"
    assert user.roles == [UserRole.NOC_OPERATOR]


def test_session_token_rejects_tampering() -> None:
    settings = Settings(session_token_secret="test-secret")
    token = create_session_token(
        AuthenticatedUser(username="noc-user", roles=[UserRole.NOC_OPERATOR]),
        settings,
    )
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")

    with pytest.raises(SessionTokenError):
        parse_session_token(tampered, settings)
