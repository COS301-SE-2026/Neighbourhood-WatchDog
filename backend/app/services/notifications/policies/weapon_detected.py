from app.services.notifications.policy import NotificationPolicy
from app.services.notifications.policy_builder import NotificationPolicyBuilder
from app.services.notifications.channels.email_channel import EmailChannel
from app.services.notifications.channels.websocket_channel import WebSocketChannel
from app.services.notifications.channels.push_channel import PushChannel
from app.services.notifications.channels.whatsapp_channel import WhatsAppChannel
from app.services.notifications.recipients import (
    resolve_neighbourhood_admins_officers_and_property_users
)

def build_weapon_detected_policy() -> NotificationPolicy:
    return (
        NotificationPolicyBuilder()
        .with_channel(WebSocketChannel())
        .with_channel(PushChannel())
        .with_channel(EmailChannel())
        .with_channel(WhatsAppChannel())
        .with_recipient_resolver(resolve_neighbourhood_admins_officers_and_property_users)
        .build()
    )