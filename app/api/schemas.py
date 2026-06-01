from pydantic import BaseModel, Field

from app.core.constants import UserRole


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    username: str
    roles: list[UserRole]
    auth_mode: str
