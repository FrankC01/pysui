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


class _Matrix(IntEnum):
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

    def _get_cref(self, value: str, vin: _Matrix, vout: _Matrix) -> Union[int, Any]:
        """."""
        result = None
        for index, mrow in enumerate(self._cref_matrix):
            if value in mrow[vin]:
                result = (
                    index if vout == _Matrix.INDEX else list(mrow[vout].values())[0]
                )
                break
        if result is None:
            raise ValueError(f"{value} not found for {vin}")
        return result

    @abstractmethod
    def _alias_check_or_gen(
        self,
        *,
        aliases: Optional[list[str]] = None,
        word_counts: Optional[int] = 12,
        alias: Optional[str] = None,
        just_one: Optional[bool] = True,
        current_iter: Optional[int] = 0,
    ) -> Union[str, list[str]]:
        """_alias_check_or_gen If alias is provided, checks if unique otherwise creates one or more.

        :param aliases: List of existing aliases
        :type aliases: list[str]
        :param word_counts: Words count used for mnemonic phrase, defaults to 12
        :type word_counts: Optional[int], optional
        :param alias: An inbound alias, defaults to None
        :type alias: Optional[str], optional
        :param just_one: If just 1 alias otherwise return parts list, defaults to True
        :type just_one: Optional[bool], optional
        :param current_iter: Internal recursion count, defaults to 0
        :type current_iter: Optional[int], optional
        :return: One or more aliases
        :rtype: Union[str, list[str]]
        """

    def _alias_assocation(self, aliases: list[dict]) -> None:
        """_alias_assocation Completes cross reference with aliases.

        If there is no dictionary of aliases we create them and associate with
        public key string.

        :param aliases: list of dicts with alias to public keystr association
        :type aliases: list[dict]
        :raises ValueError: if alias dictionary is empty
        :return: None
        :rtype: NoneType
        """
        # If there are aliases then they were already persisted
        if aliases:
            for alias_dict in aliases:
                alias_name = alias_dict.get("alias")
                pub_key_str = alias_dict["public_key_base64"]
                at_row = self._get_cref(pub_key_str, _Matrix.PKEY, _Matrix.INDEX)
                self._cref_matrix[at_row][_Matrix.ALIAS] = {alias_name: pub_key_str}
        # otherwise if we have keys we can gen aliases (scales to any size)
        elif self._cref_matrix:
            crlen = len(self._cref_matrix)
            basefetch = int(crlen / 12)
            fetches = basefetch + 1 if crlen % 12 else basefetch
            accumer: list[str] = []
            for _ in range(fetches):
                accumer.extend(
                    self._alias_check_or_gen(alias=[], word_counts=24, just_one=False)
                )
            for index, at_row in enumerate(self._cref_matrix):
                at_row[_Matrix.ALIAS] = {
                    accumer[index]: next(iter(at_row[_Matrix.PKEY]))
                }

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
            [next(iter(cref_row[_Matrix.ALIAS])) for cref_row in self._cref_matrix]
            if self.alias_file
            else []
        )

    @versionadded(version="0.41.0", reason="Supporting aliases")
    def aliases_encode(self) -> list[dict]:
        """Encodes aliases."""
        # arows = [crow[_Matrix.ALIAS] for crow in self._cref_matrix]
        return [
            [{"alias": k, "public_key_base64": v} for k, v in drows.items()][0]
            for drows in [crow[_Matrix.ALIAS] for crow in self._cref_matrix]
        ]

    @property
    def keystrings(self) -> list[str]:
        """Get keypair strings managed by wallet."""
        return [next(iter(cref_row[_Matrix.KPAIR])) for cref_row in self._cref_matrix]

    @property
    def addresses_and_keys(self) -> dict:
        """Get a copy of dictionary of address/keypair."""
        return {
            next(iter(cref_row[_Matrix.ADDY])): list(cref_row[_Matrix.KPAIR].values())[
                0
            ]
            for cref_row in self._cref_matrix
        }

    @property
    def addresses(self) -> list[str]:
        """Get all the addresses."""
        return [next(iter(cref_row[_Matrix.ADDY])) for cref_row in self._cref_matrix]

    def keypair_for_keystring(self, key_string: str) -> KeyPair:
        """Get KeyPair for keystring."""
        return self._get_cref(key_string, _Matrix.KPAIR, _Matrix.KPAIR)

    def keypair_for_address(self, addy: AbstractType) -> KeyPair:
        """Get the keypair for a given address."""
        return self._get_cref(addy.address, _Matrix.ADDY, _Matrix.KPAIR)

    def keypair_for_publickey(self, pub_key: PublicKey) -> Union[KeyPair, None]:
        """Return the keypair for the public key or None if no match."""
        return self._get_cref(
            b64encode(pub_key.scheme_and_key()).decode(), _Matrix.PKEY, _Matrix.KPAIR
        )

    @versionadded(version="0.41.0", reason="Supporting aliases")
    def address_for_alias(self, alias: str) -> AbstractType:
        """address_for_alias Returns an address for an alias

        :param alias: alias name
        :type alias: str
        :return: The SuiAddress for alias
        :rtype: AbstractType
        """
        return self._get_cref(alias, _Matrix.ALIAS, _Matrix.ADDY)

    @versionadded(version="0.41.0", reason="Supporting aliases")
    def keypair_for_alias(self, alias: str) -> Union[KeyPair, None]:
        """keypair_for_alias Returns the keypair associated with alias

        :param alias: alias name
        :type alias: str
        :return: The KeyPair associated to alias
        :rtype: Union[KeyPair, None]
        """
        return self._get_cref(alias, _Matrix.ALIAS, _Matrix.KPAIR)
