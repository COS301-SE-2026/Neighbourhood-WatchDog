from dataclasses import dataclass
from enum import Enum
from typing import Any

from services.config_service import ConfigService
from services.keyring_service import KeyringService


class StartupDestination(str, Enum):
    INSTALLER = "installer"
    MAIN_APPLICATION = "main_application"


@dataclass
class StartupDecision:
    destination: StartupDestination
    config_data: dict[str, Any] | None = None
    api_key: str | None = None
    reason: str | None = None

# Decide whether the user should be sent to the setup/pairing page or the main application.
class StartupResolver:
    """
    Determines which screen should be shown when the application opens.

    This class does not know anything about Tkinter widgets.
    """

    def __init__(
        self,
        config_service: ConfigService | None = None,
        keyring_service: KeyringService | None = None,
    ) -> None:
        self.config_service = config_service or ConfigService()
        self.keyring_service = keyring_service or KeyringService()

    def resolve(self) -> StartupDecision:
        try:
            config_data = self.config_service.load()
        except (OSError, ValueError, TypeError):
            return StartupDecision(
                destination=StartupDestination.INSTALLER,
                reason="configuration_unavailable",
            )

        if not isinstance(config_data, dict) or not config_data:
            return StartupDecision(
                destination=StartupDestination.INSTALLER,
                reason="configuration_missing",
            )

        try:
            api_key = self.keyring_service.get_api_key()
        except Exception:
            return StartupDecision(
                destination=StartupDestination.INSTALLER,
                reason="credential_store_unavailable",
            )

        if not api_key:
            return StartupDecision(
                destination=StartupDestination.INSTALLER,
                reason="api_key_missing",
            )

        return StartupDecision(
            destination=StartupDestination.MAIN_APPLICATION,
            config_data=config_data,
            api_key=api_key,
        )