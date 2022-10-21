"""Default Sui Configuration."""


import os
from io import TextIOWrapper

from pathlib import Path
import yaml
from abstracts import ClientConfiguration
from sui.sui_crypto import SuiAddress
from sui.sui_excepts import SuiConfigFileError, SuiFileNotFound


class SuiConfig(ClientConfiguration):
    """Sui default configuration class."""

    DEFAULT_PATH_STRING = "~/.sui/sui_config/client.yaml"

    def __init__(self, config_file: TextIOWrapper) -> None:
        """Initialize the default config."""
        sui_config = yaml.safe_load(config_file)
        self._active_address = SuiAddress.from_hex_string(sui_config["active_address"])
        # 0.9.0
        # self._current_url = sui_config["gateway"]["rpc"][0]
        # 0.10.0
        self._current_url = sui_config["client_type"]["rpc"][0]
        self._current_keystore_file = sui_config["keystore"]["File"]

    @classmethod
    def from_path(cls, unique_path: Path) -> ClientConfiguration:
        """Load configuration from supplied path."""
        if unique_path.exists():
            try:
                with open(str(unique_path), encoding="utf8") as core_file:
                    return SuiConfig(core_file)
            except (IOError, yaml.YAMLError) as exc:
                raise SuiConfigFileError(exc) from exc
        else:
            raise SuiFileNotFound(str(unique_path))

    @classmethod
    def default(cls) -> ClientConfiguration:
        """Load the default Sui Config from well known path."""
        expanded_path = os.path.expanduser(cls.DEFAULT_PATH_STRING)
        if os.path.exists(expanded_path):
            try:
                with open(expanded_path, encoding="utf8") as core_file:
                    return SuiConfig(core_file)
            except (IOError, yaml.YAMLError) as exc:
                raise SuiConfigFileError(exc) from exc
        else:
            raise SuiFileNotFound(cls.DEFAULT_PATH_STRING)

    @property
    def url(self) -> str:
        """Return the current URL."""
        return self._current_url

    @property
    def active_address(self) -> str:
        """Return the current address."""
        return self._active_address

    @property
    def keystore_file(self) -> str:
        """Return the fully qualified keystore path."""
        return self._current_keystore_file
