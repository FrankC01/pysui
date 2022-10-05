"""Sui Wallet Facade."""


from numbers import Number
import os
import json

from typing import Any, Union
from src.abstracts import KeyPair, Builder, SignatureScheme
from src.sui import (
    SuiClient,
    SuiConfig,
    SuiRpcResult,
    GetObjectsOwnedByAddress,
    GetObject,
    GetRawPackage,
)
from src.sui.sui_crypto import keypair_from_keystring, create_new_address, SuiAddress
from src.sui.sui_excepts import (
    SuiFileNotFound,
    SuiKeystoreFileError,
    SuiKeystoreAddressError,
    SuiNoKeyPairs,
    SuiRpcApiError,
)

from src.sui.sui_types import (
    SuiNativeCoinDescriptor,
    SuiGasType,
    ObjectInfo,
    SuiNftDescriptor,
    SuiDataDescriptor,
    from_object_descriptor,
    from_object_type,
)


class SuiWallet:
    """Sui Wallet Example."""

    def __init__(self, config: SuiConfig) -> None:
        """Initialize from keystore path."""
        if os.path.exists(config.keystore_file):
            self._keypairs = {}
            self._addresses = {}
            try:
                with open(config.keystore_file, encoding="utf8") as keyfile:
                    self._keystrings = json.load(keyfile)
                    if len(self._keystrings) > 0:
                        for keystr in self._keystrings:
                            self._keypairs[keystr] = keypair_from_keystring(keystr)
                            addy = SuiAddress.from_keypair_string(keystr)
                            self._addresses[str(addy.identifier)] = addy

                    else:
                        raise SuiNoKeyPairs()
                self._client = SuiClient(config)
            except IOError as exc:
                raise SuiKeystoreFileError(exc) from exc
            except json.JSONDecodeError as exc:
                raise SuiKeystoreAddressError(exc) from exc
        else:
            raise SuiFileNotFound(str(config.keystore_path))

    def _write_keypair(self, keypair: KeyPair, file_path: str = None) -> None:
        """Register the keypair and write out to keystore file."""
        filepath = file_path if file_path else self._client.config.keystore_file
        if os.path.exists(filepath):
            serialized = keypair.to_b64()
            self._keypairs[serialized] = keypair
            key_array = json.dumps(self.keystrings, indent=2)
            with open(filepath, "w", encoding="utf8") as keystore:
                keystore.write(key_array)
        else:
            raise SuiFileNotFound((filepath))

    @property
    def keystrings(self) -> list[str]:
        """Get keypair strings managed by wallet."""
        return list(self._keypairs)

    def keypair_for_keystring(self, key_string: str) -> KeyPair:
        """Get KeyPair for keystring."""
        return self._keypairs[key_string]

    def create_new_keypair_and_address(self, scheme: SignatureScheme) -> str:
        """
        Create a new keypair and address identifier and return the address string.

        The scheme defines generation of ED25519 or SECP256K1 keypairs.
        """
        if scheme == SignatureScheme.ED25519:
            keypair, address = create_new_address(scheme)
            self._addresses[address.identifer] = address
            self._write_keypair(keypair)
            return address.identifer
        raise NotImplementedError

    @property
    def current_address(self) -> str:
        """Get the current address."""
        return self._client.config.active_address

    @property
    def addresses(self) -> list[str]:
        """Get all the addresses."""
        return list(self._addresses.keys())

    def execute(self, builder: Builder) -> Any:
        """Execute the builder."""
        return self._client.execute(builder)

    def get_rpc_api_names(self) -> list[str]:
        """Fetch RCP API method names."""
        return self._client.rpc_api_names

    def get_rpc_api(self) -> dict:
        """Fetch RCP API descriptors."""
        return self._client.rpc_api

    def api_exists(self, api_name: str) -> bool:
        """Check if API supported in RPC host."""
        return self._client.api_exists(api_name)

    def get_package(self, package_id: str) -> Union[SuiRpcResult, Exception]:
        """Get details of Sui package."""
        result = self.execute(GetRawPackage(package_id)).json()
        if result["result"]["status"] != "Exists":
            if result["result"]["status"] == "Exists":
                return SuiRpcResult(False, f"Package id {package_id} {result['result']['status']}")
            return SuiRpcResult(False, f"Package id {package_id} is Deleted")
        if result["result"]["details"]["data"]["dataType"] == "package":
            return SuiRpcResult(True, None, from_object_type(result["result"]["details"]))
        return SuiRpcResult(False, f"ID: {package_id} is a move object, not a package")

    def get_type_descriptor(self, claz: ObjectInfo, address: str = None) -> Union[SuiRpcResult, Exception]:
        """Get descriptors of claz type for address."""
        builder = GetObjectsOwnedByAddress().set_address(address if address else self.current_address)
        result = self.execute(builder).json()
        type_descriptors = []
        if "error" in result:
            raise SuiRpcApiError(result["error"])
        for sui_objdesc in result["result"]:
            sui_type = from_object_descriptor(sui_objdesc)
            if isinstance(sui_type, claz):
                type_descriptors.append(sui_type)
        return SuiRpcResult(True, None, type_descriptors)

    def get_data_descriptors(self, address: str = None) -> Union[SuiRpcResult, Exception]:
        """Get the objects descriptors."""
        return self.get_type_descriptor(SuiDataDescriptor, address)

    def get_gas_descriptors(self, address: str = None) -> Union[SuiRpcResult, Exception]:
        """Get the gas object descriptors."""
        return self.get_type_descriptor(SuiNativeCoinDescriptor, address)

    def get_nft_descriptors(self, address: str = None) -> Union[SuiRpcResult, Exception]:
        """Get the gas object descriptors."""
        return self.get_type_descriptor(SuiNftDescriptor, address)

    def get_object(self, identifier: Any, address: str = None) -> Union[SuiRpcResult, Exception]:
        """Get specific object by it's id."""
        desc = self.get_type_descriptor(ObjectInfo, address)
        if desc.is_ok():
            for cdesc in desc.result_data:
                if str(cdesc.identifier) == str(identifier):
                    result = self.execute(GetObject().set_object(cdesc.identifier)).json()
                    if result["result"]["status"] != "Exists":
                        return SuiRpcResult(False, f"Object {cdesc.identifier} {result['result']['status']}", None)
                    return SuiRpcResult(True, None, from_object_type(result["result"]["details"]))
            return SuiRpcResult(False, f"Object with identifier '{identifier}' not found", None)
        return desc

    def get_objects(self, address: str = None, claz: ObjectInfo = None) -> Union[SuiRpcResult, Exception]:
        """Get specific object by address/id."""
        desc = self.get_type_descriptor(claz if claz else ObjectInfo, address)
        if desc.is_ok():
            obj_types = []
            for cdesc in desc.result_data:
                result = self.execute(GetObject().set_object(cdesc.identifier)).json()
                if result["result"]["status"] != "Exists":
                    return SuiRpcResult(False, f"Object {cdesc.identifier} {result['result']['status']}", None)
                data_object = from_object_type(result["result"]["details"])
                obj_types.append(data_object)
            return SuiRpcResult(True, None, obj_types)
        return desc

    def data_objects(self, address: str = None) -> Union[SuiRpcResult, Exception]:
        """Get the objects from descriptors."""
        desc = self.get_data_descriptors(address)
        if desc.is_ok():
            obj_types = []
            for cdesc in desc.result_data:
                result = self.execute(GetObject().set_object(cdesc.identifier)).json()
                if result["result"]["status"] != "Exists":
                    return SuiRpcResult(False, f"Object {cdesc.identifier} {result['result']['status']}", None)
                data_object = from_object_type(result["result"]["details"])
                obj_types.append(data_object)
            return SuiRpcResult(True, None, obj_types)
        return desc

    def nft_objects(self, address: str = None) -> Union[SuiRpcResult, Exception]:
        """Get the nft objects from descriptors."""
        desc = self.get_nft_descriptors(address)
        if desc.is_ok():
            nft_types = []
            for cdesc in desc.result_data:
                result = self.execute(GetObject().set_object(cdesc.identifier)).json()
                if result["result"]["status"] != "Exists":
                    return SuiRpcResult(False, f"Object {cdesc.identifier} {result['result']['status']}", None)
                nft_types.append(from_object_type(result["result"]["details"]))
            return SuiRpcResult(True, None, nft_types)
        return desc

    def gas_objects(self, address: str = None) -> Union[SuiRpcResult, Exception]:
        """Get the gas objects."""
        desc = self.get_gas_descriptors(address)
        if desc.is_ok():
            gas_types = []
            for cdesc in desc.result_data:
                result = self.execute(GetObject().set_object(cdesc.identifier)).json()
                if result["result"]["status"] != "Exists":
                    return SuiRpcResult(False, f"Object {cdesc.identifier} {result['result']['status']}", None)
                gas_types.append(from_object_type(result["result"]["details"]))
            return SuiRpcResult(True, None, gas_types)
        return desc

    def total_gas(self, gas_objects: list[SuiGasType]) -> Number:
        """Get the total gas for wallet."""
        results = 0
        for cdesc in gas_objects:
            results = results + cdesc.balance
        return results
