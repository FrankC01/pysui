#    Copyright 2022 Frank V. Castellucci
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#        http://www.apache.org/licenses/LICENSE-2.0
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

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
    DEFAULT_LOCAL_URL = "http://127.0.0.1:5001"

    def __init__(self, active_address: str, keystore_file: str, current_url: str) -> None:
        """Initialize the default config."""
        self._active_address = SuiAddress.from_hex_string(active_address)
        self._current_keystore_file = keystore_file
        self._current_url = current_url

    @classmethod
    def _parse_config(cls, fpath: Path, config_file: TextIOWrapper) -> tuple[str, str, str]:
        """Open configuration file and generalize for ingestion."""
        kfpath = fpath.parent
        sui_config = yaml.safe_load(config_file)
        active_address = sui_config["active_address"] if "active_address" in sui_config else None
        keystore_file = Path(sui_config["keystore"]["File"]) if "keystore" in sui_config else None
        if "client_type" in sui_config and "rpc" in sui_config["client_type"]:
            current_url = sui_config["client_type"]["rpc"]
        else:
            current_url = None
        if not active_address or not keystore_file:
            raise SuiConfigFileError(f"{fpath} is not a valid SUI configuration file.")
        keystore_file = str(kfpath.joinpath(keystore_file.name).absolute())
        match type(current_url).__name__:
            case "NoneType":
                current_url = cls.DEFAULT_LOCAL_URL
            case "list":
                current_url = current_url[0]

        return (active_address, keystore_file, current_url)

    @classmethod
    def default(cls) -> "SuiConfig":
        """Load the default Sui Config from well known path."""
        expanded_path = os.path.expanduser(cls.DEFAULT_PATH_STRING)
        if os.path.exists(expanded_path):
            with open(expanded_path, encoding="utf8") as core_file:
                return cls(*cls._parse_config(Path(expanded_path), core_file))
        else:
            raise SuiFileNotFound(f"{expanded_path} not found.")

    @classmethod
    def from_config_file(cls, infile: str) -> "SuiConfig":
        """Load the local Sui Config from well known path."""
        expanded_path = os.path.expanduser(infile)
        if os.path.exists(expanded_path):
            with open(expanded_path, encoding="utf8") as core_file:
                return cls(*cls._parse_config(Path(expanded_path), core_file))
        else:
            raise SuiFileNotFound(f"{expanded_path} not found.")

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
