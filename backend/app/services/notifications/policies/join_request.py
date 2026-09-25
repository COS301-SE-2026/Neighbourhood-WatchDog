from app.services.notifications.policy import NotificationPolicy
from app.services.notifications.policy_builder import NotificationPolicyBuilder
from app.services.notifications.channels.email_channel import EmailChannel
from app.services.notifications.channels.websocket_channel import WebSocketChannel
from app.services.notifications.channels.push_channel import PushChannel
from app.services.notifications.channels.whatsapp_channel import WhatsAppChannel
from app.services.notifications.recipients import (
    resolve_neighbourhood_officers,
    resolve_neighbourhood_members,
    resolve_neighbourhood_residents,
    resolve_neighbourhood_admins,
    resolve_neighbourhood_admins_and_officers,
    resolve_single_user,
    resolve_users_by_id,
)

def build_join_request_policy() -> NotificationPolicy:
    return (
        NotificationPolicyBuilder()
        .with_channel(WebSocketChannel())
        .with_channel(PushChannel())
        .with_channel(EmailChannel())
        .with_channel(WhatsAppChannel())
        .with_recipient_resolver(resolve_neighbourhood_officers)
    )

def build_join_request_resolved_policy() -> NotificationPolicy:
    return (
        NotificationPolicyBuilder()
        .with_channel(WebSocketChannel())
        .with_channel(PushChannel())
        .with_channel(EmailChannel())
        .with_channel(WhatsAppChannel())
        .with_recipient_resolver(resolve_neighbourhood_officers)
    )