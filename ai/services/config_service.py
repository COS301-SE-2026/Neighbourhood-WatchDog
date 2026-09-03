from app_config import save_config, load_config, clear_config


class ConfigService:
    """Handles persistent WatchDog agent configuration."""

    def save(self, data: dict) -> None:
        save_config(data)

    def load(self) -> dict | None:
        return load_config()

    def is_configured(self) -> bool:
        return load_config() is not None

    def clear(self) -> None:
        clear_config()