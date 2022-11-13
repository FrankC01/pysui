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

# -*- coding: utf-8 -*-


"""Default Sui Configuration."""


import os
from io import TextIOWrapper

from pathlib import Path
import json
import yaml
from ..abstracts import ClientConfiguration, SignatureScheme, KeyPair
from .sui_crypto import SuiAddress, keypair_from_keystring, create_new_address
from .sui_excepts import (
    SuiConfigFileError,
    SuiFileNotFound,
    SuiNoKeyPairs,
    SuiKeystoreFileError,
    SuiKeystoreAddressError,
)


class SuiConfig(ClientConfiguration):
    """Sui default configuration class."""

    DEFAULT_PATH_STRING = "~/.sui/sui_config/client.yaml"
    FAUCET_LOCAL_URL = "http://127.0.0.1:9123"
    FAUCET_DEVNET_URL = "https://faucet.devnet.sui.io:9123"

    def __init__(self, env: str, active_address: str, keystore_file: str, current_url: str) -> None:
        """Initialize the default config."""
        super().__init__(keystore_file)
        self._active_address = SuiAddress.from_hex_string(active_address)
        self._current_url = current_url
        self._current_env = env
        if env == "localnet":
            self._faucet_url = self.FAUCET_LOCAL_URL
        else:
            self._faucet_url = self.FAUCET_DEVNET_URL

        if os.path.exists(keystore_file):
            self._keypairs = {}
            self._addresses = {}
            self._address_keypair = {}
            try:
                with open(keystore_file, encoding="utf8") as keyfile:
                    self._keystrings = json.load(keyfile)
                    if len(self._keystrings) > 0:
                        for keystr in self._keystrings:
                            kpair = keypair_from_keystring(keystr)
                            self._keypairs[keystr] = kpair
                            addy = SuiAddress.from_keypair_string(keystr)
                            self._addresses[addy.address] = addy
                            self._address_keypair[addy.address] = kpair
                    else:
                        raise SuiNoKeyPairs()
            except IOError as exc:
                raise SuiKeystoreFileError(exc) from exc
            except json.JSONDecodeError as exc:
                raise SuiKeystoreAddressError(exc) from exc
        else:
            raise SuiFileNotFound(str(keystore_file))

    def _write_keypair(self, keypair: KeyPair, file_path: str = None) -> None:
        """Register the keypair and write out to keystore file."""
        filepath = file_path if file_path else self.keystore_file
        if os.path.exists(filepath):
            serialized = keypair.to_b64()
            self._keypairs[serialized] = keypair
            with open(filepath, "w", encoding="utf8") as keystore:
                keystore.write(json.dumps(self.keystrings, indent=2))
        else:
            raise SuiFileNotFound((filepath))

    def create_new_keypair_and_address(self, scheme: SignatureScheme) -> str:
        """
        Create a new keypair and address identifier and return the address string.

        The scheme defines generation of ED25519 or SECP256K1 keypairs.
        """
        if scheme == SignatureScheme.ED25519:
            keypair, address = create_new_address(scheme)
            self._addresses[address.address] = address
            self._address_keypair[address.address] = keypair
            self._write_keypair(keypair)
            return address.identifier
        if scheme == SignatureScheme.SECP256K1:
            keypair, address = create_new_address(scheme)
            self._addresses[address.address] = address
            self._address_keypair[address.address] = keypair
            self._write_keypair(keypair)
            return address.identifier

        raise NotImplementedError

    @classmethod
    def _parse_config(cls, fpath: Path, config_file: TextIOWrapper) -> tuple[str, str, str, str]:
        """Open configuration file and generalize for ingestion."""
        kfpath = fpath.parent
        sui_config = yaml.safe_load(config_file)
        active_address = sui_config["active_address"] if "active_address" in sui_config else None
        keystore_file = Path(sui_config["keystore"]["File"]) if "keystore" in sui_config else None
        # active_env is new (0.15.0) and identifies the alias in use in the 'envs' map list
        active_env = sui_config["active_env"] if "active_env" in sui_config else None
        if not active_address or not keystore_file or not active_env:
            raise SuiConfigFileError(f"{fpath} is not a valid SUI configuration file.")
        current_url = None
        # Envs is new (0.15.0), it is a list of maps, where the environment
        # contains RPC url identifed by 'aliases' (i.e. devnet, localnet)
        if "envs" in sui_config:
            for envmap in sui_config["envs"]:
                if active_env == envmap["alias"]:
                    current_url = envmap["rpc"]
                    break
        else:
            raise SuiConfigFileError("'envs' not found in configuration file.")
        keystore_file = str(kfpath.joinpath(keystore_file.name).absolute())
        return (active_env, active_address, keystore_file, current_url)

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

    @classmethod
    def generate_configuration(cls) -> "ClientConfiguration":
        """Generate a default configuration."""
        raise NotImplementedError("SuiConfig.generate_configuration not implemented yet.")

    @property
    def rpc_url(self) -> str:
        """Return the current URL."""
        return self._current_url

    @property
    def active_address(self) -> SuiAddress:
        """Return the current address."""
        return self._active_address

    @property
    def keystore_file(self) -> str:
        """Return the fully qualified keystore path."""
        return self._current_keystore_file

    def set_active_address(self, address: SuiAddress) -> SuiAddress:
        """Change the active address to address."""
        stale_addy = self._active_address
        self._active_address = address
        return stale_addy
