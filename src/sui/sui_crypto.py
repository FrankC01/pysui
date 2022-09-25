"""Sui Crpto Utilities."""

import base64
import binascii
import hashlib
import secp256k1
from nacl.signing import SigningKey, VerifyKey
from nacl.encoding import Base64Encoder

from abstracts import KeyPair, PrivateKey, PublicKey, SignatureScheme
from sui.sui_excepts import SuiInvalidKeyPair, SuiInvalidKeystringLength
from sui import (
    SUI_KEYPAIR_LEN,
    ED25519_PUBLICKEY_BYTES_LEN,
    ED25519_PRIVATEKEY_BYTES_LEN,
    ED25519_KEYPAIR_BYTES_LEN,
    SECP256K1_KEYPAIR_BYTES_LEN,
    SECP256K1_PUBLICKEY_BYTES_LEN,
    SECP256K1_PRIVATEKEY_BYTES_LEN,
    SuiType,
)


# Edwards Curve Keys


class SuiPublicKeyED25519(PublicKey):
    """A ED25519 Public Key."""

    def __init__(self, indata: bytes) -> None:
        """Initialize public key."""
        if len(indata) != ED25519_PUBLICKEY_BYTES_LEN:
            raise SuiInvalidKeyPair(f"Public Key expects {ED25519_PUBLICKEY_BYTES_LEN} bytes, found {len(indata)}")
        super().__init__(SignatureScheme.ED25519, indata)
        self._verify_key = VerifyKey(self.to_b64(), encoder=Base64Encoder)


class SuiPrivateKeyED25519(PrivateKey):
    """A ED25519 Private Key."""

    def __init__(self, indata: bytes) -> None:
        """Initialize private key."""
        dlen = len(indata)
        if dlen != ED25519_PRIVATEKEY_BYTES_LEN:
            raise SuiInvalidKeyPair(f"Private Key expects {ED25519_PRIVATEKEY_BYTES_LEN} bytes, found {dlen}")
        super().__init__(SignatureScheme.ED25519, indata)
        self._signing_key = SigningKey(self.to_b64(), encoder=Base64Encoder)


class SuiKeyPairED25519(KeyPair):
    """A SuiKey Pair."""

    def __init__(self, pub_key_bytes: bytes, priv_key_bytes: bytes) -> None:
        """Init keypair with public and private byte array."""
        self._private_key = SuiPrivateKeyED25519(priv_key_bytes)
        self._public_key = SuiPublicKeyED25519(pub_key_bytes)

    def to_bytes(self) -> bytes:
        """Convert keypair to bytes."""
        all_bytes = (
            self._private_key.scheme.to_bytes(1, "little") + self._public_key.key_bytes + self._private_key.key_bytes
        )
        return all_bytes

    @classmethod
    def unique(cls) -> "SuiKeyPairED25519":
        """Generate a unique ED25519 keypair."""
        signer = SigningKey.generate()
        verifier = signer.verify_key
        return cls(verifier.__bytes__(), signer.__bytes__())

    @classmethod
    def from_b64(cls, indata: str) -> KeyPair:
        """Convert base64 string to keypair."""
        if len(indata) != SUI_KEYPAIR_LEN:
            raise SuiInvalidKeyPair(f"Expect str len of {SUI_KEYPAIR_LEN}")
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


# Secp256


class SuiPublicKeySECP256K1(PublicKey):
    """A SECP256K1 Public Key."""

    def __init__(self, indata: bytes) -> None:
        """Initialize public key."""
        if len(indata) != SECP256K1_PUBLICKEY_BYTES_LEN:
            raise SuiInvalidKeyPair(f"Public Key expects {SECP256K1_PUBLICKEY_BYTES_LEN} bytes, found {len(indata)}")
        super().__init__(SignatureScheme.SECP256K1, indata)
        self._verify_key = secp256k1.PublicKey(indata, raw=True)


class SuiPrivateKeySECP256K1(PrivateKey):
    """A SECP256K1 Private Key."""

    def __init__(self, indata: bytes) -> None:
        """Initialize private key."""
        if len(indata) != SECP256K1_PRIVATEKEY_BYTES_LEN:
            raise SuiInvalidKeyPair(f"Private Key expects {SECP256K1_PRIVATEKEY_BYTES_LEN} bytes, found {len(indata)}")
        super().__init__(SignatureScheme.SECP256K1, indata)
        self._signing_key = secp256k1.PrivateKey(indata, raw=True)


