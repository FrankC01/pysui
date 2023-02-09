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


"""Sui Crpto Keys and Keypairs."""

import base64
import hashlib
from typing import Union

import secp256k1
import bip_utils
import ecdsa
from bip_utils.addr.addr_key_validator import AddrKeyValidator
from bip_utils.bip.bip39.bip39_mnemonic_decoder import Bip39MnemonicDecoder
from bip_utils.utils.mnemonic.mnemonic_validator import MnemonicValidator
from nacl.signing import SigningKey, VerifyKey
from nacl.encoding import Base64Encoder, RawEncoder


from pysui.abstracts import KeyPair, PrivateKey, PublicKey, SignatureScheme
from pysui.sui.sui_excepts import SuiInvalidKeyPair, SuiInvalidKeystringLength
from pysui.sui.sui_constants import (
    SUI_KEYPAIR_LEN,
    ED25519_DEFAULT_KEYPATH,
    ED25519_PUBLICKEY_BYTES_LEN,
    ED25519_PRIVATEKEY_BYTES_LEN,
    ED25519_KEYPAIR_BYTES_LEN,
    SECP256K1_DEFAULT_KEYPATH,
    SECP256K1_KEYPAIR_BYTES_LEN,
    SECP256K1_PUBLICKEY_BYTES_LEN,
    SECP256K1_PRIVATEKEY_BYTES_LEN,
    SECP256R1_DEFAULT_KEYPATH,
    SECP256R1_KEYPAIR_BYTES_LEN,
    SECP256R1_PUBLICKEY_BYTES_LEN,
    SECP256R1_PRIVATEKEY_BYTES_LEN,
)

from pysui.sui.sui_types import SuiSignature, SuiAddress


class SuiPublicKey(PublicKey):
    """SuiPublicKey Sui Basic public key."""

    @property
    def pub_key(self) -> str:
        """Return self as base64 encoded string."""
        return self.to_b64()


class SuiPrivateKey(PrivateKey):
    """SuiPrivateKey Sui Basic private/signing key."""

    def sign_secure(self, public_key: SuiPublicKey, tx_data: str, recovery_id: int = 0) -> bytes:
        """sign_secure Sign transaction intent.

        :param public_key: PublicKey from signer/private key
        :type public_key: SuiPublicKey
        :param tx_data: Transaction bytes being signed
        :type tx_data: str
        :param recovery_id: value used for secp256r1 signature completion,default to 0
        :type: recovery_id: int, optional
        :return: Singed transaction as bytes
        :rtype: bytes
        """
        indata = bytearray([0, 0, 0])
        dec_tx = base64.b64decode(tx_data)
        indata.extend(dec_tx)
        compound = bytearray([self.scheme])
        sig_bytes = self.sign(bytes(indata), recovery_id)
        compound.extend(sig_bytes)
        compound.extend(public_key.key_bytes)
        return bytes(compound)


class SuiKeyPair(KeyPair):
    """SuiKeyPair Sui Basic keypair."""

    def __init__(self) -> None:
        """__init__ Default keypair initializer."""
        self._scheme: SignatureScheme = None
        self._private_key: SuiPrivateKey = None
        self._public_key: SuiPublicKey = None

    @property
    def private_key(self) -> SuiPrivateKey:
        """Return the Private Key."""
        return self._private_key

    @property
    def public_key(self) -> SuiPublicKey:
        """Return the Public Key."""
        return self._public_key

    @property
    def scheme(self) -> SignatureScheme:
        """Get the keys scheme."""
        return self._scheme

    def new_sign_secure(self, tx_data: str, recovery_id: int = 0) -> SuiSignature:
        """New secure sign with intent."""
        sig = self.private_key.sign_secure(self.public_key, tx_data, recovery_id)
        return SuiSignature(base64.b64encode(sig).decode())

    def serialize(self) -> str:
        """serialize Returns a SUI conforming keystring.

        :return: a base64 encoded string of schema and private key bytes
        :rtype: str
        """
        all_bytes = self.scheme.to_bytes(1, "little") + self.private_key.key_bytes
        return base64.b64encode(all_bytes).decode()

    def to_bytes(self) -> bytes:
        """Convert keypair to bytes."""
        all_bytes = self.scheme.to_bytes(1, "little") + self.public_key.key_bytes + self.private_key.key_bytes
        return all_bytes

    def __repr__(self) -> str:
        """To string."""
        return f"PubKey {self._public_key}, PrivKey {self._private_key}"


# Secp256r1 Curve Keys


