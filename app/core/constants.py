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


ROLE_HIERARCHY: dict[UserRole, set[UserRole]] = {
    UserRole.NOC_VIEWER: {UserRole.NOC_VIEWER},
    UserRole.NOC_OPERATOR: {UserRole.NOC_VIEWER, UserRole.NOC_OPERATOR},
    UserRole.NOC_ADMIN: {
        UserRole.NOC_VIEWER,
        UserRole.NOC_OPERATOR,
        UserRole.NOC_ADMIN,
    },
}
