from dataclasses import dataclass
from enum import Enum
from typing import Any

from services.config_service import ConfigService
from services.keyring_service import KeyringService
from services.authentication_service import AuthenticationService, CredentialStatus
from services.dependency_service import DependencyService
from services.benchmark_state_service import (
    BenchmarkStateService,
)

class StartupDestination(str, Enum):
    INSTALLER = "installer"
    BENCHMARK = "benchmark"
    AUTHENTICATION = "authentication"
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
        dependency_service: DependencyService | None = None,
        benchmark_state_service: BenchmarkStateService | None = None,
        authentication_service: AuthenticationService | None = None,
    ) -> None:
        self.config_service = config_service or ConfigService()
        self.keyring_service = keyring_service or KeyringService()
        self.dependency_service = dependency_service or DependencyService()
        self.benchmark_state_service = benchmark_state_service or BenchmarkStateService()
        self.authentication_service = authentication_service or AuthenticationService()

    def resolve(self) -> StartupDecision:
        dependency_decision = self._resolve_dependencies()

        if dependency_decision is not None:
            return dependency_decision

        if not self.benchmark_state_service.has_accepted_result():
            return StartupDecision(
                destination=StartupDestination.BENCHMARK,
                reason="benchmark_required",
            )

        return self.resolve_authentication()

    def resolve_authentication(self) -> StartupDecision:
        """Checks config, api key, backend validation, assumes dependencies already installed"""
        try:
            config_data = self.config_service.load()
        except (OSError, ValueError, TypeError):
            return StartupDecision(
                destination=StartupDestination.AUTHENTICATION,
                reason="configuration_unavailable",
            )

        if not isinstance(config_data, dict) or not config_data:
            return StartupDecision(
                destination=StartupDestination.AUTHENTICATION,
                reason="configuration_missing",
            )

        try:
            api_key = self.keyring_service.get_api_key()
        except Exception:
            return StartupDecision(
                destination=StartupDestination.AUTHENTICATION,
                reason="credential_store_unavailable",
            )

        if not api_key:
            return StartupDecision(
                destination=StartupDestination.AUTHENTICATION,
                reason="api_key_missing",
            )

        result = self.authentication_service.validate_api_key(api_key)

        if result.status is CredentialStatus.INVALID:
            return StartupDecision(
                destination=StartupDestination.AUTHENTICATION,
                reason="api_key_invalid",
            )

        reason = (
            "api_key_valid"
            if result.status is CredentialStatus.VALID
            else "backend_unavailable"
        )

        return StartupDecision(
            destination=StartupDestination.MAIN_APPLICATION,
            config_data=config_data,
            api_key=api_key,
            reason=reason,
        )

    def _resolve_dependencies(self) -> StartupDecision | None:
        """Returns INSTALLER decision if dependencies are invalid otherwise proceeds to authentication"""
        problems = self.dependency_service.get_problems()

        if not problems:
            return None

        return StartupDecision(
            destination=StartupDestination.INSTALLER,
            reason=f"dependencies_invalid:{','.join(problems)}",
        )