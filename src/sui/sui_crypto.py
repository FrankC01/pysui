"""Sui Crpto Utilities."""

import base64
from nacl.signing import SigningKey
from nacl.signing import VerifyKey
from nacl.encoding import Base64Encoder

from abstracts import KeyPair, PrivateKey, PublicKey, SignatureScheme
from sui.sui_excepts import SuiInvalidKeyPair

B64_ADDRESS_LEN = 88
B64_KEYPAIR_LEN = 87
ED25519_KEYPAIR_BYTES_LEN = 64
ED25519_KEY_BYTES_LEN = 32


class SuiPublicKeyED25519(PublicKey):
    """A ED25519 Public Key."""

    def __init__(self, indata: bytes) -> None:
        """Initialize public key."""
        if len(indata) != ED25519_KEY_BYTES_LEN:
            raise SuiInvalidKeyPair(f"Expect bytes len of {ED25519_KEY_BYTES_LEN} found {len(indata)}")
        super().__init__(SignatureScheme.ED25519, indata)
        self._verify_key = VerifyKey(self.to_b64(), encoder=Base64Encoder)


class SuiPrivateKeyED25519(PrivateKey):
    """A ED25519 Public Key."""

    def __init__(self, indata: bytes) -> None:
        """Initialize private key."""
        if len(indata) != ED25519_KEY_BYTES_LEN:
            raise SuiInvalidKeyPair(f"Expect bytes len of {ED25519_KEY_BYTES_LEN} found {len(indata)}")
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
        raise SuiInvalidKeyPair(f"Expect str len of {B64_ADDRESS_LEN}")
    addy_bytes = base64.b64decode(address)
    if addy_bytes[0] == SignatureScheme.ED25519:
        return SuiKeyPairED25519.from_bytes(addy_bytes[1:])
    raise NotImplementedError
