#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sui Configuration Group."""

import dataclasses
from typing import Optional
import dataclasses_json


@dataclasses.dataclass
class ProfileAlias(dataclasses_json.DataClassJsonMixin):
    """Holds alias for base64 public key."""

    alias: str
    public_key_base64: str


@dataclasses.dataclass
class ProfileKey(dataclasses_json.DataClassJsonMixin):
    """Holds private key base64 string."""

    private_key_base64: str


@dataclasses.dataclass
class Profile(dataclasses_json.DataClassJsonMixin):
    """Unique connection profile."""

    profile_name: str  # Known as environmental alias in sui configuration
    url: str
    faucet_url: Optional[str] = None
    faucet_status_url: Optional[str] = None


@dataclasses.dataclass
class ProfileGroup(dataclasses_json.DataClassJsonMixin):
    """Represents a group of profile."""

    group_name: str
    using_profile: str
    using_address: str
    alias_list: list[ProfileAlias]
    key_list: list[ProfileKey]
    address_list: Optional[list[str]] = dataclasses.field(default_factory=list)
    profiles: Optional[list[Profile]] = dataclasses.field(default_factory=list)

    def set_active_profile(self, *, change_to: str) -> Profile:
        """Set the using profile to change_to."""
        # Validate it exists
        _res = next(
            filter(lambda prf: prf.profile_name == change_to, self.profiles),
            -1,
        )
        if _res == -1:
            raise ValueError(
                f"{change_to} profile does not exist in group {self.group_name}"
            )
        self.using_profile = change_to

    def set_active_address(self, *, change_to: str) -> str:
        """Set the using address to change_to."""
        _ = self.address_list.index(change_to)
        self.using_address = change_to

    @property
    def active_profile(self) -> Profile:
        """Gets the active profile."""
        _res = next(
            filter(lambda prf: prf.profile_name == self.using_profile, self.profiles),
            -1,
        )
        if _res == -1:
            raise ValueError(f"Profile {self.using_profile} not found in group")
        return _res

    def add_profile(self, *, new_prf: Profile, make_active: bool = False):
        """Add profile to list after validating name"""
        _res = next(
            filter(lambda x: x.profile_name == new_prf.profile_name, self.profiles), -1
        )
        if _res != -1:
            raise ValueError(f"Profile {new_prf.profile_name} already exists.")
        self.profiles.append(new_prf)
        if make_active:
            self.set_active_profile(change_to=new_prf.profile_name)
