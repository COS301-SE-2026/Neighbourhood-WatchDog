from app.services.notifications.policy import NotificationPolicy
from app.services.notifications.policy_builder import NotificationPolicyBuilder
from app.services.notifications.channels.email_channel import EmailChannel
from app.services.notifications.channels.push_channel import PushChannel
from app.services.notifications.channels.whatsapp_channel import WhatsAppChannel
from app.services.notifications.recipients import (
    resolve_single_user
)

def build_property_invite_policy() -> NotificationPolicy:
    return (
        NotificationPolicyBuilder()
        .with_channel(EmailChannel())
        .with_channel(PushChannel()) 
        .with_channel(WhatsAppChannel())
        .with_recipient_resolver(resolve_single_user)
        .build()
    )