#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Pysui Configuration."""


import platform
from pathlib import Path
from typing import Optional

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
    def active_address(self) -> str:
        """Returns the active groups active address."""
        return self._model.active_group.using_address

    @property
    def active_address_alias(self) -> str:
        """Returns the active groups active address."""
        return self._model.active_group.active_alias

    @property
    def active_env(self) -> str:
        """Returns the active groups active profile name."""
        return self._model.active_group.using_profile

    @property
    def url(self) -> str:
        """Returns the active groups active profile url."""
        return self._model.active_group.active_profile.url

    @property
    def faucet_url(self) -> str:
        """Returns the active groups active profile faucet url."""
        return self._model.active_group.active_profile.faucet_urls

    @property
    def faucet_status_url(self) -> str:
        """Returns the active groups active profile faucet status url."""
        return self._model.active_group.active_profile.faucet_status_url

    @property
    def config_path(self) -> str:
        """Return configuration breadcrump path."""
        _group = self._model.active_group
        return f"{_group.group_name}.{_group.active_profile.profile_name}"

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
            _group = self._model.active_group

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