#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sui Configuration Model."""

import dataclasses
from typing import Optional, Union
from pathlib import Path
import dataclasses_json


import pysui.sui.sui_pgql.config.confgroup as prfgrp
from pysui.sui.sui_pgql.config.conflegacy import load_client_yaml

_GQL_DEFAULTS: dict = {
    "devnet_beta": "https://sui-devnet.mystenlabs.com/graphql/beta",
    "devnet": "https://sui-devnet.mystenlabs.com/graphql/stable",
    "testnet": "https://sui-testnet.mystenlabs.com/graphql",
    "mainnet": "https://sui-mainnet.mystenlabs.com/graphql",
}


@dataclasses.dataclass
class PysuiConfigModel(dataclasses_json.DataClassJsonMixin):
    """pysui configuration in memory model."""

    sui_binary: Optional[str] = dataclasses.field(default="")
    group_active: Optional[str] = dataclasses.field(default="")
    groups: Optional[list[prfgrp.ProfileGroup]] = dataclasses.field(
        default_factory=list
    )

    def _group_exists(self, *, group_name: str) -> Union[prfgrp.ProfileGroup, bool]:
        """Check if a group, by name, exists."""
        return next(
            filter(lambda grp: grp.group_name == group_name, self.groups), False
        )

    def has_group(self, *, group_name: str) -> bool:
        """Test for group existence."""
        return self._group_exists(group_name=group_name)

    def remove_group(self, *, group_name: str) -> None:
        """Remove a group from the group list."""
        _target_group = self.get_group(group_name=group_name)
        self.groups.remove(_target_group)
        # Adjust active group
        if self.group_active == _target_group.group_name:
            if self.groups:
                self.group_active = self.groups[0].group_name

    def get_group(self, *, group_name: str) -> prfgrp.ProfileGroup:
        """Get a group or throw exception if doesn't exist."""
        _res = self._group_exists(group_name=group_name)
        if not _res:
            raise ValueError(f"{group_name} does not exist.")
        return _res

    @property
    def active_group(self) -> prfgrp.ProfileGroup:
        """Returns the active group."""
        _res = self._group_exists(group_name=self.group_active)
        if _res:
            return _res
        raise ValueError("No active group set")

    @active_group.setter
    def active_group(self, group_str: str) -> prfgrp.ProfileGroup:
        """Sets the active group."""
        _res = self._group_exists(group_name=group_str)
        if _res:
            self.group_active = group_str
            return _res
        raise ValueError(f"{group_str} does not exist")

    @property
    def active_address(self) -> str:
        """Returns the active address from the active group."""
        return self.active_group.using_address

    def initialize_json_rpc(
        self,
        *,
        sui_config: Path,
        sui_binary: Path,
        json_rpc_group_name: str,
    ) -> bool:
        """Initialize group from sui configuration client.yaml."""
        _updated = False

        if sui_binary.exists() and not self.sui_binary:
            self.sui_binary = f"{sui_binary}"
            _updated = True
        if sui_config.exists():
            # If group doesn't exist, create it
            if not self._group_exists(group_name=json_rpc_group_name):
                sui_group = load_client_yaml(sui_config, json_rpc_group_name)
                self.groups.append(sui_group)
                _updated = True
        return _updated

    def initialize_gql_rpc(
        self,
        *,
        sui_binary: Path,
        gql_rpc_group_name: str,
        json_rpc_group_name: str,
    ) -> bool:
        """Initialize GraphQL with defaults if not found."""
        _updated = False
        if sui_binary.exists() and not self.sui_binary:
            self.sui_binary = f"{sui_binary}"
            _updated = True

        # If group doesn't exist, create it
        _res = self._group_exists(group_name=gql_rpc_group_name)
        if not _res:
            # Get keys, aliases and addresses from rpc
            _suigrp = self._group_exists(group_name=json_rpc_group_name)
            if _suigrp:
                if _suigrp.using_profile in list(_GQL_DEFAULTS.keys()):
                    _using_profile = _suigrp.using_profile
                else:
                    _using_profile = "testnet"
                self.groups.append(
                    prfgrp.ProfileGroup(
                        gql_rpc_group_name,
                        _using_profile,
                        _suigrp.using_address,
                        _suigrp.alias_list.copy(),
                        _suigrp.key_list.copy(),
                        _suigrp.address_list.copy(),
                        [prfgrp.Profile(k, v) for k, v in _GQL_DEFAULTS.items()],
                    )
                )
            else:
                _mnem, new_addy, prf_key, prf_alias = (
                    prfgrp.ProfileGroup.new_keypair_parts(
                        alias="Primary",
                        alias_list=[],
                    )
                )
                self.groups.append(
                    prfgrp.ProfileGroup(
                        gql_rpc_group_name,
                        "testnet",
                        new_addy,
                        [prf_alias],
                        [prf_key],
                        [new_addy],
                        [prfgrp.Profile(k, v) for k, v in _GQL_DEFAULTS.items()],
                    )
                )

            _updated = True

        return _updated

    def add_group(
        self, *, group: prfgrp.ProfileGroup, make_active: bool, overwrite: bool = False
    ) -> bool:
        """."""
        # If group doesn't exist, create it
        _updated = False
        _res = self._group_exists(group_name=group.group_name)
        if not _res:
            self.groups.append(group)
            self.group_active = group.group_name if make_active else self.group_active
            _updated = True
        elif overwrite:
            # Replace with new group
            self.groups[self.groups.index(_res)] = group
            self.group_active = group.group_name if make_active else self.group_active
            _updated = True
        return _updated

    def remove_group(self, *, group_name: str):
        """Remove group from model."""
        _res = self._group_exists(group_name=group_name)
        if _res:
            _gindex = self.groups.index(_res)
            # Adjuest active group if the one being removed is it
            if _res.group_name == self.group_active:
                if _gindex:
                    self.group_active = self.groups[0].group_name
                elif len(self.groups) > 1:
                    self.group_active = self.groups[1].group_name
                else:
                    self.group_active = ""
            self.groups.pop(_gindex)
            return
        raise ValueError(f"Group {group_name} not found.")
