"""Sui Crpto Utilities."""

import base64
import binascii
import hashlib
from nacl.signing import SigningKey
from nacl.signing import VerifyKey
from nacl.encoding import Base64Encoder

from abstracts import KeyPair, PrivateKey, PublicKey, SignatureScheme
from sui.sui_excepts import SuiInvalidKeyPair, SuiInvalidKeystringLength
from sui import (
    B64_ADDRESS_LEN,
    ED25519_PUBLICKEY_BYTES_LEN,
    ED25519_PRIVATEKEY_BYTES_LEN,
    ED25519_KEYPAIR_BYTES_LEN,
    SuiType,
)


class SuiPublicKeyED25519(PublicKey):
    """A ED25519 Public Key."""

    def __init__(self, indata: bytes) -> None:
        """Initialize public key."""
        if len(indata) != ED25519_PUBLICKEY_BYTES_LEN:
            raise SuiInvalidKeyPair(f"Public Key expects {ED25519_PUBLICKEY_BYTES_LEN} bytes, found {len(indata)}")
        super().__init__(SignatureScheme.ED25519, indata)
        self._verify_key = VerifyKey(self.to_b64(), encoder=Base64Encoder)


class SuiPrivateKeyED25519(PrivateKey):
    """A ED25519 Public Key."""

    def __init__(self, indata: bytes) -> None:
        """Initialize private key."""
        if len(indata) != ED25519_PRIVATEKEY_BYTES_LEN:
            raise SuiInvalidKeyPair(f"Private Key expects {ED25519_PRIVATEKEY_BYTES_LEN} bytes, found {len(indata)}")
        super().__init__(SignatureScheme.ED25519, indata)
        self._signing_key = SigningKey(self.to_b64(), encoder=Base64Encoder)


class SuiKeyPairED25519(KeyPair):
    """A SuiKey Pair."""

    def __init__(self, pub_key_bytes: bytes, priv_key_bytes: bytes) -> None:
        """Init keypair with public and private byte array."""
        self._private_key = SuiPrivateKeyED25519(priv_key_bytes)
        self._public_key = SuiPublicKeyED25519(pub_key_bytes)

    @classmethod
    def from_b64(cls, indata: str) -> KeyPair:
        """Convert base64 string to keypair."""
        if len(indata) != B64_ADDRESS_LEN:
            raise SuiInvalidKeyPair(f"Expect str len of {B64_ADDRESS_LEN}")
        base_decode = base64.b64decode(indata)
        if base_decode[0] == SignatureScheme.ED25519:
            return SuiKeyPairED25519.from_bytes(base_decode[1:])
        raise SuiInvalidKeyPair("Scheme not ED25519")

    @classmethod
    def from_bytes(cls, indata: bytes) -> KeyPair:
        """Convert bytes to keypair."""
        if len(indata) != ED25519_KEYPAIR_BYTES_LEN:
            raise SuiInvalidKeyPair("Expect bytes len of 64")
        return SuiKeyPairED25519(indata[0:32], indata[32:])

    def __repr__(self) -> str:
        """To string."""
        return f"PubKey {self._public_key}, PrivKey {self._private_key}"


def keypair_from_b64address(address: str) -> KeyPair:
    """Derive keypair from address string."""
    if len(address) != B64_ADDRESS_LEN:
        raise SuiInvalidKeystringLength(len(address))
    addy_bytes = base64.b64decode(address)
    if addy_bytes[0] == SignatureScheme.ED25519:
        return SuiKeyPairED25519.from_bytes(addy_bytes[1:])
    raise NotImplementedError


class SuiAddress(SuiType):
    """Sui Address Type."""

    def __init__(self, scheme: SignatureScheme, identifier: str) -> None:
        """Initialize address."""
        super().__init__(f"0x{identifier}")
        self._scheme = scheme

    @property
    def scheme(self) -> str:
        """Get the address scheme."""
        return self._scheme


def address_from_keystring(indata: str) -> SuiAddress:
    """From a 88 byte keypair string create a SuiAddress."""
    #   Check address is legit keypair
    _kp = keypair_from_b64address(indata)
    #   decode from base64
    fromb64 = base64.b64decode(indata)
    #   Check valid encoding (0 or 1)
    #   hash the scheme and public key
    glg = hashlib.sha3_256()
    glg.update(fromb64[0:33])
    hash_bytes = binascii.hexlify(glg.digest())[0:40]
    # Stringify
    return SuiAddress(fromb64[0], hash_bytes.decode("utf-8"))
