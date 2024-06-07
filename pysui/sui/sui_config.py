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
import logging
import base64
import re
from pathlib import Path
import json
from typing import Optional, Union
import yaml
from deprecated.sphinx import versionadded, versionchanged, deprecated
from pysui.abstracts import ClientConfiguration, SignatureScheme, CrefType
from pysui.sui.sui_constants import (
    DEFAULT_SUI_ALIAS_CONFIG,
    DEFAULT_SUI_CLIENT_CONFIG,
    SUI_MIN_ALIAS_LEN,
    SUI_MAX_ALIAS_LEN,
    DEFAULT_ALIAS_PATH_STRING,
    EMPEHMERAL_PATH,
    EMPEHMERAL_USER,
    LOCALNET_PROXY_SUI_URL,
    LOCALNET_SUI_URL,
    MAINNET_SUI_URL,
    MAINNET_SOCKET_URL,
    PYSUI_EXEC_ENV,
    PYSUI_CLIENT_CONFIG_ENV,
    DEFAULT_SUI_BINARY_PATH,
    DEFAULT_DEVNET_PATH_STRING,
    DEVNET_SUI_URL,
    DEVNET_FAUCET_URLV1,
    DEVNET_SOCKET_URL,
    LOCALNET_FAUCET_URL,
    LOCALNET_SOCKET_URL,
    TESTNET_FAUCET_URLV1,
    TESTNET_SOCKET_URL,
    TESTNET_SUI_URL,
)
from pysui.sui.sui_crypto import (
    SuiAddress,
    as_keystrings,
    create_new_address,
    emphemeral_keys_and_addresses,
    keypair_from_keystring,
    load_keys_and_addresses,
    recover_key_and_address,
    gen_mnemonic_phrase,
)
from pysui.sui.sui_excepts import (
    SuiConfigFileError,
    SuiFileNotFound,
)
from pysui.sui.sui_utils import partition, sui_base_get_config

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

    __ALIAS_PATTERN: re.Pattern = re.compile(r"^[a-zA-Z][a-zA-Z0-9._-]*$")

    @versionchanged(version="0.29.0", reason="Now accepts ws url.")
    @versionchanged(version="0.53.0", reason="Added GraphQL url property.")
    def _initiate(
        self,
        active_address: str,
        rpc_url: str,
        socket_url: str,
        environment: str,
        gql_url: Optional[str] = None,
    ) -> None:
        """."""
        self._active_address = SuiAddress(active_address)
        self._current_url = rpc_url
        self._current_env = environment
        self._local_running = False
        self._faucet_url = None
        self._socket_url = None
        self._current_graphql_url = gql_url
        match self._current_env:
            case "devnet":
                self._faucet_url = DEVNET_FAUCET_URLV1
                self._socket_url = socket_url if socket_url else DEVNET_SOCKET_URL
            case "testnet":
                self._faucet_url = TESTNET_FAUCET_URLV1
                self._socket_url = socket_url if socket_url else TESTNET_SOCKET_URL
            case "localnet" | "localnet_proxy":
                self._faucet_url = LOCALNET_FAUCET_URL
                self._socket_url = socket_url if socket_url else LOCALNET_SOCKET_URL
                self._local_running = True
            case "mainnet":
                self._faucet_url = None
                self._socket_url = socket_url if socket_url else MAINNET_SOCKET_URL
            case _:
                self._socket_url = socket_url
        self._cref_matrix = load_keys_and_addresses(self.keystore_file)
        # Setup aliases
        if self.alias_file:
            try:
                with open(self.alias_file, encoding="utf8") as keyfile:
                    self._alias_assocation(json.load(keyfile))
            except FileNotFoundError:
                self._alias_assocation({})

    @versionadded(version="0.41.0", reason="Support aliases.")
    def _write_aliases(self):
        """Write alias file."""
        if self._current_env != EMPEHMERAL_USER and self._has_aliases:
            alias_filepath = self.alias_file
            logger.debug(f"Writing aliases to {alias_filepath}")
            with open(alias_filepath, "w", encoding="utf8") as alias_store:
                alias_store.write(json.dumps(self.aliases_encode(), indent=2))

    @versionchanged(version="0.41.0", reason="Support aliases.")
    def _write_keypairs(self, file_path: Optional[str] = None) -> None:
        """Update keystore and alias files."""
        keys_filepath = file_path if file_path else self.keystore_file
        logger.debug(f"Updating keystore {keys_filepath}")
        if os.path.exists(keys_filepath):
            with open(keys_filepath, "w", encoding="utf8") as keystore:
                keystore.write(json.dumps(self.keystrings, indent=2))
        else:
            raise SuiFileNotFound((keys_filepath))
        self._write_aliases()

    @versionadded(version="0.41.0", reason="Support aliases.")
    def _alias_gen_batch(self, *, word_counts: int) -> list[str]:
        """_alias_gen_batch Generates a batch of alias name pairs

        :param word_counts: Words count used for mnemonic phrase
        :type word_counts: int
        :return: A list of alias-name pairs
        :rtype: list[str]
        """
        parts = list(
            partition(gen_mnemonic_phrase(word_counts).split(" "), int(word_counts / 2))
        )
        return [k + "-" + v for k, v in zip(*parts)]

    @versionadded(version="0.41.0", reason="Support aliases.")
    def _alias_check_or_gen(
        self,
        *,
        aliases: Optional[list[str]] = None,
        word_counts: Optional[int] = 12,
        alias: Optional[str] = None,
        current_iter: Optional[int] = 0,
    ) -> str:
        """_alias_check_or_gen If alias is provided, checks if unique otherwise creates one or more.

        :param aliases: List of existing aliases, defaults to None
        :type aliases: list[str], optional
        :param word_counts: Words count used for mnemonic phrase, defaults to 12
        :type word_counts: Optional[int], optional
        :param alias: An inbound alias, defaults to None
        :type alias: Optional[str], optional
        :param current_iter: Internal recursion count, defaults to 0
        :type current_iter: Optional[int], optional
        :return: An aliases
        :rtype: str
        """
        if not alias:
            alias_names = self._alias_gen_batch(word_counts=word_counts)
            # Find a unique part if just_one
            if not aliases:
                alias = alias_names[0]
            else:
                for alias_name in alias_names:
                    if alias_name not in aliases:
                        # Found one
                        alias = alias_name
                        break
            # If all match (unlikely), try unless threshold
            if not alias:
                if current_iter > 2:
                    raise ValueError("Unable to find unique alias")
                else:
                    alias = self._alias_check_or_gen(
                        aliases=aliases,
                        word_counts=word_counts,
                        current_iter=current_iter + 1,
                    )
        else:
            if alias in aliases:
                raise ValueError(f"Alias {alias} already exists.")
            if SUI_MIN_ALIAS_LEN <= len(alias) <= SUI_MAX_ALIAS_LEN:
                raise ValueError(
                    f"Invalid alias string length, must be betwee {SUI_MIN_ALIAS_LEN} and {SUI_MAX_ALIAS_LEN} characters."
                )
        return alias

    def rename_alias(self, *, old_alias: str, new_alias: str) -> None:
        """rename_alias Renames existing alias.

        :param old_alias: Existing alias name
        :type old_alias: str
        :param new_alias: Replacement name
        :type new_alias: str
        :raises ValueError: Invalid arguments
        :return: None
        :rtype: NoneType
        """
        if (
            old_alias
            and isinstance(old_alias, str)
            and new_alias
            and isinstance(new_alias, str)
            and SUI_MIN_ALIAS_LEN <= len(new_alias) <= SUI_MAX_ALIAS_LEN
        ):
            re_alias = self.__ALIAS_PATTERN.findall(new_alias)
            if not re_alias or len(re_alias[0]) != len(new_alias):
                raise ValueError(f"Invalid new_alias {new_alias} for alias")
            self._replace_alias_key(
                self._cref_result_for(old_alias, CrefType.ALIAS, CrefType.INDEX),
                new_alias,
            )
            self._write_aliases()
        else:
            raise ValueError("Invalid arguments")

    @versionchanged(version="0.33.0", reason="Return mnemonics to caller.")
    @versionchanged(version="0.41.0", reason="Support aliases.")
    @versionchanged(version="0.41.0", reason="Added make_active flag.")
    @versionchanged(version="0.42.0", reason="Changed to require keyword arguments.")
    def create_new_keypair_and_address(
        self,
        *,
        scheme: SignatureScheme,
        word_counts: Optional[int] = 12,
        derivation_path: Optional[str] = None,
        make_active: Optional[bool] = False,
        alias: Optional[str] = None,
    ) -> tuple[str, SuiAddress]:
        """create_new_keypair_and_address Create a new keypair and address identifier and writes to client.yaml.

        :param scheme: Identifies whether new key is ed25519, secp256k1 or secp256r1
        :type scheme: SignatureScheme
        :param word_counts: count of words to generate mnemonic phrase, defaults to 12
        :type word_counts: int, optional
        :param derivation_path: The derivation path for key, specific to Signature scheme,
            defaults to root path of scheme
        :type derivation_path: str, optional
        :param make_active: Flag to make address from created KeyPair the 'active_address', defaults to False
        :type make_active: bool, optional
        :param alias: Associates alias string to newly created kp and address,defaults to None
            If not provide, alias will be generated
        :type alias: Optional[str], optional
        :raises NotImplementedError: When providing unregognized scheme
        :return: The input or generated mnemonic string and the new keypair associated SuiAddress
        :rtype: tuple[str, SuiAddress]
        """
        logger.debug(
            f"Creating new keypair for type {scheme.as_str} with alias {alias}"
        )
        match scheme:
            case (
                SignatureScheme.ED25519
                | SignatureScheme.SECP256K1
                | SignatureScheme.SECP256R1
            ):
                # First, early check alias given or create new one
                alias = self._alias_check_or_gen(
                    aliases=self.aliases, alias=alias, word_counts=word_counts
                )
                # Generate the new key and address
                mnem, keypair, address = create_new_address(
                    scheme, word_counts, derivation_path
                )
                # Valid Sui base64 keystring
                kpstr = keypair.serialize()
                # Valid type encoded base64 Sui public key
                puks = base64.b64encode(keypair.public_key.scheme_and_key()).decode()
                self._cref_matrix.append(
                    [
                        # Alias to public key string
                        {alias: puks},
                        # Keypair string to keypair
                        {kpstr: keypair},
                        # Public key string to keypair string
                        {puks: kpstr},
                        # Address string to address
                        {address.address: address},
                    ]
                )
                if self._current_env != EMPEHMERAL_USER:
                    logger.debug(f"Writing new keypair to {self.keystore_file}")
                    self._write_keypairs()
                if make_active or not self.active_address:
                    self.set_active_address(address)
                return mnem, address
            case _:
                raise NotImplementedError(
                    f"{scheme}: Not recognized as valid keypair scheme."
                )

    @versionadded(version="0.24.0", reason="Added to recover keypairs")
    @versionchanged(
        version="0.33.0",
        reason="If install is True, checks if not in 'user_config' setup before writing",
    )
    @versionchanged(version="0.41.0", reason="Support aliases.")
    @versionchanged(version="0.41.0", reason="Added make_active flag.")
    def recover_keypair_and_address(
        self,
        scheme: SignatureScheme,
        mnemonics: Union[str, list[str]],
        derivation_path: str,
        install: bool = False,
        make_active: Optional[bool] = False,
        alias: Optional[str] = None,
    ) -> tuple[str, SuiAddress]:
        """recover_keypair_and_address Recover a keypair from mnemonic string.

        :param scheme: Identifies whether new key is ed25519, secp256k1 or secp256r1
        :type scheme: SignatureScheme
        :param mnemonics: string of phrases separated by spaces
        :type mnemonics: str
        :param derivation_path: The derivation path for key, specific to Signature scheme
        :type derivation_path: str
        :param install: Flag indicating to write back to sui.keystore, defaults to False
            This flag is ignored if config was initiated through 'user_config()'
        :type install: bool, optional
        :param make_active: Flag to make address from created KeyPair the 'active_address', defaults to False
        :type make_active: bool, optional
        :param alias: Associates alias string to newly created kp and address,defaults to None
            If not provide, alias will be generated
        :type alias: Optional[str], optional
        :raises NotImplementedError: When providing unregognized scheme
        :return: The input mnemonic string and the new keypair associated SuiAddress
        :rtype: tuple[str, SuiAddress]
        """
        logger.debug(f"Recovering keypair of type {scheme.as_str} with alias {alias}")
        match scheme:
            case (
                SignatureScheme.ED25519
                | SignatureScheme.SECP256K1
                | SignatureScheme.SECP256R1
            ):
                alias = self._alias_check_or_gen(aliases=self.aliases, alias=alias)
                mnem, keypair, address = recover_key_and_address(
                    scheme, mnemonics, derivation_path
                )
                if address.address in self.addresses:
                    # already exists, nothing more to do
                    return mnem, address
                # Valid Sui base64 keystring
                kpstr = keypair.serialize()
                # Valid type encoded base64 Sui public key
                puks = base64.b64encode(keypair.public_key.scheme_and_key()).decode()
                self._cref_matrix.append(
                    [
                        # Alias to public key string
                        {alias: puks},
                        # Keypair string to keypair
                        {kpstr: keypair},
                        # Public key string to keypair string
                        {puks: kpstr},
                        # Address string to address
                        {address.address: address},
                    ]
                )
                if install and self._current_env != EMPEHMERAL_USER:
                    logger.debug(f"Writing new keypair to {self.keystore_file}")
                    self._write_keypairs()
                if make_active or not self.active_address:
                    self.set_active_address(address)
                return mnem, address
            case _:
                raise NotImplementedError(
                    f"{scheme}: Not recognized as valid keypair scheme."
                )

    @versionadded(
        version="0.33.0",
        reason="Allow import from valid Sui keystring or Wallet key export",
    )
    @versionchanged(version="0.41.0", reason="Support aliases.")
    def add_keypair_from_keystring(
        self,
        *,
        keystring: Union[str, dict],
        install: bool = False,
        make_active: Optional[bool] = False,
        alias: Optional[str] = False,
    ) -> SuiAddress:
        """add_keypair_from_keystring Adds a KeyPair from Sui keystring.

        :param keystring: Either a valid Sui keystring (flag | private 32 byte seed) in base64 form
            or a dictionary for conversion from wallet::

                {
                    'wallet_key':'0x.....',                 # Wallet exported key hex string
                    'key_scheme': SignatureScheme.ED25519   # Must align with wallet_key type
                }

        :type keystring: Union[str, dict]
        :param install: Flag indicating to write back to sui.keystore, defaults to False
            This flag is ignored if config was initiated through 'user_config()'
        :type install: bool, optional
        :param make_active: Flag to make address from created KeyPair the 'active_address', defaults to False
        :type make_active: bool, optional
        :param alias: Associates alias string to newly created kp and address,defaults to None
            If not provide, alias will be generated
        :type alias: Optional[str], optional
        :raises ValueError: If the derived address is already registered in SuiConfig
        :return: The derived SuiAddress
        :rtype: SuiAddress
        """

        alias = self._alias_check_or_gen(aliases=self.aliases, alias=alias)

        keystring = as_keystrings([keystring])[0]
        to_kp = keypair_from_keystring(keystring)
        to_addy = SuiAddress.from_bytes(to_kp.to_bytes())
        if to_addy.address in self.addresses:
            raise ValueError(f"Address {to_addy.address} already exists.")
        # Valid Sui base64 keystring
        kpstr = to_kp.serialize()
        # Valid type encoded base64 Sui public key
        puks = base64.b64encode(to_kp.public_key.scheme_and_key()).decode()
        self._cref_matrix.append(
            [
                # Alias to public key string
                {alias: puks},
                # Keypair string to keypair
                {kpstr: to_kp},
                # Public key string to keypair string
                {puks: kpstr},
                # Address string to address
                {to_addy.address: to_addy},
            ]
        )
        if install and self._current_env != EMPEHMERAL_USER:
            logger.debug(f"Writing new keypair to {self.keystore_file}")
            self._write_keypairs()
        if make_active or not self.active_address:
            self.set_active_address(to_addy)
        return to_addy

    @classmethod
    @versionchanged(version="0.29.0", reason="Now returns ws url.")
    def _new_parse_config(cls, sui_config: str) -> tuple[str, str, str, str]:
        """New Config Parser."""
        active_address = (
            sui_config["active_address"] if "active_address" in sui_config else None
        )
        keystore_file = (
            Path(sui_config["keystore"]["File"]) if "keystore" in sui_config else None
        )
        # active_env is new (0.15.0) and identifies the alias in use in the 'envs' map list
        active_env = sui_config["active_env"] if "active_env" in sui_config else None
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
    @versionchanged(version="0.41.0", reason="Sui aliases configuration feature added")
    def _create_config(
        cls, expanded_path: Path, expanded_binary: Path, expanded_alias: Path
    ) -> "SuiConfig":
        """."""
        client_yaml = yaml.safe_load(expanded_path.read_text(encoding="utf8"))
        config = super(ClientConfiguration, cls).__new__(cls)
        # alias_file = (
        #     str(expanded_alias) if expanded_alias and expanded_alias.exists() else None
        # )
        config.__init__(
            str(expanded_path), client_yaml["keystore"]["File"], str(expanded_alias)
        )
        _set_env_vars(expanded_path, expanded_binary)
        config._initiate(*cls._new_parse_config(client_yaml))
        return config

    @classmethod
    @versionadded(version="0.16.1", reason="New loading of default configuration.")
    @versionchanged(version="0.41.0", reason="Sui aliases configuration feature added")
    def default_config(cls) -> "SuiConfig":
        """default_config Loads the configuration created by use of sui binaries `sui client`

        :raises SuiFileNotFound: If Sui configuration does not exist
        :return: Instantiated configuration ready for use
        :rtype: SuiConfig
        """
        logger.debug("Initializing default configuration from ~/.sui")
        expanded_path = Path(os.path.expanduser(DEFAULT_DEVNET_PATH_STRING))
        if expanded_path.exists():
            return cls._create_config(
                expanded_path,
                Path(os.path.expanduser(DEFAULT_SUI_BINARY_PATH)),
                Path(os.path.expanduser(DEFAULT_ALIAS_PATH_STRING)),
            )
        raise SuiFileNotFound(f"{expanded_path} not found.")

    @classmethod
    @versionadded(version="0.51.0", reason="New alternate configuration path loading.")
    def pysui_config(cls, cfg_path: str) -> "SuiConfig":
        """pysui_config Loads an alternate configuration from specified path.

        This behaves as a normal configuration where address and alias adds/changes are persisted

        :param cfg_path: path to folder holding alternate configuration
        :type cfg_path: str
        :raises SuiFileNotFound: If path is invalid
        :return: Instantiated configuration ready for use
        :rtype: SuiConfig
        """
        logger.debug(f"Initializing configuration from path {cfg_path}")
        expanded_path = Path(os.path.expanduser(cfg_path))
        if expanded_path.exists():
            alias_path = expanded_path / DEFAULT_SUI_ALIAS_CONFIG
            expanded_path = expanded_path / DEFAULT_SUI_CLIENT_CONFIG
            return cls._create_config(
                expanded_path,
                Path(os.path.expanduser(DEFAULT_SUI_BINARY_PATH)),
                alias_path,
            )
        raise SuiFileNotFound(f"{expanded_path} not found.")

    @classmethod
    @versionadded(
        version="0.16.1",
        reason="Supporting more flexible non-default configurations",
    )
    def sui_base_config(cls) -> "SuiConfig":
        """sui_base_config Loads the active configuration set by suibase

        :return: Instantiated configuration ready for use
        :rtype: SuiConfig
        """
        logger.debug("Initializing suibase local node configuration.")
        return cls._create_config(*sui_base_get_config())

    @classmethod
    @versionadded(version="0.25.0", reason="Removes reliance on client.yaml")
    @versionchanged(
        version="0.26.0",
        reason="Relax initialization requirements of prv_keys",
    )
    @versionchanged(
        version="0.33.0",
        reason="Add support for importing Wallet private keys",
    )
    @versionchanged(
        version="0.34.0",
        reason="Add support for suibase localnet proxy",
    )
    @versionchanged(
        version="0.57.0",
        reason="Add gql_url argument to support setting GraphQL RPC host URL",
    )
    def user_config(
        cls,
        *,
        rpc_url: str,
        prv_keys: Optional[list[Union[str, dict]]] = None,
        ws_url: Optional[str] = None,
        gql_url: Optional[str] = None,
    ) -> "SuiConfig":
        """user_config Load a user defined configuraiton.

        Note: New address/keypairs added in this session are not persisted.
        Note: publish is not available in this option.

        :param rpc_url: he RPC url for RPC API interaction
        :type rpc_url: str
        :param prv_keys: Optional list containing either
            valid Sui keystrings (flag | private 32 byte seed) in base64 form and/or
            valid Sui bech32 encoded keystrings 'suiprivkey1xyxy' and/or
            dictionaries for conversion from Wallet key exports::

                {
                    'wallet_key':'0x.....',                 # Wallet exported key hex string
                    'key_scheme': SignatureScheme.ED25519   # Must align with wallet_key type
                }

        :type prv_keys: Optional[list[Union[str, dict]]], optional
        :param ws_url: Optional wss url for subscriptions, defaults to None
        :type ws_url: Optional[str], optional
        :param gql_url: Optional GraphQL RPC url, defaults to None
        :type gql_url: Optional[str], optional
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
        config._current_graphql_url = gql_url
        config._current_env = EMPEHMERAL_USER
        if rpc_url == DEVNET_SUI_URL:
            config._faucet_url = DEVNET_FAUCET_URLV1
            config._socket_url = ws_url or DEVNET_SOCKET_URL
        elif rpc_url == TESTNET_SUI_URL:
            config._faucet_url = TESTNET_FAUCET_URLV1
            config._socket_url = ws_url or TESTNET_SOCKET_URL
        elif rpc_url == MAINNET_SUI_URL:
            config._faucet_url = EMPEHMERAL_PATH
            config._socket_url = ws_url or MAINNET_SOCKET_URL
        elif rpc_url == LOCALNET_SUI_URL or rpc_url == LOCALNET_PROXY_SUI_URL:
            config._faucet_url = LOCALNET_FAUCET_URL
            config._socket_url = ws_url or LOCALNET_SOCKET_URL
        else:
            config._faucet_url = EMPEHMERAL_USER
            config._socket_url = ws_url or EMPEHMERAL_USER
        config._local_running = False
        if prv_keys:
            config._cref_matrix = emphemeral_keys_and_addresses(prv_keys)
            if len(config.addresses):
                config._active_address = SuiAddress(config.addresses[0])
        else:
            config._active_address = None
        config._alias_assocation([])
        return config

    @property
    def rpc_url(self) -> str:
        """Return the current URL."""
        return self._current_url

    @property
    def graphql_url(self) -> str:
        """Return the GraphQL RPC URL."""
        return self._current_graphql_url

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

    def set_active_address(self, address: SuiAddress) -> SuiAddress:
        """Change the active address to address."""
        stale_addy = self._active_address
        self._active_address = address
        return stale_addy
