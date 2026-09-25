from app.services.notifications.policy import NotificationPolicy
from app.services.notifications.policy_builder import NotificationPolicyBuilder
from app.services.notifications.channels.email_channel import EmailChannel
from app.services.notifications.channels.websocket_channel import WebSocketChannel
from app.services.notifications.channels.push_channel import PushChannel
from app.services.notifications.channels.whatsapp_channel import WhatsAppChannel
from app.services.notifications.recipients import (
    resolve_neighbourhood_officers
)

def build_tracking_match_policy() -> NotificationPolicy:
    return (
        NotificationPolicyBuilder()
        .with_channel(WebSocketChannel())
        .with_recipient_resolver(resolve_neighbourhood_officers)
        .build()
    )