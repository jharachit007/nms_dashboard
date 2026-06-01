from dataclasses import dataclass

from ldap3 import Connection, Server

from app.core.config import Settings
from app.core.constants import UserRole


@dataclass(frozen=True)
class AuthenticatedUser:
    username: str
    roles: list[UserRole]


class AuthenticationError(Exception):
    pass


class LDAPAuthService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def authenticate(self, username: str, password: str) -> AuthenticatedUser:
        if not username or not password:
            raise AuthenticationError("username and password are required")

        if self.settings.ldap_stub_enabled:
            # Phase 1 stub: verifies request shape while LDAP endpoint details are configured.
            return AuthenticatedUser(
                username=username,
                roles=[self.settings.ldap_default_role],
            )

        if not self.settings.ldap_server_url or not self.settings.ldap_bind_dn_template:
            raise AuthenticationError("LDAP is not configured")

        bind_dn = self.settings.ldap_bind_dn_template.format(username=username)
        server = Server(self.settings.ldap_server_url)
        try:
            with Connection(server, user=bind_dn, password=password, auto_bind=True):
                return AuthenticatedUser(
                    username=username,
                    roles=[self._resolve_default_role()],
                )
        except Exception as exc:  # ldap3 raises multiple bind/configuration exceptions.
            raise AuthenticationError("LDAP authentication failed") from exc

    def _resolve_default_role(self) -> UserRole:
        return self.settings.ldap_default_role
