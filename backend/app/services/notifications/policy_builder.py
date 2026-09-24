from collections.abc import Callable

from app.services.notifications.channel import NotificationChannel
from app.services.notifications.policy import NotificationPolicy

class NotificationPolicyBuilder:
    def with_channel(self, channel: NotificationChannel):
        pass #TODO we finna add to this
        return self

    def with_recipient_resolver(self, fn):
        pass #TODO: implement
        return self

    def with_severity(self, fn):
        pass #TODO: implement
        return self

    def build(self) -> NotificationPolicy:
        pass # TODO: implement