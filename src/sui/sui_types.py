"""Sui Types."""

from abstracts import ClientType


class SuiBaseType(ClientType):
    """Base SUI Type."""

    def __init__(self, indata: dict) -> None:
        """Initialize the base."""
        self._identifier = indata["objectId"]
        self._version = indata["version"]
        self._owner = indata["owner"]["AddressOwner"]
        self._digest = indata["digest"]
        self._previous_txn = indata["previousTransaction"]

    @property
    def identifer(self) -> str:
        """Return the type identifer."""
        return self._identifier

    @property
    def version(self) -> int:
        """Return the types version."""
        return self._version

    @property
    def owner(self):
        """Return the types instance owner."""
        return self._owner


class SuiCoin(SuiBaseType):
    """Sui Coin but not necessarily gas."""

    # def __init__(self, indata: dict) -> None:
    #     """Initialize a Sui coint object."""
    #     super().__init__(indata)


class SuiGas(SuiCoin):
    """Sui gas is a coin."""

    # def __init__(self, indata: dict) -> None:
    #     """Initialize a Sui gas object."""
    #     super().__init__(indata)


def parse_sui_object_type(indata: dict) -> SuiBaseType:
    """Parse an inbound JSON string to a Sui type."""
    split = indata["type"].split("::", 2)
    if split[0] == "0x2":
        return SuiGas(indata)
    else:
        return SuiBaseType(indata)
