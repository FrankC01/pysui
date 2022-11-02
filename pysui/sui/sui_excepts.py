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


"""Sui Exceptions."""


class SuiException(Exception):
    """Base Exception."""


class SuiFileNotFound(SuiException):
    """Exception for file missing."""


# Config file exceptions


class SuiConfigFileError(SuiException):
    """Config file errors."""


class SuiKeystoreFileError(SuiException):
    """Keystore file errors."""


# Address exceptions


class SuiInvalidAddress(SuiException):
    """Invalid Sui address."""


# Keystring exceptions


class SuiKeystoreAddressError(SuiException):
    """Keystore file errors."""


class SuiInvalidKeystringLength(SuiException):
    """Invalid Keystring Length Exception."""

    def __init__(self, msg: int) -> None:
        """Initiate keystring length error."""
        self.args = (f"Invalid keystring length of {msg}",)


class SuiNoKeyPairs(SuiException):
    """Exception for missing keypairs."""

    def __init__(self) -> None:
        """Initialize no keypair exception."""
        self.args = ("No keypairs found",)


class SuiInvalidKeyPair(SuiException):
    """Invalid KeyPair Exception."""


# RPC API Discover Corruptions


class SuiApiDefinitionInvalid(SuiException):
    """Corrupted Schema Exception."""


class SuiParamSchemaInvalid(SuiException):
    """Corrupted Schema Exception."""


# RPC API exceptions


class SuiRpcApiNotAvailable(SuiException):
    """Non active or non-existing RPC API method exception."""


class SuiRpcApiMalformed(SuiException):
    """Sui Method malformed."""


class SuiRpcApiInvalidParameter(SuiException):
    """Sui Method invalid parameter."""


# RPC API exceptions


class SuiRpcApiError(SuiException):
    """For RPC error returns."""


# Publish exceptions


class SuiPackageBuildFail(SuiException):
    """For publishing."""


class SuiMiisingBuildFolder(SuiException):
    """For publishing."""


class SuiMiisingModuleByteCode(SuiException):
    """For publishing."""
