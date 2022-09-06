"""Default Sui Configuration."""

import json
from pathlib import Path
import yaml
from abstracts import ClientConfiguration


_DEFAULT_PATH_STRING = "~/.sui/sui_config/client.yaml"


class SuiConfig(ClientConfiguration):
    """Sui default configuration class."""

    def __init__(self, unique_path: str = None) -> None:
        """Initialize the default config."""
        sui_config = None
        use_path = unique_path if unique_path else _DEFAULT_PATH_STRING
        with open(str(Path(use_path).expanduser())) as file:
            try:
                sui_config = yaml.safe_load(file)
                with open(sui_config["keystore"]["File"]) as keyfile:
                    #   TODO: Convert base64 to keypairs
                    self._addresses = json.load(keyfile)
            except yaml.YAMLError as exc:
                raise exc
        # print(sui_config)
        self._active_address = sui_config["active_address"]
        self._current_url = sui_config["gateway"]["rpc"][0]
        self._current_keystore_file = sui_config["keystore"]["File"]

    @property
    def url(self) -> str:
        """Return the current URL."""
        return self._current_url

    @property
    def active_address(self) -> str:
        """Return the current address."""
        return self._active_address

    @property
    def addresses(self) -> list[str]:
        """Return all addresses in configuration."""
        return self._addresses