class SuiPublicKeySECP256R1(SuiPublicKey):
    """A secp256r1 Public Key."""

    def __init__(self, indata: bytes) -> None:
        """Initialize public key."""
        if len(indata) != SECP256R1_PUBLICKEY_BYTES_LEN:
            raise SuiInvalidKeyPair(f"Public Key expects {SECP256R1_PUBLICKEY_BYTES_LEN} bytes, found {len(indata)}")
        super().__init__(SignatureScheme.SECP256R1, indata)
        self._verify_key = ecdsa.VerifyingKey.from_string(indata, curve=ecdsa.NIST256p, hashfunc=hashlib.sha256)


class SuiPrivateKeySECP256R1(SuiPrivateKey):
    """A secp256r1 Private Key."""

    def __init__(self, indata: bytes) -> None:
        """Initialize private key."""
        dlen = len(indata)
        if dlen != SECP256R1_PRIVATEKEY_BYTES_LEN:
            raise SuiInvalidKeyPair(f"Private Key expects {SECP256R1_PRIVATEKEY_BYTES_LEN} bytes, found {dlen}")
        super().__init__(SignatureScheme.SECP256R1, indata)
        self._signing_key = ecdsa.SigningKey.from_string(indata, ecdsa.NIST256p, hashfunc=hashlib.sha256)

    def sign(self, data: bytes, recovery_id: int = 0) -> bytes:
        """SECP256R1 sign data bytes."""
        core_sig = self._signing_key.sign_deterministic(data, hashfunc=hashlib.sha256)
        core_sig += recovery_id.to_bytes(1, "little")
        return core_sig


class SuiKeyPairSECP256R1(SuiKeyPair):
    """A SuiKey Pair."""

    def __init__(self, secret_bytes: bytes) -> None:
        """Init keypair with public and private byte array."""
        super().__init__()
        self._scheme = SignatureScheme.SECP256R1
        self._private_key = SuiPrivateKeySECP256R1(secret_bytes)
        pub_bytes = self._private_key._signing_key.get_verifying_key().to_string(encoding="compressed")
        self._public_key = SuiPublicKeySECP256R1(pub_bytes)

    @classmethod
    def from_b64(cls, indata: str) -> KeyPair:
        """Convert base64 string to keypair."""
        if len(indata) != SUI_KEYPAIR_LEN:
            raise SuiInvalidKeyPair(f"Expect str len of {SUI_KEYPAIR_LEN}")
        base_decode = base64.b64decode(indata)
        if base_decode[0] == SignatureScheme.SECP256R1:
            return SuiKeyPairED25519.from_bytes(base_decode[1:])
        raise SuiInvalidKeyPair("Scheme not ED25519")

    @classmethod
    def from_bytes(cls, indata: bytes) -> KeyPair:
        """Convert bytes to keypair."""
        if len(indata) != SECP256R1_KEYPAIR_BYTES_LEN:
            raise SuiInvalidKeyPair(f"Expect bytes len of {SECP256R1_KEYPAIR_BYTES_LEN}")
        return SuiKeyPairSECP256R1(indata)


class SuiPublicKeyED25519(SuiPublicKey):
    """A ED25519 Public Key."""

    def __init__(self, indata: bytes) -> None:
        """Initialize public key."""
        if len(indata) != ED25519_PUBLICKEY_BYTES_LEN:
            raise SuiInvalidKeyPair(f"Public Key expects {ED25519_PUBLICKEY_BYTES_LEN} bytes, found {len(indata)}")
        super().__init__(SignatureScheme.ED25519, indata)
        self._verify_key = VerifyKey(self.to_b64(), encoder=Base64Encoder)


class SuiPrivateKeyED25519(SuiPrivateKey):
    """A ED25519 Private Key."""

    def __init__(self, indata: bytes) -> None:
        """Initialize private key."""
        dlen = len(indata)
        if dlen != ED25519_PRIVATEKEY_BYTES_LEN:
            raise SuiInvalidKeyPair(f"Private Key expects {ED25519_PRIVATEKEY_BYTES_LEN} bytes, found {dlen}")
        super().__init__(SignatureScheme.ED25519, indata)
        self._signing_key = SigningKey(self.to_b64(), encoder=Base64Encoder)

    def sign(self, data: bytes, _recovery_id: int = 0) -> bytes:
        """ED25519 sign data bytes."""
        sig = self._signing_key.sign(data, encoder=RawEncoder).signature
        return sig


class SuiKeyPairED25519(SuiKeyPair):
    """A SuiKey Pair."""

    def __init__(self, secret_bytes: bytes) -> None:
        """Init keypair with public and private byte array."""
        super().__init__()
        self._scheme = SignatureScheme.ED25519
        self._private_key = SuiPrivateKeyED25519(secret_bytes)
        pub_bytes = self._private_key._signing_key.verify_key
        self._public_key = SuiPublicKeyED25519(pub_bytes.encode())

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
            raise SuiInvalidKeyPair(f"Expect bytes len of {ED25519_KEYPAIR_BYTES_LEN}")
        return SuiKeyPairED25519(indata)


