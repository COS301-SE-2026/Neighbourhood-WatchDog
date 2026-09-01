import keyring


class KeyringService:
    """Handles secure storage of WatchDog credentials in the OS keyring."""

    SERVICE_NAME = "WatchDog"

    def save_api_key(self, api_key: str) -> None:
        keyring.set_password(
            self.SERVICE_NAME,
            "api_key",
            api_key
        )

    def get_api_key(self) -> str | None:
        return keyring.get_password(
            self.SERVICE_NAME,
            "api_key"
        )

    def clear_api_key(self) -> None:
        try:
            keyring.delete_password(
                self.SERVICE_NAME,
                "api_key"
            )
        except keyring.errors.PasswordDeleteError:
            pass