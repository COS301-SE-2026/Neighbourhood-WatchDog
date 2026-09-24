from abc import ABC

from app.core.database import DbSession

class NotificationChannel(ABC):
    """The abstract parent class for the notifcation channels"""