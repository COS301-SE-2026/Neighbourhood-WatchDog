from app.services.notifications.policy import NotificationPolicy
from app.services.notifications.policy_builder import NotificationPolicyBuilder
from app.services.notifications.channels.email_channel import EmailChannel
from app.services.notifications.channels.push_channel import PushChannel
from app.services.notifications.channels.whatsapp_channel import WhatsAppChannel
from app.services.notifications.recipients import (
    resolve_neighbourhood_officers
)

def build_property_invite_policy() -> NotificationPolicy:
    return (
        NotificationPolicyBuilder()
        .with_channel(EmailChannel())# not too sure whether we should include email since it is a notification of something that has already happened
        .with_channel(PushChannel()) 
        .with_channel(WhatsAppChannel())
        .with_recipient_resolver(resolve_neighbourhood_officers)
        .build()
    )