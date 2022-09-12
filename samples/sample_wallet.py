"""Sui Wallet Facade."""

from numbers import Number
import os
import json
from typing import Any
from src.abstracts import KeyPair
from src.abstracts import Builder
from src.sui import (
    SuiClient,
    SuiConfig,
    GetObjectsOwnedByAddress,
    GetObject,
    parse_sui_object_descriptors,
    parse_sui_object_type,
)
from src.sui.sui_excepts import SuiFileNotFound, SuiKeystoreFileError, SuiKeystoreAddressError
from src.sui.sui_crypto import keypair_from_b64address
from sui.sui_types import SuiNativeCoinDescriptor, SuiGasType, SuiObjectDescriptor, SuiNftDescriptor, SuiNftType


class SuiWallet:
    """Wallet."""

    def __init__(self, config: SuiConfig) -> None:
        """Initialize from keystore path."""
        if os.path.exists(config.keystore_file):
            self._keypairs = {}
            try:
                with open(config.keystore_file, encoding="utf8") as keyfile:
                    self._keystrings = json.load(keyfile)
                    if len(self._keystrings) > 0:
                        for keystr in self._keystrings:
                            self._keypairs[keystr] = keypair_from_b64address(keystr)

                self._client = SuiClient(config)
            except IOError as exc:
                raise SuiKeystoreFileError(exc) from exc
            except json.JSONDecodeError as exc:
                raise SuiKeystoreAddressError(exc) from exc
        else:
            raise SuiFileNotFound(str(config.keystore_path))

    @property
    def keystrings(self) -> list[str]:
        """Get keypair strings managed by wallet."""
        return list(self._keypairs)

    def keypair_for_keystring(self, key_string: str) -> KeyPair:
        """Get KeyPair for keystring."""
        return self._keypairs[key_string]

    @property
    def current_address(self) -> str:
        """Get the current address."""
        return self._client.config.active_address

    def execute(self, builder: Builder) -> Any:
        """Execute the builder."""
        return self._client.execute(builder)

    def get_type_descriptor(self, claz: SuiObjectDescriptor) -> list[SuiObjectDescriptor]:
        """Get descriptors of claz type."""
        result = self.execute(GetObjectsOwnedByAddress().add_parameter(self.current_address))
        type_descriptors = []
        for sui_objdesc in result.json()["result"]:
            sui_type = parse_sui_object_descriptors(sui_objdesc)
            if isinstance(sui_type, claz):
                type_descriptors.append(sui_type)
        return type_descriptors

    def get_gas_descriptors(self) -> list[SuiNativeCoinDescriptor]:
        """Get the gas object descriptors."""
        return self.get_type_descriptor(SuiNativeCoinDescriptor)

    def get_nft_descriptors(self) -> list[SuiNftDescriptor]:
        """Get the gas object descriptors."""
        return self.get_type_descriptor(SuiNftDescriptor)

    def nft_objects(self) -> list[SuiNftType]:
        """Get the gas object descriptors."""
        desc = self.get_nft_descriptors()
        nft_types = []
        for cdesc in desc:
            result = self.execute(GetObject().add_parameter(cdesc.identifer))
            nft_types.append(parse_sui_object_type(result.json()["result"]["details"]["data"]))
        return nft_types

    def gas_objects(self) -> list[SuiGasType]:
        """Get the gas objects."""
        desc = self.get_gas_descriptors()
        gas_types = []
        for cdesc in desc:
            result = self.execute(GetObject().add_parameter(cdesc.identifer))
            gas_types.append(parse_sui_object_type(result.json()["result"]["details"]["data"]))
        return gas_types

    def total_gas(self, gas_objects: list[SuiGasType]) -> Number:
        """Get the total gas for wallet."""
        results = 0
        for cdesc in gas_objects:
            results = results + cdesc.balance
        return results
