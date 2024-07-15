#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sui Configuration Group."""

import base64
import hashlib
import dataclasses
from typing import Optional, Union
import dataclasses_json
import pysui.sui.sui_crypto as crypto


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

    def _address_exists(self, *, address: str) -> Union[str, bool]:
        """Check if address is valid."""
        return next(filter(lambda addy: addy == address, self.address_list), False)

    def _key_exists(self, *, key_string: str) -> Union[ProfileKey, bool]:
        """Check if key string exists."""
        return next(
            filter(lambda pkey: pkey.private_key_base64 == key_string, self.key_list),
            False,
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

    def address_for_alias(self, *, alias: str) -> str:
        """Get address associated with alias."""
        _res = self._alias_exists(alias_name=alias)
        if _res:
            aliindx = self.alias_list.index(_res)
            return self.address_list[aliindx]
        raise ValueError(f"Alias {alias} not found in group")

    def alias_for_address(self, *, address: str) -> ProfileAlias:
        """Get alias associated with address."""
        _res = self._address_exists(address=address)
        if _res:
            adindex = self.address_list.index(_res)
            return self.alias_list[adindex]
        raise ValueError(f"Address {address} not found in group")

    def alias_name_for_address(self, *, address: str) -> str:
        """Get alias associated with address."""
        _res = self._address_exists(address=address)
        if _res:
            adindex = self.address_list.index(_res)
            return self.alias_list[adindex].alias
        raise ValueError(f"Address {address} not found in group")

    def replace_alias_name(self, *, from_alias: str, to_alias: str) -> str:
        """Replace alias name and return associated address."""
        _res = self._alias_exists(alias_name=from_alias)
        if _res:
            _rese = self._alias_exists(alias_name=to_alias)
            if not _rese:
                aliindx = self.alias_list.index(_res)
                _res.alias = to_alias
                return self.address_list[aliindx]
            raise ValueError(f"Alias {to_alias} already exists")
        raise ValueError(f"Alias {from_alias} not found in group")

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

    def address_keypair(self, *, address: str) -> crypto.SuiKeyPair:
        """Fetch an addresses KeyPair."""
        _res = self._address_exists(address=address)
        if _res:
            return crypto.keypair_from_keystring(
                self.key_list[self.address_list.index(_res)].private_key_base64
            )

    def add_keypair_and_parts(
        self,
        *,
        new_alias: str,
        new_keypair: crypto.SuiKeyPair,
        make_active: Optional[bool] = False,
    ) -> str:
        """Add a new keypair with associated address and alias."""
        _new_keystr = new_keypair.serialize()
        if not self._key_exists(key_string=_new_keystr):
            if self._alias_exists(alias_name=new_alias):
                raise ValueError(
                    f"Alias {new_alias} already exist attempting new key and address."
                )
            # ProfileKey Entry
            _prvk_entry = ProfileKey(_new_keystr)
            # Generate artifacts
            _pkey_bytes = new_keypair.to_bytes()
            _digest = _pkey_bytes[0:33] if _pkey_bytes[0] == 0 else _pkey_bytes[0:34]
            # ProfileAlias Entry
            _alias_entry = ProfileAlias(
                new_alias,
                base64.b64encode(new_keypair.public_key.scheme_and_key()).decode(),
            )
            _new_addy = format(
                f"0x{hashlib.blake2b(_digest, digest_size=32).hexdigest()}"
            )
            # Populate group
            self.address_list.append(_new_addy)
            self.key_list.append(_prvk_entry)
            self.alias_list.append(_alias_entry)

            if make_active:
                self.using_address = _new_addy
            return _new_addy
        raise ValueError(
            f"Private keystring {_new_keystr} already exists attempting new key and address.."
        )

    def add_profile(self, *, new_prf: Profile, make_active: bool = False):
        """Add profile to list after validating name"""
        _res = self._profile_exists(profile_name=new_prf.profile_name)
        if _res:
            raise ValueError(f"Profile {new_prf.profile_name} already exists.")
        self.profiles.append(new_prf)
        if make_active:
            self.active_profile = new_prf.profile_name
