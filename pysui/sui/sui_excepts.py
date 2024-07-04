#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sui Exceptions."""

from deprecated.sphinx import deprecated


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class SuiException(Exception):
    """Base Exception."""


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class SuiFileNotFound(SuiException):
    """Exception for file missing."""


# Config file exceptions


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class SuiConfigFileError(SuiException):
    """Config file errors."""


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class SuiKeystoreFileError(SuiException):
    """Keystore file errors."""


# Address exceptions


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class SuiInvalidAddress(SuiException):
    """Invalid Sui address."""


# Keystring exceptions


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class SuiKeystoreAddressError(SuiException):
    """Keystore file errors."""


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class SuiInvalidKeystringLength(SuiException):
    """Invalid Keystring Length Exception."""

    def __init__(self, msg: int) -> None:
        """Initiate keystring length error."""
        self.args = (f"Invalid keystring length of {msg}",)


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class SuiNoKeyPairs(SuiException):
    """Exception for missing keypairs."""

    def __init__(self) -> None:
        """Initialize no keypair exception."""
        self.args = ("No keypairs found",)


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class SuiInvalidKeyPair(SuiException):
    """Invalid KeyPair Exception."""


# Signing exceptions


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class SuiNotComplexTransaction(SuiException):
    """Exception for attempting to sign a simple transaction."""

    def __init__(self, tx_name) -> None:
        """Initialize."""
        self.args = (f"{tx_name} does not require signing",)


# RPC API Discover Corruptions


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class SuiApiDefinitionInvalid(SuiException):
    """Corrupted Schema Exception."""


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class SuiParamSchemaInvalid(SuiException):
    """Corrupted Schema Exception."""


# RPC API exceptions


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class SuiRpcApiNotAvailable(SuiException):
    """Non active or non-existing RPC API method exception."""


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class SuiRpcApiMalformed(SuiException):
    """Sui Method malformed."""


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class SuiRpcApiInvalidParameter(SuiException):
    """Sui Method invalid parameter."""


# RPC API exceptions


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class SuiRpcApiError(SuiException):
    """For RPC error returns."""


# Publish exceptions


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class SuiPackageBuildFail(SuiException):
    """For publishing."""


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class SuiMiisingBuildFolder(SuiException):
    """For publishing."""


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class SuiMiisingModuleByteCode(SuiException):
    """For publishing."""
