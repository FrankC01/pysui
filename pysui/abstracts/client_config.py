#    Copyright 2022 Frank V. Castellucci
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
from .client_types import AbstractType
from .client_keypair import KeyPair


class ClientConfiguration(ABC):
    """Base abstraction for managing a clients configuration."""

    def __init__(self, config_path: str, keystore_file: str):
        """__init__ ClientConfiguration initializer.

        :param config_path: Fully qualified path to SUI `client.yaml`
        :type config_path: str
        :param keystore_file: Full qualified path to `sui.keystore`
        :type keystore_file: str
        """
        self._current_keystore_file = keystore_file
        self._configuration_path = config_path
        self._keypairs = {}
        self._addresses = {}
        self._address_keypair = {}

    @property
    @abstractmethod
    def rpc_url(self) -> str:
        """Return the URL the client configuration has."""

    @property
    @abstractmethod
    def active_address(self) -> AbstractType:
        """Return the active address from the client configuration."""

    @property
    def configuration_path(self) -> str:
        """configuration_path Returns the configuration path that defined configuraiton instance.

        :return: The fully qualified configuration path
        :rtype: str
        """
        return self._configuration_path

    @property
    def keystore_file(self) -> str:
        """Get the kestore filename."""
        return self._current_keystore_file

    @property
    def keystrings(self) -> list[str]:
        """Get keypair strings managed by wallet."""
        return list(self._keypairs)

    @property
    def addresses(self) -> list[str]:
        """Get all the addresses."""
        return list(self._addresses.keys())

    def keypair_for_keystring(self, key_string: str) -> KeyPair:
        """Get KeyPair for keystring."""
        return self._keypairs[key_string]

    def keypair_for_address(self, addy: AbstractType) -> KeyPair:
        """Get the keypair for a given address."""
        if addy.address in self._address_keypair:
            return self._address_keypair[addy.address]
        raise ValueError(f"{addy.address} is not known")