# Secp256
# TODO: Change to use the ecdsa library and drop the secp256k1 library requirement


class SuiPublicKeySECP256K1(SuiPublicKey):
    """A SECP256K1 Public Key."""

    def __init__(self, indata: bytes) -> None:
        """Initialize public key."""
        if len(indata) != SECP256K1_PUBLICKEY_BYTES_LEN:
            raise SuiInvalidKeyPair(f"Public Key expects {SECP256K1_PUBLICKEY_BYTES_LEN} bytes, found {len(indata)}")
        super().__init__(SignatureScheme.SECP256K1, indata)
        self._verify_key = secp256k1.PublicKey(indata, raw=True)


# TODO: Change to use the ecdsa library
class SuiPrivateKeySECP256K1(SuiPrivateKey):
    """A SECP256K1 Private Key."""

    def __init__(self, indata: bytes) -> None:
        """Initialize private key."""
        if len(indata) != SECP256K1_PRIVATEKEY_BYTES_LEN:
            raise SuiInvalidKeyPair(f"Private Key expects {SECP256K1_PRIVATEKEY_BYTES_LEN} bytes, found {len(indata)}")
        super().__init__(SignatureScheme.SECP256K1, indata)
        self._signing_key = secp256k1.PrivateKey(indata, raw=True)

    def sign(self, data: bytes, _recovery_id: int = 0) -> bytes:
        """secp256k1 sign data bytes."""
        return self._signing_key.ecdsa_serialize_compact(self._signing_key.ecdsa_sign(data))


# TODO: Change to use the ecdsa library
class SuiKeyPairSECP256K1(SuiKeyPair):
    """A SuiKey Pair."""

    def __init__(self, secret_bytes: bytes) -> None:
        """Init keypair with public and private byte array."""
        super().__init__()
        self._scheme = SignatureScheme.SECP256K1
        self._private_key = SuiPrivateKeySECP256K1(secret_bytes)
        pubkey_bytes = self._private_key._signing_key.pubkey.serialize(compressed=True)
        self._public_key = SuiPublicKeySECP256K1(pubkey_bytes)

    @classmethod
    def from_b64(cls, indata: str) -> KeyPair:
        """Convert base64 string to keypair."""
        if len(indata) != SUI_KEYPAIR_LEN:
            raise SuiInvalidKeyPair(f"Expect str len of {SUI_KEYPAIR_LEN}")
        base_decode = base64.b64decode(indata)
        if base_decode[0] == SignatureScheme.SECP256K1:
            return SuiKeyPairSECP256K1.from_bytes(base_decode[1:])
        raise SuiInvalidKeyPair("Scheme not SECP256K1")

    @classmethod
    def from_bytes(cls, indata: bytes) -> KeyPair:
        """Convert bytes to keypair."""
        if len(indata) != SECP256K1_KEYPAIR_BYTES_LEN:
            raise SuiInvalidKeyPair("Expect bytes len of 65")
        return SuiKeyPairSECP256K1(indata)


# Utility functions
def _valid_mnemonic(key_type: SignatureScheme, mnemonics: Union[str, list[str]] = "") -> str:
    """_valid_mnemonic Validate, or create, mnemonic word string.

    :param mnemonics: space separated word string (12) or list of words(12), defaults to ""
    :type mnemonics: Union[str, list[str]], optional
    :raises ValueError: If the validation of supplied mnemonics fails
    :return: mnemonic word (12) string separated by spaces
    :rtype: str
    """
    if mnemonics:
        if isinstance(mnemonics, list):
            mnemonics = " ".join(mnemonics)

        if MnemonicValidator(Bip39MnemonicDecoder()).IsValid(mnemonics):
            return mnemonics
        raise ValueError(f"{mnemonics} is not a valid mnemonic phrase.")
    match key_type:
        case SignatureScheme.ED25519 | SignatureScheme.SECP256K1:
            return bip_utils.Bip39MnemonicGenerator().FromWordsNumber(bip_utils.Bip39WordsNum.WORDS_NUM_12).ToStr()
        case SignatureScheme.SECP256R1:
            return bip_utils.Bip39MnemonicGenerator().FromWordsNumber(bip_utils.Bip39WordsNum.WORDS_NUM_24).ToStr()
        case _:
            raise ValueError(f"{key_type} is not a valid key signature scheme type.")


