from enum import Enum

from app.models.alert import DetectionType
from app.services.notifications.policy import NotificationPolicy
from app.services.notifications.policies.join_request import JoinRequest
from app.services.notifications.policies.property_invite import PropertyInvite
from app.services.notifications.policies.tracking_match import TrackingMatch
from app.services.notifications.policies.weapon_detected import WeaponDetected

class EventType(str, Enum):
    WEAPON_DETECTED = "WEAPON_DETECTED"
    GENERAL_DETECTION = "GENERAL_DETECTION"
    TRACKING_MATCH = "TRACKING_MATCH"
    PROPERTY_INVITE = "PROPERTY_INVITE"
    JOIN_REQUEST = "JOIN_REQUEST"
    JOIN_REQUEST_RESOLVED = "JOIN_REQUEST_RESOLVED"

class NotificationPolicyFactory:
    _registry: dict[EventType, NotificationPolicy] = {}

    @classmethod
    def get(cls, event_type: EventType) -> NotificationPolicy:
        return cls._registry[event_type]

    @classmethod
    def _register(cls, event_type: EventType, policy: NotificationPolicy) -> None:
        cls._registry[event_type] = policy

NotificationPolicyFactory._register(EventType.WEAPON_DETECTED, build_weapon_detected_policy())
NotificationPolicyFactory._register(EventType.TRACKING_MATCH, build_tracking_match_policy())
NotificationPolicyFactory._register(EventType.PROPERTY_INVITE, build_property_invite_policy())
NotificationPolicyFactory._register(EventType.JOIN_REQUEST, build_join_request_policy())
NotificationPolicyFactory._register(EventType.JOIN_REQUEST_RESOLVED, build_join_request_resolved_policy())