class SuiKeyPairSECP256K1(KeyPair):
    """A SuiKey Pair."""

    def __init__(self, pub_key_bytes: bytes, priv_key_bytes: bytes) -> None:
        """Init keypair with public and private byte array."""
        self._private_key = SuiPrivateKeySECP256K1(priv_key_bytes)
        self._public_key = SuiPublicKeySECP256K1(pub_key_bytes)

    def to_bytes(self) -> bytes:
        """Convert keypair to bytes."""
        all_bytes = (
            self._private_key.scheme.to_bytes(1, "little") + self._public_key.key_bytes + self._private_key.key_bytes
        )
        return all_bytes

    @classmethod
    def unique(cls) -> KeyPair:
        """Generate a unique secp256k1 keypair."""
        signer = secp256k1.PrivateKey()
        prv = signer.serialize()
        prvh = binascii.unhexlify(prv)
        print(f"s prv {prv} w len {len(prv)} and type {type(prv)} and hl {prvh}")
        pub = signer.pubkey.serialize()
        print(f"s pub {pub} w len {len(pub)}")

        return cls(signer.pubkey.serialize(compressed=True), signer.serialize())

    @classmethod
    def from_b64(cls, indata: str) -> KeyPair:
        """Convert base64 string to keypair."""
        if len(indata) != SUI_KEYPAIR_LEN:
            raise SuiInvalidKeyPair(f"Expect str len of {SUI_KEYPAIR_LEN}")
        base_decode = base64.b64decode(indata)
        if base_decode[0] == SignatureScheme.SECP256K1:
            return SuiKeyPairED25519.from_bytes(base_decode[1:])
        raise SuiInvalidKeyPair("Scheme not SECP256K1")

    @classmethod
    def from_bytes(cls, indata: bytes) -> KeyPair:
        """Convert bytes to keypair."""
        if len(indata) != SECP256K1_KEYPAIR_BYTES_LEN:
            raise SuiInvalidKeyPair("Expect bytes len of 65")
        return SuiKeyPairSECP256K1(indata[0:33], indata[33:])

    def __repr__(self) -> str:
        """To string."""
        return f"PubKey {self._public_key}, PrivKey {self._private_key}"


def keypair_from_keystring(address: str) -> KeyPair:
    """Derive keypair from address string."""
    if len(address) != SUI_KEYPAIR_LEN:
        raise SuiInvalidKeystringLength(len(address))
    addy_bytes = base64.b64decode(address)
    match addy_bytes[0]:
        case SignatureScheme.ED25519:
            return SuiKeyPairED25519.from_bytes(addy_bytes[1:])
        case SignatureScheme.SECP256K1:
            return SuiKeyPairSECP256K1.from_bytes(addy_bytes[1:])
    raise NotImplementedError


# Address


class SuiAddress(SuiType):
    """Sui Address Type."""

    def __init__(self, scheme: SignatureScheme, identifier: str) -> None:
        """Initialize address."""
        super().__init__(f"0x{identifier}")
        self._scheme = scheme

    @classmethod
    def from_bytes(cls, in_bytes: bytes) -> "SuiAddress":
        """Create address from bytes."""
        glg = hashlib.sha3_256()
        glg.update(in_bytes[0:33])
        hash_bytes = binascii.hexlify(glg.digest())[0:40]
        return SuiAddress(in_bytes[0], hash_bytes.decode("utf-8"))

    @property
    def scheme(self) -> str:
        """Get the address scheme."""
        return self._scheme


def address_from_keystring(indata: str) -> SuiAddress:
    """From a 88 byte keypair string create a SuiAddress."""
    #   Check address is legit keypair
    _kp = keypair_from_keystring(indata)
    #   decode from base64
    return SuiAddress.from_bytes(base64.b64decode(indata))
    # fromb64 = base64.b64decode(indata)
    # #   hash the scheme and public key
    # glg = hashlib.sha3_256()
    # glg.update(fromb64[0:33])
    # hash_bytes = binascii.hexlify(glg.digest())[0:40]
    # # Stringify
    # return SuiAddress(fromb64[0], hash_bytes.decode("utf-8"))


def create_new_keypair(keytype: SignatureScheme = SignatureScheme.ED25519) -> KeyPair:
    """Generate a new keypair."""
    match keytype:
        case SignatureScheme.ED25519:
            return SuiKeyPairED25519.unique()
        case SignatureScheme.SECP256K1:
            return SuiKeyPairSECP256K1.unique()
        case _:
            raise NotImplementedError


def create_new_address(keytype: SignatureScheme) -> tuple[KeyPair, SuiAddress]:
    """Create a new keypair and address for a key type."""
    new_kp = create_new_keypair(keytype)
    return (new_kp, SuiAddress.from_bytes(new_kp.to_bytes()))


if __name__ == "__main__":
    # TODO: Move to test for regression after secp256k1 working
    keyp, new_addy = create_new_address(SignatureScheme.ED25519)
    print(keyp)
    print(new_addy.identifer)
    # keyp, new_addy = create_new_address(SignatureScheme.SECP256K1)
    # print(keyp)
    # print(new_addy.identifer)
