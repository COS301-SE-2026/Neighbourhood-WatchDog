from app.models.alert import DetectionType
from app.services.notifications.policy import NotificationPolicy
from app.services.notifications.policies.join_request import JoinRequest
from app.services.notifications.policies.property_invite import PropertyInvite
from app.services.notifications.policies.tracking_match import TrackingMatch
from app.services.notifications.policies.weapon_detected import WeaponDetected

class NotificationPolicyFactory:
    def __init__(
        self,
        _registry: dict[DetectionType, NotificationPolicy]
    ):
        self._registry = _registry