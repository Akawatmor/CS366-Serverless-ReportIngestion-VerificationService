"""
Enums — all controlled vocabulary used across the service.
Matches the ENUM definitions in Service Proposal.
"""
from enum import Enum


class ValidationStatus(str, Enum):
    """Report lifecycle states."""
    RECEIVED = "RECEIVED"
    PENDING_REVIEW = "PENDING_REVIEW"
    VERIFIED = "VERIFIED"
    SPAM = "SPAM"
    REJECTED = "REJECTED"
    DUPLICATE = "DUPLICATE"
    DELETED = "DELETED"


class SourcePlatform(str, Enum):
    """Allowed reporter sources."""
    TWITTER = "TWITTER"
    FACEBOOK = "FACEBOOK"
    LINE = "LINE"
    OFFICIAL_APP = "OFFICIAL_APP"
    IOT_SENSOR = "IOT_SENSOR"


class IncidentType(str, Enum):
    """Disaster / incident categories."""
    FIRE = "FIRE"
    FLOOD = "FLOOD"
    EARTHQUAKE = "EARTHQUAKE"
    ACCIDENT = "ACCIDENT"
    SOS = "SOS"
    DAMAGE = "DAMAGE"
    OTHER = "OTHER"


class SeverityLevel(int, Enum):
    """Severity scale 1-5."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    CATASTROPHIC = 5


class AuditActionType(str, Enum):
    """Types of auditable actions."""
    STATUS_CHANGE = "STATUS_CHANGE"
    DATA_EDIT = "DATA_EDIT"
    SOFT_DELETE = "SOFT_DELETE"
    AI_ANALYSIS = "AI_ANALYSIS"


class VerificationAction(str, Enum):
    """Action taken after verification."""
    TRIGGER_NEW_INCIDENT = "TRIGGER_NEW_INCIDENT"
    MERGED_EXISTING_INCIDENT = "MERGED_EXISTING_INCIDENT"
    NO_ACTION = "NO_ACTION"


# Severity keywords for queue prioritization (Thai + English)
SEVERITY_KEYWORDS = [
    "ติดอยู่", "หายใจไม่ออก", "ช่วยด้วย", "คนติด", "ถล่ม",
    "trapped", "can't breathe", "help", "collapsed", "critical",
    "ไฟไหม้", "น้ำท่วม", "แผ่นดินไหว", "SOS", "emergency",
]
