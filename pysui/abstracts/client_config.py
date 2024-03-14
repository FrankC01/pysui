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

"""Client Configuration Abstraction."""
from abc import ABC, abstractmethod
from typing import Union, Optional, Any
from enum import IntEnum
from base64 import b64encode
from deprecated.sphinx import versionadded, versionchanged
from .client_types import AbstractType
from .client_keypair import KeyPair, PublicKey


class CrefType(IntEnum):
    """."""

    ALIAS = 0
    KPAIR = 1
    PKEY = 2
    ADDY = 3
    INDEX = 4


@versionchanged(version="0.41.0", reason="Sui aliases configuration feature added")
class ClientConfiguration(ABC):
    """Base abstraction for managing a clients configuration."""

    def __init__(
        self, config_path: str, keystore_file: str, alias_file: Optional[str] = None
    ):
        """__init__ ClientConfiguration initializer.

        :param config_path: Fully qualified path to SUI `client.yaml`
        :type config_path: str
        :param keystore_file: Fully qualified path to `sui.keystore`
        :type keystore_file: str
        :param alias_file: Fully qualified path to `sui.aliases`,default = None
        :type alias_file: Optional[str], optional
        """
        self._current_keystore_file = keystore_file
        self._current_alias_file = alias_file
        self._configuration_path = config_path
        self._cref_matrix: list[list[dict]] = []

    def _cref_result_for(
        self, value: str, vin: CrefType, vout: CrefType
    ) -> Union[int, Any]:
        """."""
        result = None
        for index, mrow in enumerate(self._cref_matrix):
            if value in mrow[vin]:
                if vout == CrefType.INDEX:
                    result = index
                else:
                    result = list(mrow[vout].values())[0]
                break
        return result

    def _get_cref_value(
        self, value: str, vin: CrefType, vout: CrefType
    ) -> Union[int, Any]:
        """_get_cref Gets an associated value of input value.

        :param value: The key value
        :type value: str
        :param vin: What type does value represent
        :type vin: CrefType
        :param vout: What value type result to return
        :type vout: CrefType
        :raises ValueError: If input value is not present or vin type
        :return: Either int (if vout CrefType.INDEX) or value (if vout !CrefType.INDEX)
        :rtype: Union[int, Any]
        """
        result = self._cref_result_for(value, vin, vout)
        if result is None:
            raise ValueError(f"{value} not found for {vin.name}")
        return result

    @abstractmethod
    def _alias_check_or_gen(
        self,
        *,
        aliases: Optional[list[str]] = None,
        word_counts: Optional[int] = 12,
        alias: Optional[str] = None,
        current_iter: Optional[int] = 0,
    ) -> str:
        """_alias_check_or_gen If alias is provided, checks if unique otherwise creates one or more.

        :param aliases: List of existing aliases
        :type aliases: list[str]
        :param word_counts: Words count used for mnemonic phrase, defaults to 12
        :type word_counts: Optional[int], optional
        :param alias: An inbound alias, defaults to None
        :type alias: Optional[str], optional
        :param current_iter: Internal recursion count, defaults to 0
        :type current_iter: Optional[int], optional
        :return: An alias
        :rtype: str
        """

    @abstractmethod
    def _alias_gen_batch(self, *, word_counts: int) -> list[str]:
        """_alias_gen_batch Generates a batch of alias name pairs

        :param word_counts: Words count used for mnemonic phrase
        :type word_counts: int
        :return: A list of alias-name pairs
        :rtype: list[str]
        """

    def _alias_assocation(self, aliases: list[dict]) -> None:
        """_alias_assocation Completes cross reference with aliases.

        If there is no dictionary of aliases we create them and associate with
        public key string.

        :param aliases: list of dicts with alias to public keystr association
        :type aliases: list[dict]
        :raises ValueError: if aliases count not equal to keypairs count
        :return: None
        :rtype: NoneType
        """
        # If there are aliases then they were already persisted
        if aliases:
            if len(aliases) == len(self._cref_matrix):
                for alias_dict in aliases:
                    alias_name = alias_dict.get("alias")
                    pub_key_str = alias_dict["public_key_base64"]
                    at_row = self._get_cref_value(
                        pub_key_str, CrefType.PKEY, CrefType.INDEX
                    )
                    self._cref_matrix[at_row][CrefType.ALIAS] = {
                        alias_name: pub_key_str
                    }
            else:
                raise ValueError(
                    f"Aliases count {len(aliases)} does not match address/key count {len(self._cref_matrix)}"
                )
        # otherwise if we have keys we can gen aliases (scales to any size)
        elif self._cref_matrix:
            crlen = len(self._cref_matrix)
            basefetch = int(crlen / 12)
            fetches = basefetch + 1 if crlen % 12 else basefetch
            accumer: list[str] = []
            for _ in range(fetches):
                accumer.extend(self._alias_gen_batch(word_counts=24))

            for index, at_row in enumerate(self._cref_matrix):
                at_row[CrefType.ALIAS] = {
                    accumer[index]: next(iter(at_row[CrefType.PKEY]))
                }

    def _replace_alias_key(self, row_index: int, new_key: str) -> str:
        """_replace_alias_key Replaces the alias key (rename) at cref row index.

        :param row_index: The _cref_matrix index
        :type row_index: int
        :param new_key: The new alias name for row
        :type new_key: str
        :return: The old key
        :rtype: str
        """
        cref_row = self._cref_matrix[row_index]
        old_alias = cref_row[CrefType.ALIAS]
        cref_row[CrefType.ALIAS] = {new_key: list(old_alias.values())[0]}
        return next(iter(old_alias))

    @property
    def _has_aliases(self) -> bool:
        """_has_aliases Tests if aliases are part of crefCrefType

        :return: True if aliases present
        :rtype: bool
        """
        return self._cref_matrix and self._cref_matrix[0] and self._cref_matrix[0][0]

    @property
    @abstractmethod
    def rpc_url(self) -> str:
        """Return the URL the client configuration has."""

    @property
    @abstractmethod
    def active_address(self) -> AbstractType:
        """Return the active address from the client configuration."""

    @property
    def keystore_file(self) -> str:
        """Get the keystore filename."""
        return self._current_keystore_file

    @versionadded(version="0.41.0", reason="Supporting aliases")
    @property
    def alias_file(self) -> str:
        """Get the alias filename."""
        return self._current_alias_file

    @versionadded(version="0.41.0", reason="Supporting aliases")
    @property
    def aliases(self) -> list[str]:
        """Get aliases managed by wallet."""
        return (
            [next(iter(cref_row[CrefType.ALIAS])) for cref_row in self._cref_matrix]
            if self._cref_matrix
            else []
        )

    @versionadded(version="0.41.0", reason="Supporting aliases")
    def aliases_encode(self) -> list[dict]:
        """Encodes aliases."""
        encoded_aliases: list[dict] = []
        if self._has_aliases:
            encoded_aliases = [
                [{"alias": k, "public_key_base64": v} for k, v in drows.items()][0]
                for drows in [crow[CrefType.ALIAS] for crow in self._cref_matrix]
            ]
        return encoded_aliases

    @property
    def keystrings(self) -> list[str]:
        """Get keypair strings managed by wallet."""
        return [next(iter(cref_row[CrefType.KPAIR])) for cref_row in self._cref_matrix]

    @property
    def addresses_and_keys(self) -> dict:
        """Get a copy of dictionary of address/keypair."""
        return {
            next(iter(cref_row[CrefType.ADDY])): list(
                cref_row[CrefType.KPAIR].values()
            )[0]
            for cref_row in self._cref_matrix
        }

    @property
    def addresses(self) -> list[str]:
        """Get all the addresses."""
        return [next(iter(cref_row[CrefType.ADDY])) for cref_row in self._cref_matrix]

    def keypair_for_keystring(self, key_string: str) -> KeyPair:
        """Get KeyPair for keystring."""
        return self._get_cref_value(key_string, CrefType.KPAIR, CrefType.KPAIR)

    def keypair_for_address(self, addy: AbstractType) -> KeyPair:
        """Get the keypair for a given address."""
        return self._get_cref_value(addy.address, CrefType.ADDY, CrefType.KPAIR)

    def keypair_for_publickey(self, pub_key: PublicKey) -> Union[KeyPair, None]:
        """Return the keypair for the public key or None if no match."""
        return self._get_cref_value(
            b64encode(pub_key.scheme_and_key()).decode(), CrefType.PKEY, CrefType.KPAIR
        )

    @versionadded(version="0.54.0", reason="Supporting aliases")
    def kp4add(self, addy: str) -> KeyPair:
        """Get the keypair for a given address."""
        return self._get_cref_value(addy, CrefType.ADDY, CrefType.KPAIR)

    @versionadded(version="0.41.0", reason="Supporting aliases")
    def addr4al(self, alias: str) -> AbstractType:
        """addr4al Returns an address for an alias

        :param alias: alias name
        :type alias: str
        :return: The SuiAddress for alias
        :rtype: AbstractType
        """
        return self._get_cref_value(alias, CrefType.ALIAS, CrefType.ADDY)

    @versionadded(version="0.41.0", reason="Supporting aliases")
    def kp4al(self, alias: str) -> Union[KeyPair, None]:
        """kp4al Returns the keypair associated with alias

        :param alias: alias name
        :type alias: str
        :return: The KeyPair associated to alias
        :rtype: Union[KeyPair, None]
        """
        return self._get_cref_value(alias, CrefType.ALIAS, CrefType.KPAIR)

    @versionadded(version="0.41.0", reason="Supporting aliases")
    def pk4al(self, alias: str) -> Union[PublicKey, None]:
        """pk4al Returns the PublicKey associated with alias

        :param alias: alias name
        :type alias: str
        :return: The PublicKey associated to alias
        :rtype: Union[PublicKey, None]
        """
        return self._get_cref_value(alias, CrefType.ALIAS, CrefType.PKEY)

    @versionadded(version="0.41.0", reason="Supporting aliases")
    def al4addr(self, addr: Union[str, AbstractType]) -> str:
        """al4addr Returns an alias for an address

        :param addr: Address str or Address type
        :type alias: Union[str, AbstractType]
        :return: The alias name associated to address
        :rtype: str
        """
        addy = addr if isinstance(addr, str) else addr.address
        result = self._get_cref_value(addy, CrefType.ADDY, CrefType.INDEX)
        return next(iter(self._cref_matrix[result][CrefType.ALIAS]))

    @versionadded(version="0.41.0", reason="Supporting aliases")
    def al4kp(self, kp: KeyPair) -> str:
        """al4kp Returns the alias associated with keypair

        :param kp: Key pair to find associated alias
        :type kp: KeyPair
        :return: The alias name associated to KeyPair
        :rtype: str
        """
        kps = kp.serialize()
        result = self._get_cref_value(kps, CrefType.KPAIR, CrefType.INDEX)
        return next(iter(self._cref_matrix[result][CrefType.ALIAS]))

    @versionadded(version="0.41.0", reason="Supporting aliases")
    def al4pk(self, pk: PublicKey) -> str:
        """al4pk Returns the alias associated with PublicKey

        :param pk: Public key to find associated alias
        :type pk: PublicKey
        :return: The alias associated to PublicKey
        :rtype: str
        """
        pks = b64encode(pk.scheme_and_key()).decode()
        result = self._get_cref_value(pks, CrefType.PKEY, CrefType.INDEX)
        return next(iter(self._cref_matrix[result][CrefType.ALIAS]))
