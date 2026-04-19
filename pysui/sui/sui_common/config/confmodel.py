#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sui Configuration Model."""

import dataclasses
from typing import Optional
from deprecated.sphinx import versionchanged
import dataclasses_json


import pysui.sui.sui_common.config.confgroup as prfgrp

_GQL_DEFAULTS: dict = {
    "devnet": "https://sui-devnet.mystenlabs.com/graphql",
    "testnet": "https://sui-testnet.mystenlabs.com/graphql",
    "mainnet": "https://sui-mainnet.mystenlabs.com/graphql",
}

_CONFIG_VERSION_100: str = "1.0.0"
_CURRENT_CONFIG_VERSION: str = "1.1.0"


@dataclasses.dataclass
class PysuiConfigModel(dataclasses_json.DataClassJsonMixin):
    """pysui configuration in memory model."""

    version: str = dataclasses.field(default="")
    sui_binary: str = dataclasses.field(default="")
    group_active: str = dataclasses.field(default="")
    groups: list[prfgrp.ProfileGroup] = dataclasses.field(default_factory=list)

    def _group_exists(
        self, *, group_name: str
    ) -> Optional[prfgrp.ProfileGroup]:
        """Check if a group, by name, exists."""
        return next(
            (grp for grp in self.groups if grp.group_name == group_name), None
        )

    def has_group(self, *, group_name: str) -> bool:
        """Test for group existence."""
        return bool(self._group_exists(group_name=group_name))

    def get_group(self, *, group_name: str) -> prfgrp.ProfileGroup:
        """Get a group or throw exception if doesn't exist."""
        _res = self._group_exists(group_name=group_name)
        if not _res:
            raise ValueError(f"{group_name} does not exist.")
        return _res

    def update_model(self, gql_well_known: str, grpc_well_known: str) -> bool:
        """Update the model."""
        # If prior was 1.0.0, 1.1.0 brings protocol indicator
        # in groups
        change_made: bool = False
        if self.version == _CONFIG_VERSION_100:
            change_made = True
            for g in self.groups:
                if g.group_name == gql_well_known:
                    g.protocol = prfgrp.GroupProtocol.GRAPHQL
                elif g.group_name == grpc_well_known:
                    g.protocol = prfgrp.GroupProtocol.GRPC
                else:
                    g.protocol = prfgrp.GroupProtocol.OTHER
        return change_made

    @property
    def active_group(self) -> prfgrp.ProfileGroup:
        """Returns the active group."""
        _res = self._group_exists(group_name=self.group_active)
        if _res:
            return _res
        raise ValueError("No active group set")

    @active_group.setter
    def active_group(self, group_str: str) -> None:
        """Sets the active group."""
        _res = self._group_exists(group_name=group_str)
        if _res:
            self.group_active = group_str
            return
        raise ValueError(f"{group_str} does not exist")

    @property
    def active_address(self) -> str:
        """Returns the active address from the active group."""
        return self.active_group.using_address

    def gql_version_fixup(
        self,
        *,
        group_name: str,
    ):
        """Called when no version set so was pre-initialized."""
        try:
            gql_group = self.get_group(group_name=group_name)
            gql_prof = gql_group.get_profile(profile_name="devnet")
            gql_prof.url = _GQL_DEFAULTS["devnet"]
            gql_group.remove_profile(profile_name="devnet_beta")
        except:
            pass
        self.version = _CURRENT_CONFIG_VERSION

    def add_group(
        self, *, group: prfgrp.ProfileGroup, make_active: bool, overwrite: bool = False
    ) -> bool:
        """Add a new group to the model."""
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

    @versionchanged(version="0.86.0", reason="Return new active replacing removed.")
    def remove_group(self, *, group_name: str) -> str:
        """Remove group from model, reassign active and return name."""
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
            return self.group_active
        raise ValueError(f"Group {group_name} not found.")
