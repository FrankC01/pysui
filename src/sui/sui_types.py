"""Sui Types."""

from abstracts import ClientTypeDescriptor


class SuiTypeDescriptor(ClientTypeDescriptor):
    """Base SUI Type."""

    def __init__(self, indata: dict) -> None:
        """Initialize the base."""
        self._identifier = indata["objectId"]
        self._version = indata["version"]
        self._owner = indata["owner"]["AddressOwner"]
        self._digest = indata["digest"]
        self._previous_txn = indata["previousTransaction"]
        self._type_signature = indata["type"]

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

    @property
    def type_signature(self):
        """Return the types type."""
        return self._type_signature


class SuiObjectDescriptor(SuiTypeDescriptor):
    """Sui Object base type."""


class SuiNftDescriptor(SuiObjectDescriptor):
    """Sui NFT base type."""


class SuiCoinDescriptor(SuiObjectDescriptor):
    """Sui Coin but not necessarily gas."""

    # def __init__(self, indata: dict) -> None:
    #     """Initialize a Sui coint object."""
    #     super().__init__(indata)


class SuiNativeCoinDescriptor(SuiCoinDescriptor):
    """Sui gas is a coin."""

    # def __init__(self, indata: dict) -> None:
    #     """Initialize a Sui gas object."""
    #     super().__init__(indata)


def parse_sui_object_descriptors(indata: dict) -> SuiTypeDescriptor:
    """Parse an inbound JSON string to a Sui type."""
    split = indata["type"].split("::", 2)

    if split[0] == "0x2":
        match split[1]:
            case "coin":
                split2 = split[2][5:-1].split("::")
                if split2[2] == "SUI":
                    return SuiNativeCoinDescriptor(indata)
                return SuiCoinDescriptor(indata)
            case "devnet_nft":
                if split[2] == "DevNetNFT":
                    return SuiNftDescriptor(indata)
    return SuiObjectDescriptor(indata)