def _valid_pubkey(key_valmethod: str, pub_key: bytes) -> Union[None, TypeError, ValueError]:
    """_valid_pubkey Validate the public key.

    Public key bytes may be from secp256k1 or ed25519

    :param key_valmethod: Validator for keytype string
    :type key_valmethod: str
    :param pub_key: Public key bytes
    :type pub_key: bytes
    :raises TypeError: Invalid public key
    :raises ValueError: Invalid public key
    :return: None for valid public key
    :rtype: Union[None, TypeError, ValueError]
    """
    try:
        getattr(AddrKeyValidator, key_valmethod)(pub_key)
    except TypeError as texc:
        raise texc
    except ValueError as vexc:
        raise vexc


# TODO: Change to use the ecdsa library
def _generate_secp256k1(
    mnemonics: Union[str, list[str]] = "", derv_path: str = None
) -> tuple[str, SuiKeyPairSECP256K1]:
    """_generate_secp256k1 Create a mnemonic seed and use derivation path for secp256k1 keypair.

    :param mnemonics: _description_, defaults to ""
    :type mnemonics: Union[str, list[str]], optional
    :param derv_path: _description_, defaults to None
    :type derv_path: str, optional
    :return: _description_
    :rtype: KeyPair
    """
    mnemonic_phrase = _valid_mnemonic(SignatureScheme.SECP256K1, mnemonics)
    derv_path = derv_path or SECP256K1_DEFAULT_KEYPATH
    # Generate seed from mnemonic phrase and optional password
    seed_bytes = bip_utils.Bip39SeedGenerator(mnemonic_phrase).Generate()
    bip32_ctx = bip_utils.Bip32Slip10Secp256k1.FromSeedAndPath(seed_bytes, derv_path)
    # Get private key bytes list
    prv_key = bip32_ctx.PrivateKey().Raw().ToBytes()
    # Instantiate secp256k1 library keypair
    # 1. Private, or signer, key
    secp_priv = secp256k1.PrivateKey(prv_key, raw=True)
    # 2. Public, or verifier, key
    _valid_pubkey("ValidateAndGetSecp256k1Key", secp_priv.pubkey.serialize(compressed=True))
    return mnemonic_phrase, SuiKeyPairSECP256K1(secp_priv.private_key)


def _generate_secp256r1(
    mnemonics: Union[str, list[str]] = "", derv_path: str = None
) -> tuple[str, SuiKeyPairSECP256R1]:
    """_generate_secp256r1 Create a mnemonic seed and use derivation path for secp256r1 keypair.

    :param mnemonics: _description_, defaults to ""
    :type mnemonics: Union[str, list[str]], optional
    :param derv_path: _description_, defaults to None
    :type derv_path: str, optional
    :return: _description_
    :rtype: KeyPair
    """
    mnemonic_phrase = _valid_mnemonic(SignatureScheme.SECP256R1, mnemonics)
    derv_path = derv_path or SECP256R1_DEFAULT_KEYPATH
    # Generate seed from mnemonic phrase and optional password
    seed_bytes = bip_utils.Bip39SeedGenerator(mnemonic_phrase).Generate()
    bip32_ctx = bip_utils.Bip32Slip10Nist256p1.FromSeedAndPath(seed_bytes, derv_path)
    # Get private key bytes list
    prv_key = bip32_ctx.PrivateKey().Raw().ToBytes()
    # Instantiate secp256k1 library keypair
    # 1. Private, or signer, key
    secp_priv = ecdsa.SigningKey.from_string(prv_key, curve=ecdsa.NIST256p)
    # 2. Public, or verifier, key
    _valid_pubkey("ValidateAndGetNist256p1Key", secp_priv.get_verifying_key().to_string("compressed"))
    return mnemonic_phrase, SuiKeyPairSECP256R1(secp_priv.to_string())


def _generate_ed25519(mnemonics: Union[str, list[str]] = "", derv_path: str = None) -> tuple[str, SuiKeyPairED25519]:
    """_generate_secp256k1 Create a mnemonic seed and use derivation path for ed25519 keypair.

    :param mnemonics: _description_, defaults to ""
    :type mnemonics: Union[str, list[str]], optional
    :param derv_path: _description_, defaults to None
    :type derv_path: str, optional
    :return: _description_
    :rtype: KeyPair
    """
    mnemonic_phrase = _valid_mnemonic(SignatureScheme.ED25519, mnemonics)
    derv_path = derv_path or ED25519_DEFAULT_KEYPATH
    # Generate seed from mnemonic phrase and optional password
    seed_bytes = bip_utils.Bip39SeedGenerator(mnemonic_phrase).Generate()
    bip32_ctx = bip_utils.Bip32Slip10Ed25519.FromSeedAndPath(seed_bytes, derv_path)
    # Get private key bytes list
    prv_key = bip32_ctx.PrivateKey().Raw().ToBytes()
    # Instantiate ed25519 library keypair
    # Private, or signer, key
    ed_priv = SigningKey(base64.b64encode(prv_key), encoder=Base64Encoder)
    ed_enc_prv = ed_priv.encode()
    # Public, or verifier, key
    _valid_pubkey("ValidateAndGetEd25519Key", ed_priv.verify_key.encode())
    return mnemonic_phrase, SuiKeyPairED25519(ed_enc_prv)


