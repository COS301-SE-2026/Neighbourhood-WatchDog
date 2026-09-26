
from app.services.notifications.policy import NotificationPolicy
from app.services.notifications.policies.join_request import build_join_request_policy, build_join_request_resolved_policy
from app.services.notifications.policies.property_invite import build_property_invite_policy
from app.services.notifications.policies.tracking_match import build_tracking_match_policy
from app.services.notifications.policies.weapon_detected import build_weapon_detected_policy
from app.services.notifications.policies.neighbourhood_wide import build_neighbourhood_wide_broadcast_policy
from app.services.notifications.policies.general_detection import build_neighbourhood_general_detection_policy
from app.schemas.notification import EventType

class NotificationPolicyFactory:
    _registry: dict[EventType, NotificationPolicy] = {}

    @classmethod
    def get(cls, event_type: EventType) -> NotificationPolicy:
        return cls._registry[event_type]

    @classmethod
    def _register(cls, event_type: EventType, policy: NotificationPolicy) -> None:
        cls._registry[event_type] = policy

NotificationPolicyFactory._register(EventType.WEAPON_DETECTED, build_weapon_detected_policy())
NotificationPolicyFactory._register(EventType.NEIGHBOURHOOD_BROADCAST, build_neighbourhood_wide_broadcast_policy())
NotificationPolicyFactory._register(EventType.GENERAL_DETECTION, build_neighbourhood_general_detection_policy())
NotificationPolicyFactory._register(EventType.TRACKING_MATCH, build_tracking_match_policy())
NotificationPolicyFactory._register(EventType.PROPERTY_INVITE, build_property_invite_policy())
NotificationPolicyFactory._register(EventType.JOIN_REQUEST, build_join_request_policy())
NotificationPolicyFactory._register(EventType.JOIN_REQUEST_RESOLVED, build_join_request_resolved_policy())