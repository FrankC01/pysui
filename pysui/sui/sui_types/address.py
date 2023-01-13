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

"""Sui Address Type."""

import base64
import binascii
import hashlib
import re
from typing import Union
from pysui.abstracts import SuiBaseType
from pysui.sui.sui_types.scalars import SuiString
from pysui.sui.sui_constants import SUI_ADDRESS_STRING_LEN, SUI_HEX_ADDRESS_STRING_LEN
from pysui.sui.sui_excepts import SuiInvalidAddress

__partstring_pattern: re.Pattern = re.compile(r"[0-9a-fA-F]{38}")
__fullstring_pattern: re.Pattern = re.compile(r"0[xX][0-9a-fA-F]{40}")


def valid_sui_address(instr: str) -> bool:
    """Verify Sui address string."""
    inlen = len(instr)
    match instr:
        case "0x2" | "Immutable":
            return True
        case _:
            if inlen > SUI_HEX_ADDRESS_STRING_LEN or inlen < SUI_ADDRESS_STRING_LEN:
                return False
            # _kp = keypair_from_keystring(instr)
            if inlen == SUI_HEX_ADDRESS_STRING_LEN and __fullstring_pattern.findall(instr):
                return True
            return __partstring_pattern.findall(instr)


class SuiAddress(SuiBaseType):
    """Sui Address Type."""

    def __init__(self, identifier: Union[SuiString, str]) -> None:
        """Initialize address."""
        testvalid: str = identifier if isinstance(identifier, str) else identifier.value
        if valid_sui_address(testvalid):
            testvalid = testvalid if testvalid.startswith("0x") else format(f"0x{testvalid}")
            super().__init__(SuiString(testvalid))
        else:
            raise ValueError(f"{testvalid} is not valid address string")
        # Alias for transaction validation
        self.address = testvalid

    @property
    def signer(self) -> str:
        """Alias for signer in transaction validation."""
        return self.address

    @property
    def owner(self) -> str:
        """Alias for signer in transaction validation."""
        return self.address

    @property
    def sender(self) -> str:
        """Alias for signer in transaction validation."""
        return self.address

    @property
    def sender_address(self) -> str:
        """Alias for sender in transaction validation."""
        return self.address

    @property
    def recipient(self) -> str:
        """Alias for recipient in transaction validation."""
        return self.address

    @property
    def recipients(self) -> str:
        """Alias for recipients in transaction validation."""
        return self.address

    @classmethod
    def from_hex_string(cls, instr: Union[str, SuiString]) -> "SuiAddress":
        """Instantiate instance of SuiAddress from hex string."""
        instr = instr if isinstance(instr, str) else str(instr)
        if valid_sui_address(instr):
            return cls(instr)
        raise SuiInvalidAddress(f"{instr} is not a valid address string.")

    @classmethod
    def from_keypair_string(cls, keystring: str) -> "SuiAddress":
        """Address from base64 encoded keypair string with no validation."""
        return cls.from_bytes(base64.b64decode(keystring))

    @classmethod
    def from_bytes(cls, in_bytes: bytes) -> "SuiAddress":
        """Create address from bytes."""
        digest = in_bytes[0:33] if in_bytes[0] == 0 else in_bytes[0:34]
        glg = hashlib.sha3_256()
        glg.update(digest)
        hash_bytes = binascii.hexlify(glg.digest())[0:40]
        return cls(hash_bytes.decode("utf-8"))


def address_from_keystring(indata: str) -> SuiAddress:
    """From a 88 byte keypair string create a SuiAddress."""
    #   Check address is legit keypair
    from pysui.sui.sui_crypto import keypair_from_keystring

    _kp = keypair_from_keystring(indata)
    #   decode from base64 and generate
    return SuiAddress.from_bytes(_kp.to_bytes())
