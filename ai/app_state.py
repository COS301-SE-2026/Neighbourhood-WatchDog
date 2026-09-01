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
    property_id: str | None = None
    address: str | None = None
    cameras: list = field(default_factory=list)
    created_at: str | None = None
    agent_status: str = "stopped"
    is_paired: bool = False

    # Non-secret configuration loaded after pairing.
    config_data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_config(
        cls,
        config_data: dict[str, Any],
        api_key: str | None,
    ) -> "AppState":
        return cls(
            api_key=api_key,
            property_id=(
                str(config_data["property_id"])
                if config_data.get("property_id") is not None
                else None
            ),
            address=config_data.get("address"),
            cameras=list(config_data.get("cameras") or []),
            created_at=(
                str(config_data["created_at"])
                if config_data.get("created_at") is not None
                else None
            ),
            config_data=dict(config_data),
            is_paired=bool(config_data and api_key),
        )