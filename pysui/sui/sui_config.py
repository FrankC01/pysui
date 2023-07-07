#    Copyright Frank V. Castellucci
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
import logging
from pathlib import Path
import json
from typing import Optional
import yaml
from deprecated.sphinx import versionadded, versionchanged, deprecated
from pysui.abstracts import ClientConfiguration, SignatureScheme, KeyPair
from pysui.sui.sui_constants import (
    EMPEHMERAL_PATH,
    EMPEHMERAL_USER,
    LOCALNET_SUI_URL,
    MAINNET_SOCKET_URL,
    PYSUI_EXEC_ENV,
    PYSUI_CLIENT_CONFIG_ENV,
    DEFAULT_SUI_BINARY_PATH,
    DEFAULT_DEVNET_PATH_STRING,
    DEVNET_SUI_URL,
    DEVNET_FAUCET_URL,
    DEVNET_SOCKET_URL,
    LOCALNET_FAUCET_URL,
    LOCALNET_SOCKET_URL,
    TESTNET_FAUCET_URL,
    TESTNET_SOCKET_URL,
    TESTNET_SUI_URL,
)
from pysui.sui.sui_crypto import (
    SuiAddress,
    create_new_address,
    emphemeral_keys_and_addresses,
    load_keys_and_addresses,
    recover_key_and_address,
)
from pysui.sui.sui_excepts import (
    SuiConfigFileError,
    SuiFileNotFound,
)
from pysui.sui.sui_utils import sui_base_get_config

logger = logging.getLogger("pysui.config")
if not logging.getLogger().handlers:
    logger.addHandler(logging.NullHandler())
    logger.propagate = False


@versionadded(
    version="0.16.1",
    reason="Support for sui-base as well as sharing with signing and publishing",
)
def _set_env_vars(client_config_path: Path, sui_exec_path: Path):
    """_set_env_vars Sets runtime paths to environment variables.

    The most important will be the binary execution for compiling move packages and
    performing MultiSig signing.

    :param client_config_path: _description_
    :type client_config_path: Path
    :param sui_exec_path: _description_
    :type sui_exec_path: Path
    """
    logger.debug(
        f"Setting environment {PYSUI_CLIENT_CONFIG_ENV} to {client_config_path}"
    )
    os.environ[PYSUI_CLIENT_CONFIG_ENV] = str(client_config_path)
    logger.debug(f"Setting environment {PYSUI_EXEC_ENV} to {sui_exec_path}")
    os.environ[PYSUI_EXEC_ENV] = str(sui_exec_path)


