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
    """Non active or existing RPC API exception."""
