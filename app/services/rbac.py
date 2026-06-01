from app.core.constants import ROLE_HIERARCHY, UserRole


class AuthorizationError(Exception):
    pass


def ensure_role(user_roles: list[UserRole] | tuple[UserRole, ...], required_role: UserRole) -> None:
    allowed_roles = set()
    for role in user_roles:
        allowed_roles.update(ROLE_HIERARCHY[role])

    if required_role not in allowed_roles:
        raise AuthorizationError(f"role required: {required_role.value}")
