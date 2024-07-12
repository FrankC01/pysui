#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sui Configuration Group."""

import dataclasses
from typing import Optional, Union
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

    def _profile_exists(self, *, profile_name: str) -> Union[Profile, bool]:
        """Check if a profile, by name, exists."""
        return next(
            filter(lambda prf: prf.profile_name == profile_name, self.profiles), False
        )

    def _alias_exists(self, *, alias_name: str) -> Union[ProfileAlias, bool]:
        """Check if an alias, by name, exists."""
        return next(
            filter(lambda ally: ally.alias == alias_name, self.alias_list), False
        )

    @property
    def active_address(self) -> str:
        """Return the active address."""
        return self.using_address

    @active_address.setter
    def active_address(self, change_to: str) -> str:
        """Set the using address to change_to."""
        _ = self.address_list.index(change_to)
        self.using_address = change_to
        return change_to

    @property
    def active_alias(self) -> str:
        """Return the alias associated to the using (active) address."""
        adex = self.address_list.index(self.using_address)
        return self.alias_list[adex].alias

    @active_alias.setter
    def active_alias(self, change_to: str) -> str:
        """Change the alias that is active."""
        # Find the index of the change_to alias
        _res = self._alias_exists(alias_name=change_to)
        if _res:
            aliindx = self.alias_list.index(_res)
            self.using_address = self.address_list[aliindx]
            return _res.alias
        raise ValueError(f"Alias {change_to} not found in group")

    @property
    def active_profile(self) -> Profile:
        """Gets the active profile."""
        _res = self._profile_exists(profile_name=self.using_profile)
        if _res:
            return _res
        raise ValueError(f"Profile {self.using_profile} not found in group")

    @active_profile.setter
    def active_profile(self, change_to: str) -> Profile:
        """Set the using Profile to change_to."""
        # Validate it exists
        _res = self._profile_exists(profile_name=change_to)
        if _res:
            self.using_profile = change_to
            return _res
        raise ValueError(f"{change_to} profile does not exist")

    def add_profile(self, *, new_prf: Profile, make_active: bool = False):
        """Add profile to list after validating name"""
        _res = self._profile_exists(profile_name=new_prf.profile_name)
        if _res:
            raise ValueError(f"Profile {new_prf.profile_name} already exists.")
        self.profiles.append(new_prf)
        if make_active:
            self.active_profile = new_prf.profile_name
