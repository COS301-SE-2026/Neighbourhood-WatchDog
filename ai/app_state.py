from dataclasses import dataclass


@dataclass
class AppState:
    api_key: str | None = None
    agent_id: str | None = None
    account_name: str | None = None