def keypair_from_keystring(keystring: str) -> KeyPair:
    """keypair_from_keystring Parse keystring to keypair.

    :param keystring: base64 keystring
    :type keystring: str
    :raises SuiInvalidKeystringLength: If invalid keypair string length
    :raises NotImplementedError: If invalid keytype signature in string
    :return: keypair derived from keystring
    :rtype: KeyPair
    """
    if len(keystring) != SUI_KEYPAIR_LEN:
        raise SuiInvalidKeystringLength(len(keystring))
    addy_bytes = base64.b64decode(keystring)
    match addy_bytes[0]:
        case SignatureScheme.ED25519:
            return SuiKeyPairED25519.from_bytes(addy_bytes[1:])
        case SignatureScheme.SECP256K1:
            return SuiKeyPairSECP256K1.from_bytes(addy_bytes[1:])
        case SignatureScheme.SECP256R1:
            return SuiKeyPairSECP256R1.from_bytes(addy_bytes[1:])
    raise NotImplementedError


def create_new_keypair(
    keytype: SignatureScheme = SignatureScheme.ED25519, mnemonics: Union[str, list[str]] = None, derv_path: str = None
) -> tuple[str, KeyPair]:
    """create_new_keypair Generate a new keypair.

    :param keytype: One of ED25519, SECP256K1 or SECP256R1 key type, defaults to SignatureScheme.ED25519
    :type keytype: SignatureScheme, optional
    :param mnemonics: mnemonic words, defaults to None
    :type mnemonics: Union[str, list[str]], optional
    :param derv_path: derivation path coinciding with key type, defaults to None
    :type derv_path: str, optional
    :raises NotImplementedError: If invalid keytype is provided
    :return: mnemonic words and new keypair
    :rtype: tuple[str, KeyPair]
    """
    match keytype:
        case SignatureScheme.ED25519:
            return _generate_ed25519(mnemonics, derv_path)
        case SignatureScheme.SECP256K1:
            return _generate_secp256k1(mnemonics, derv_path)
        case SignatureScheme.SECP256R1:
            return _generate_secp256r1(mnemonics, derv_path)
        case _:
            raise NotImplementedError


def create_new_address(
    keytype: SignatureScheme, mnemonics: Union[str, list[str]] = None, derv_path: str = None
) -> tuple[str, KeyPair, SuiAddress]:
    """create_new_address Create a new keypair and address for a key type.

    :param keytype: One of ED25519, SECP256K1 or SECP256R1 key type
    :type keytype: SignatureScheme
    :param mnemonics: mnemonic words, defaults to None
    :type mnemonics: Union[str, list[str]], optional
    :param derv_path: derivation path coinciding with key type, defaults to None
    :type derv_path: str, optional
    :return: mnemonic words, new keypair and derived sui address
    :rtype: tuple[str, KeyPair, SuiAddress]
    """
    mnem, new_kp = create_new_keypair(keytype, mnemonics, derv_path)
    return mnem, new_kp, SuiAddress.from_bytes(new_kp.to_bytes())


def recover_key_and_address(
    keytype: SignatureScheme, mnemonics: Union[str, list[str]], derv_path: str
) -> tuple[str, KeyPair, SuiAddress]:
    """recover_key_and_address Recover a keypair and address.

    :param keytype: One of ED25519 or SECP256K1 key type for the original key
    :type keytype: SignatureScheme
    :param mnemonics: mnemonic words used when creating original keypair
    :type mnemonics: Union[str, list[str]]
    :param derv_path: derivation path used when creating original keypair
    :type derv_path: str
    :return: mnemonic words, recovered keypair and derived sui address
    :rtype: tuple[str, KeyPair, SuiAddress]
    """
    mnem, new_kp = create_new_keypair(keytype, mnemonics, derv_path)
    return mnem, new_kp, SuiAddress.from_bytes(new_kp.to_bytes())


# pylint:disable=line-too-long,invalid-name
if __name__ == "__main__":
    pass
