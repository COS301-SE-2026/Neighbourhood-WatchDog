from dataclasses import dataclass, field
from typing import Any


@dataclass
class AppState:
    """
    Runtime state held while the desktop application is running.

    Persistent configuration belongs in ConfigService.
    The API key belongs in the OS keyring.
    """

    api_key: str | None = None
    agent_id: str | None = None
    account_name: str | None = None

    # Non-secret configuration loaded after pairing.
    config_data: dict[str, Any] = field(default_factory=dict)

    # Runtime status.
    agent_status: str = "stopped"
    is_paired: bool = False

    @classmethod
    def from_config(
        cls,
        config_data: dict[str, Any],
        api_key: str | None,
    ) -> "AppState":
        """
        Build runtime state from persisted configuration and keyring data.

        The exact config keys should be adjusted after confirming the
        backend pairing response shape.
        """

        return cls(
            api_key=api_key,
            agent_id=(
                str(config_data["agent_id"])
                if config_data.get("agent_id") is not None
                else None
            ),
            account_name=config_data.get("account_name"),
            config_data=dict(config_data),
            is_paired=bool(config_data and api_key),
        )