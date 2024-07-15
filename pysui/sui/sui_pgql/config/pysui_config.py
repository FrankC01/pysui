#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Pysui Configuration."""


import platform
from pathlib import Path
from typing import Optional

import pysui.sui.sui_crypto as crypto
import pysui.sui.sui_utils as utils

from pysui.abstracts.client_keypair import SignatureScheme
from pysui.sui.sui_constants import SUI_MAX_ALIAS_LEN, SUI_MIN_ALIAS_LEN

from pysui.sui.sui_pgql.config.confgroup import ProfileGroup
from pysui.sui.sui_pgql.config.confmodel import PysuiConfigModel


class PysuiConfiguration:
    """pysui configuration class."""

    SUI_JSON_RPC_GROUP: str = "sui_json_config"
    SUI_GQL_RPC_GROUP: str = "sui_gql_config"

    def __init__(
        self,
        *,
        from_cfg_path: str = None,
        group_name: Optional[str] = "sui_gql_config",
        profile_name: Optional[str] = None,
        address: Optional[str] = None,
        alias: Optional[str] = None,
        persist: Optional[bool] = False,
    ):
        """Initialize configuration."""
        # Get the base configuration folder and profile file
        self._config_root = Path(from_cfg_path or "~/.pysui").expanduser()
        # _ecfgdir = Path(self._config_root).expanduser()
        self._config_file = self._config_root / "PysuiConfig.json"
        # If the primmary path doesn't exist create
        if not self._config_root.exists():
            self._config_root.mkdir()
        # If above, then true else determine
        if not self._config_file.exists():
            # Populate the default profile configuration and write
            self._model: PysuiConfigModel = PysuiConfigModel()
            self._config_file.write_text(self._model.to_json(indent=2))
        else:
            self._model: PysuiConfigModel = PysuiConfigModel.from_json(
                self._config_file.read_text(encoding="utf8")
            )
        # Determine if sui binaries installed
        if platform.system() == "Windows":
            _bcfg = Path("~/.cargo/bin/sui.exe").expanduser()
        else:
            _bcfg = Path("~/.cargo/bin/sui").expanduser()
        # Initialize from sui config if found
        self.refresh_legacy(replace=False)
        # Set if not exist, don't overwrite
        self.model.add_group(
            group=ProfileGroup("user", "", "", [], [], [], []), make_active=False
        )
        if self._model.initialize_gql_rpc(
            sui_binary=_bcfg,
            gql_rpc_group_name=self.SUI_GQL_RPC_GROUP,
            json_rpc_group_name=self.SUI_JSON_RPC_GROUP,
        ):
            self._write_model()
        # Make active as per arguments
        self.make_active(
            group_name=group_name,
            profile_name=profile_name,
            address=address,
            alias=alias,
            persist=persist,
        )

    def _write_model(self):
        """Writes out the configuration model."""
        self._config_file.write_text(self.to_json(indent=2))

    def to_json(self, *_cmds, **kwargs) -> str:
        """."""
        return self._model.to_json(**kwargs)

    def refresh_legacy(self, *, replace: bool = True):
        """Refresh from legacy Sui JSON RPC client yaml."""
        # Determine if sui configuration installed
        _scfg = Path("~/.sui/sui_config").expanduser()
        if _scfg.exists():
            # If exists legacy group, remove it
            if self._model.has_group(group_name=self.SUI_JSON_RPC_GROUP):
                if replace:
                    self._model.remove_group(group_name=self.SUI_JSON_RPC_GROUP)
                else:
                    return
            # Determine if sui binaries installed
            if platform.system() == "Windows":
                _bcfg = Path("~/.cargo/bin/sui.exe").expanduser()
            else:
                _bcfg = Path("~/.cargo/bin/sui").expanduser()
            _needs_write_json = self._model.initialize_json_rpc(
                sui_config=_scfg,
                sui_binary=_bcfg,
                json_rpc_group_name=self.SUI_JSON_RPC_GROUP,
            )
            if _needs_write_json:
                self._write_model()

    @property
    def model(self) -> PysuiConfigModel:
        """."""
        return self._model

    @property
    def active_group(self) -> ProfileGroup:
        """Return the active group."""
        return self._model.active_group

    @property
    def active_address(self) -> str:
        """Returns the active groups active address."""
        return self.active_group.using_address

    @property
    def active_address_alias(self) -> str:
        """Returns the active groups active address."""
        return self.active_group.active_alias

    @property
    def active_env(self) -> str:
        """Returns the active groups active profile name."""
        return self.active_group.using_profile

    @property
    def url(self) -> str:
        """Returns the active groups active profile url."""
        return self.active_group.active_profile.url

    @property
    def faucet_url(self) -> str:
        """Returns the active groups active profile faucet url."""
        return self.active_group.active_profile.faucet_urls

    @property
    def faucet_status_url(self) -> str:
        """Returns the active groups active profile faucet status url."""
        return self.active_group.active_profile.faucet_status_url

    @property
    def config_path(self) -> str:
        """Return configuration breadcrump path."""
        _group = self.active_group
        return f"{_group.group_name}.{_group.active_profile.profile_name}"

    def address_for_alias(self, *, alias_name: str) -> str:
        """Return the address for the alias name in current group."""
        return self.active_group.address_for_alias(alias=alias_name)

    def alias_for_address(self, *, address: str) -> str:
        """Return the alias for the address in current group."""
        return self.active_group.alias_for_address(address=address)

    def rename_alias(
        self,
        *,
        existing_alias: str,
        new_alias: str,
        in_group: Optional[str] = None,
        persist: Optional[bool] = False,
    ) -> str:
        """Rename an alias in a group, default to active_group."""
        _group = self.active_group
        if in_group and in_group != _group.group_name:
            _group = self._model.get_group(group_name=in_group)

        _res = _group.replace_alias_name(from_alias=existing_alias, to_alias=new_alias)
        if _res and persist:
            self._write_model()

    def make_active(
        self,
        *,
        group_name: Optional[str] = None,
        profile_name: Optional[str] = None,
        address: Optional[str] = None,
        alias: Optional[str] = None,
        persist: Optional[bool] = True,
    ):
        """Activate specific aspects of configuration."""
        # Track changes for persist
        _changes: bool = False

        # If group specified and it's not the active
        if group_name and self._model.group_active != group_name:
            # If  it exists and is not already the active group then set it
            if _group := self._model.has_group(group_name=group_name):
                self._model.active_group = group_name
                _changes = True
            else:
                raise ValueError(f"{group_name} does not exist")
        else:
            _group = self.active_group

        # Change profile, checks if it exists
        if profile_name and _group.using_profile != profile_name:
            _group.active_profile = profile_name
            _changes = True

        # Change activte address, checks if exists
        if address and _group.active_address != address:
            _group.active_address = address
            _changes = True
        # Else try alias
        elif alias and _group.active_alias != alias:
            _group.active_alias = alias
            _changes = True

        if _changes and persist:
            self._write_model()

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
            parts = list(
                utils.partition(
                    crypto.gen_mnemonic_phrase(word_counts).split(" "),
                    int(word_counts / 2),
                )
            )
            alias_names = [k + "-" + v for k, v in zip(*parts)]

            # alias_names = self._alias_gen_batch(word_counts=word_counts)
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
            if not (SUI_MIN_ALIAS_LEN <= len(alias) <= SUI_MAX_ALIAS_LEN):
                raise ValueError(
                    f"Invalid alias string length, must be betwee {SUI_MIN_ALIAS_LEN} and {SUI_MAX_ALIAS_LEN} characters."
                )
        return alias

    def new_keypair(
        self,
        *,
        of_keytype: SignatureScheme,
        in_group: Optional[str] = None,
        word_counts: Optional[int] = 12,
        derivation_path: Optional[str] = None,
        make_active: Optional[bool] = False,
        alias: Optional[str] = None,
        persist: Optional[bool] = True,
    ) -> tuple[str, str]:
        """Creates a new keypair returning generated passphrase and associated address."""
        # Resolve group
        _group = self.active_group
        if in_group and in_group != _group.group_name:
            _group = self._model.get_group(group_name=in_group)

        match of_keytype:
            case (
                SignatureScheme.ED25519
                | SignatureScheme.SECP256K1
                | SignatureScheme.SECP256R1
            ):
                # First, early check alias given or create new one
                _aliases = [x.alias for x in _group.alias_list]
                alias = self._alias_check_or_gen(
                    aliases=_aliases, alias=alias, word_counts=word_counts
                )
                # Generate the new key and address
                mnem, keypair = crypto.create_new_keypair(
                    scheme=of_keytype,
                    word_counts=word_counts,
                    derv_path=derivation_path,
                )
                new_addy = _group.add_keypair_and_parts(
                    new_alias=alias, new_keypair=keypair, make_active=make_active
                )
                if make_active and _group.group_name != self.active_group.group_name:
                    self._model.active_group = _group.group_name
                if persist:
                    self._write_model()
                return mnem, new_addy
            case _:
                raise NotImplementedError(
                    f"{of_keytype}: Not recognized as valid keypair scheme."
                )
