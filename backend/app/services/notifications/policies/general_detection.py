from app.services.notifications.policy import NotificationPolicy
from app.services.notifications.policy_builder import NotificationPolicyBuilder
from app.services.notifications.channels.websocket_channel import WebSocketChannel
from app.services.notifications.channels.push_channel import PushChannel
from app.services.notifications.recipients import resolve_neighbourhood_members

def build_neighbourhood_general_detection_policy() -> NotificationPolicy:
    return (
        NotificationPolicyBuilder()
        .with_channel(WebSocketChannel())
        .with_channel(PushChannel())
        .with_recipient_resolver(resolve_neighbourhood_members)
        .build()
    )