# pylint:disable=too-many-instance-attributes,attribute-defined-outside-init,too-many-arguments,unnecessary-dunder-call
class SuiConfig(ClientConfiguration):
    """Sui default configuration class."""

    @versionchanged(version="0.29.0", reason="Now accepts ws url.")
    def _initiate(
        self,
        active_address: str,
        rpc_url: str,
        socket_url: str,
        environment: str,
    ) -> None:
        """."""
        self._active_address = SuiAddress(active_address)
        self._current_url = rpc_url
        self._current_env = environment
        self._local_running = False
        match self._current_env:
            case "devnet":
                self._faucet_url = DEVNET_FAUCET_URL
                self._socket_url = (
                    socket_url if socket_url else DEVNET_SOCKET_URL
                )
            case "testnet":
                self._faucet_url = TESTNET_FAUCET_URL
                self._socket_url = (
                    socket_url if socket_url else TESTNET_SOCKET_URL
                )
            case "localnet":
                self._faucet_url = LOCALNET_FAUCET_URL
                self._socket_url = (
                    socket_url if socket_url else LOCALNET_SOCKET_URL
                )
                self._local_running = True
            case "mainnet":
                self._faucet_url = None
                self._socket_url = (
                    socket_url if socket_url else MAINNET_SOCKET_URL
                )
            case _:
                self._socket_url = socket_url
        (
            self._keypairs,
            self._addresses,
            self._address_keypair,
        ) = load_keys_and_addresses(self.keystore_file)

    def _write_keypair(self, keypair: KeyPair, file_path: str = None) -> None:
        """Register the keypair and write out to keystore file."""
        filepath = file_path if file_path else self.keystore_file
        logger.debug(f"Writing new keypair to {filepath}")
        if os.path.exists(filepath):
            self._keypairs[keypair.serialize()] = keypair
            with open(filepath, "w", encoding="utf8") as keystore:
                keystore.write(json.dumps(self.keystrings, indent=2))
        else:
            raise SuiFileNotFound((filepath))

    @versionchanged(
        version="0.21.2", reason="Corrected signature return values."
    )
    @versionchanged(
        version="0.25.0", reason="Support emphemeral configuration."
    )
    def create_new_keypair_and_address(
        self,
        scheme: SignatureScheme,
        mnemonics: str = None,
        derivation_path: str = None,
    ) -> tuple[str, SuiAddress]:
        """create_new_keypair_and_address Create a new keypair and address identifier and writes to client.yaml.

        :param scheme: Identifies whether new key is ed25519, secp256k1 or secp256r1
        :type scheme: SignatureScheme
        :param mnemonics: string of phrases separated by spaces, defaults to None
        :type mnemonics: str, optional
        :param derivation_path: The derivation path for key, specific to Signature scheme,
            defaults to root path of scheme
        :type derivation_path: str, optional
        :raises NotImplementedError: When providing unregognized scheme
        :return: The input or generated mnemonic string and the new keypair associated SuiAddress
        :rtype: tuple[str, SuiAddress]
        """
        logger.debug(f"Creating new keypair for type {scheme.as_str}")
        match scheme:
            case SignatureScheme.ED25519 | SignatureScheme.SECP256K1 | SignatureScheme.SECP256R1:
                mnem, keypair, address = create_new_address(
                    scheme, mnemonics, derivation_path
                )
                self._addresses[address.address] = address
                self._address_keypair[address.address] = keypair
                if self._current_env != EMPEHMERAL_USER:
                    self._write_keypair(keypair)
                else:
                    if not self.active_address:
                        self._active_address = address
                return mnem, address
            case _:
                raise NotImplementedError(
                    f"{scheme}: Not recognized as valid keypair scheme."
                )

    @versionadded(version="0.24.0", reason="Added to recover keypairs")
    def recover_keypair_and_address(
        self,
        scheme: SignatureScheme,
        mnemonics: str,
        derivation_path: str,
        install: bool = False,
    ) -> tuple[str, SuiAddress]:
        """recover_keypair_and_address Recover a keypair from mnemonic string.

        :param scheme: Identifies whether new key is ed25519, secp256k1 or secp256r1
        :type scheme: SignatureScheme
        :param mnemonics: string of phrases separated by spaces
        :type mnemonics: str
        :param derivation_path: The derivation path for key, specific to Signature scheme
        :type derivation_path: str
        :param install: Flag indicating to write back to client.yaml, defaults to False
        :type install: bool, optional
        :raises NotImplementedError: When providing unregognized scheme
        :raises ValueError: If recovered keypair/address already exists
        :return: The input mnemonic string and the new keypair associated SuiAddress
        :rtype: tuple[str, SuiAddress]
        """
        logger.debug(f"Recovering keypair of type {scheme.as_str}")
        match scheme:
            case SignatureScheme.ED25519 | SignatureScheme.SECP256K1 | SignatureScheme.SECP256R1:
                mnem, keypair, address = recover_key_and_address(
                    scheme, mnemonics, derivation_path
                )
                if address.address in self._addresses:
                    raise ValueError(
                        f"Address {address.address} already exists."
                    )
                else:
                    self._addresses[address.address] = address
                    self._address_keypair[address.address] = keypair
                    if install:
                        self._write_keypair(keypair)
                    return mnem, address
            case _:
                raise NotImplementedError(
                    f"{scheme}: Not recognized as valid keypair scheme."
                )

    @classmethod
    @deprecated(version="0.29.0", reason="Use _new_parse_config")
    def _parse_config(
        cls, fpath: Path, config_file: TextIOWrapper
    ) -> tuple[str, str, str, str, str]:
        """Open configuration file and generalize for ingestion."""
        kfpath = fpath.parent
        sui_config = yaml.safe_load(config_file)
        active_address = (
            sui_config["active_address"]
            if "active_address" in sui_config
            else None
        )
        keystore_file = (
            Path(sui_config["keystore"]["File"])
            if "keystore" in sui_config
            else None
        )
        # active_env is new (0.15.0) and identifies the alias in use in the 'envs' map list
        active_env = (
            sui_config["active_env"] if "active_env" in sui_config else None
        )
        if not active_address or not keystore_file or not active_env:
            raise SuiConfigFileError(
                f"{fpath} is not a valid SUI configuration file."
            )
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
        return (
            str(fpath),
            active_env,
            active_address,
            keystore_file,
            current_url,
        )

    @classmethod
    @versionchanged(version="0.29.0", reason="Now returns ws url.")
    def _new_parse_config(cls, sui_config: str) -> tuple[str, str, str, str]:
        """New Config Parser."""
        active_address = (
            sui_config["active_address"]
            if "active_address" in sui_config
            else None
        )
        keystore_file = (
            Path(sui_config["keystore"]["File"])
            if "keystore" in sui_config
            else None
        )
        # active_env is new (0.15.0) and identifies the alias in use in the 'envs' map list
        active_env = (
            sui_config["active_env"] if "active_env" in sui_config else None
        )
        if not active_address or not keystore_file or not active_env:
            raise SuiConfigFileError("Not a valid SUI configuration file.")
        current_url = None
        socket_url = None
        if "envs" in sui_config:
            for envmap in sui_config["envs"]:
                if active_env == envmap["alias"]:
                    current_url = envmap["rpc"]
                    if "ws" in envmap:
                        socket_url = envmap["ws"]
                    break
        else:
            raise SuiConfigFileError("'envs' not found in configuration file.")
        return active_address, current_url, socket_url, active_env

    @classmethod
    @versionadded(version="0.16.1", reason="More flexible configuration.")
    def _create_config(
        cls, expanded_path: Path, expanded_binary: Path
    ) -> "SuiConfig":
        """."""
        client_yaml = yaml.safe_load(expanded_path.read_text(encoding="utf8"))
        config = super(ClientConfiguration, cls).__new__(cls)
        config.__init__(str(expanded_path), client_yaml["keystore"]["File"])
        _set_env_vars(expanded_path, expanded_binary)
        config._initiate(*cls._new_parse_config(client_yaml))
        return config

    @classmethod
    @versionadded(
        version="0.16.1", reason="New loading of default configuration."
    )
    def default_config(cls) -> "SuiConfig":
        """."""
        logger.debug("Initializing default configuration from ~/.sui")
        expanded_path = Path(os.path.expanduser(DEFAULT_DEVNET_PATH_STRING))
        if expanded_path.exists():
            return cls._create_config(
                expanded_path,
                Path(os.path.expanduser(DEFAULT_SUI_BINARY_PATH)),
            )
        raise SuiFileNotFound(f"{expanded_path} not found.")

    @classmethod
    @versionadded(
        version="0.16.1",
        reason="Supporting more flexible non-default configurations",
    )
    def sui_base_config(cls) -> "SuiConfig":
        """."""
        logger.debug("Initializing suibase local node configuration.")
        return cls._create_config(*sui_base_get_config())

    @classmethod
    @versionadded(version="0.25.0", reason="Removes reliance on client.yaml")
    @versionchanged(
        version="0.26.0",
        reason="Relax initialization requirements of prv_keys",
    )
    def user_config(
        cls,
        *,
        rpc_url: str,
        prv_keys: Optional[list[str]] = None,
        ws_url: Optional[str] = None,
    ) -> "SuiConfig":
        """user_config Load a user defined configuraiton.

        Note: New address/keypairs added in this session are not persisted.
        Note: publish is not available in this option.

        :param rpc_url: he RPC url for RPC API interaction
        :type rpc_url: str
        :param prv_keys: Optional list of keystrings (Sui format), defaults to None
        :type prv_keys: Optional[list[str]], optional
        :param ws_url: Optional wss url for subscriptions, defaults to None
        :type ws_url: Optional[str], optional
        :return: An instance of SuiConfig that can be used to initialize a SuiClient
        :rtype: SuiConfig
        """
        assert rpc_url
        logger.debug(f"Initializing user configuration for rpc url: {rpc_url}")
        prv_keys = prv_keys or []
        config = super(ClientConfiguration, cls).__new__(cls)
        config.__init__(EMPEHMERAL_PATH, EMPEHMERAL_PATH)
        _set_env_vars(EMPEHMERAL_PATH, EMPEHMERAL_PATH)
        config._current_env = EMPEHMERAL_USER
        config._current_url = rpc_url
        config._current_env = EMPEHMERAL_USER
        if rpc_url == DEVNET_SUI_URL:
            config._faucet_url = DEVNET_FAUCET_URL
            config._socket_url = ws_url or DEVNET_SOCKET_URL
        elif rpc_url == TESTNET_SUI_URL:
            config._faucet_url = TESTNET_FAUCET_URL
            config._socket_url = ws_url or TESTNET_SOCKET_URL
        elif rpc_url == LOCALNET_SUI_URL:
            config._faucet_url = LOCALNET_FAUCET_URL
            config._socket_url = ws_url or LOCALNET_SOCKET_URL
        else:
            config._faucet_url = EMPEHMERAL_USER
            config._socket_url = ws_url or EMPEHMERAL_USER
        config._local_running = False
        if prv_keys:
            (
                config._keypairs,
                config._addresses,
                config._address_keypair,
            ) = emphemeral_keys_and_addresses(prv_keys)
            config._active_address = SuiAddress(config.addresses[0])
        else:
            config._active_address = None
        return config

    @property
    def rpc_url(self) -> str:
        """Return the current URL."""
        return self._current_url

    @property
    def local_config(self) -> bool:
        """Return the mode we are running in."""
        return self._local_running

    @property
    def faucet_url(self) -> str:
        """Return faucet url."""
        return self._faucet_url

    @property
    def socket_url(self) -> str:
        """Return socket url."""
        return self._socket_url

    @property
    def active_address(self) -> SuiAddress:
        """Return the current address."""
        return self._active_address

    @property
    def environment(self) -> str:
        """environment Return the current environment of config in use.

        :return: The environment name
        :rtype: str
        """
        return self._current_env

    @property
    def keystore_file(self) -> str:
        """Return the fully qualified keystore path."""
        return self._current_keystore_file

    def set_active_address(self, address: SuiAddress) -> SuiAddress:
        """Change the active address to address."""
        stale_addy = self._active_address
        self._active_address = address
        return stale_addy
