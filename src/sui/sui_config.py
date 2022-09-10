"""Default Sui Configuration."""


import os
from io import TextIOWrapper
import json
from pathlib import Path
import yaml
from abstracts import ClientConfiguration, KeyPair
from sui.sui_excepts import SuiConfigFileError, SuiFileNotFound
from sui.sui_crypto import keypair_from_b64address


class SuiConfig(ClientConfiguration):
    """Sui default configuration class."""

    _DEFAULT_PATH_STRING = "~/.sui/sui_config/client.yaml"

    def __init__(self, config_file: TextIOWrapper) -> None:
        """Initialize the default config."""
        sui_config = None
        self._keypairs = {}
        sui_config = yaml.safe_load(config_file)
        with open(sui_config["keystore"]["File"], encoding="utf8") as keyfile:
            self._addresses = json.load(keyfile)
            if len(self._addresses) > 0:
                for addy in self._addresses:
                    self._keypairs[addy] = keypair_from_b64address(addy)
        # print(sui_config)
        self._active_address = sui_config["active_address"]
        self._current_url = sui_config["gateway"]["rpc"][0]
        self._current_keystore_file = sui_config["keystore"]["File"]

    @classmethod
    def from_path(cls, unique_path: Path) -> ClientConfiguration:
        """Load configuration from supplied path."""
        if unique_path.exists():
            try:
                with open(str(unique_path), encoding="utf8") as core_file:
                    return SuiConfig(core_file)
            except (IOError, yaml.YAMLError, json.JSONDecodeError) as exc:
                raise SuiConfigFileError(exc) from exc
        else:
            raise SuiFileNotFound(str(unique_path))

    @classmethod
    def default(cls) -> ClientConfiguration:
        """Load the default Sui Config from well known path."""
        expanded_path = os.path.expanduser(cls._DEFAULT_PATH_STRING)
        if os.path.exists(expanded_path):
            try:
                with open(expanded_path, encoding="utf8") as core_file:
                    return SuiConfig(core_file)
            except (IOError, yaml.YAMLError, json.JSONDecodeError) as exc:
                raise SuiConfigFileError(exc) from exc
        else:
            raise SuiFileNotFound(cls._DEFAULT_PATH_STRING)

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

    def keypair_for_address(self, address: str = None) -> KeyPair:
        """Return keypair for address."""
        if not address:
            return self._keypairs[self.active_address]
        return self._keypairs[address]
