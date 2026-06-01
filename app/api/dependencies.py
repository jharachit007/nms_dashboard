from collections.abc import Callable

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.constants import ROLE_HIERARCHY, UserRole
from app.db.session import get_db_session
from app.services.auth_service import AuthenticatedUser
from app.services.session_tokens import SessionTokenError, parse_session_token


def get_db(db: Session = Depends(get_db_session)) -> Session:
    return db


def get_current_user(
    authorization: str | None = Header(default=None),
    x_user: str | None = Header(default=None),
    x_roles: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> AuthenticatedUser:
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        try:
            return parse_session_token(token, settings)
        except SessionTokenError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid session token",
            ) from exc

    if not x_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="authenticated user header or bearer token is required",
        )

    roles = []
    for role in (x_roles or UserRole.NOC_VIEWER.value).split(","):
        role = role.strip()
        if role:
            try:
                roles.append(UserRole(role))
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"unsupported role: {role}",
                ) from exc

    return AuthenticatedUser(username=x_user, roles=roles or [UserRole.NOC_VIEWER])


def require_role(required_role: UserRole) -> Callable[[AuthenticatedUser], AuthenticatedUser]:
    def dependency(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        allowed_roles = set()
        for role in user.roles:
            allowed_roles.update(ROLE_HIERARCHY[role])

        if required_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"role required: {required_role.value}",
            )
        return user

    return dependency
