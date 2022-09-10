"""Sui Exceptions."""


class SuiException(Exception):
    """Base Exception."""


class SuiConfigFileError(SuiException):
    """Config file errors."""

    def __init__(self, caught: Exception) -> None:
        """Wrap the IU Error."""
        self.args = caught.args


class SuiFileNotFound(SuiException):
    """Exception for file missing."""

    def __init__(self, file_name: str) -> None:
        """Add filename to exception args."""
        self.args = f"Can't find file {file_name}"


class SuiInvalidKeyPair(SuiException):
    """Invalid KeyPair Exception."""

    def __init__(self, msg: str) -> None:
        """Indicate type of error."""
        self.args = f"{msg}"
