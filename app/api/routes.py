from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.api.schemas import HealthResponse, LoginRequest, LoginResponse
from app.core.config import Settings, get_settings
from app.services.audit_service import AuditService
from app.services.auth_service import AuthenticationError, LDAPAuthService

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.environment,
    )


@router.post(
    "/auth/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> LoginResponse:
    auth_service = LDAPAuthService(settings)
    try:
        user = auth_service.authenticate(payload.username, payload.password)
    except AuthenticationError:
        AuditService(db).record(
            action="user_login_failed",
            user_id=payload.username,
            ip_address=request.client.host if request.client else None,
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid username or password",
        )

    AuditService(db).record(
        action="user_login",
        user_id=user.username,
        ip_address=request.client.host if request.client else None,
        details={"auth_mode": "stub" if settings.ldap_stub_enabled else "ldap"},
    )
    db.commit()
    return LoginResponse(
        username=user.username,
        roles=user.roles,
        auth_mode="stub" if settings.ldap_stub_enabled else "ldap",
    )
