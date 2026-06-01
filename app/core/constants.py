from enum import StrEnum


class AlertLifecycleStatus(StrEnum):
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    CLEARED = "CLEARED"


class AlertSeverity(StrEnum):
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    WARNING = "WARNING"
    NORMAL = "NORMAL"
    UNKNOWN = "UNKNOWN"


class UserRole(StrEnum):
    NOC_VIEWER = "noc-viewer"
    NOC_OPERATOR = "noc-operator"
    NOC_ADMIN = "noc-admin"


class FeedbackType(StrEnum):
    HELPFUL = "Helpful"
    NOT_HELPFUL = "Not Helpful"


class ResolutionStatus(StrEnum):
    RESOLVED = "Resolved"
    NOT_RESOLVED = "Not Resolved"


class ChatRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatSessionStatus(StrEnum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


ROLE_HIERARCHY: dict[UserRole, set[UserRole]] = {
    UserRole.NOC_VIEWER: {UserRole.NOC_VIEWER},
    UserRole.NOC_OPERATOR: {UserRole.NOC_VIEWER, UserRole.NOC_OPERATOR},
    UserRole.NOC_ADMIN: {
        UserRole.NOC_VIEWER,
        UserRole.NOC_OPERATOR,
        UserRole.NOC_ADMIN,
    },
}
