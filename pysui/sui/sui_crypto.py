#    Copyright Frank V. Castellucci
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

import os
import ast
import base64
import binascii
import hashlib
import subprocess
import json
from typing import Union
from deprecated.sphinx import versionadded, versionchanged

import secp256k1
import bip_utils
import ecdsa
from bip_utils.addr.addr_key_validator import AddrKeyValidator
from bip_utils.bip.bip39.bip39_mnemonic_decoder import Bip39MnemonicDecoder
from bip_utils.utils.mnemonic.mnemonic_validator import MnemonicValidator
from nacl.signing import SigningKey, VerifyKey
from nacl.encoding import Base64Encoder, RawEncoder


from pysui.abstracts import KeyPair, PrivateKey, PublicKey, SignatureScheme
from pysui.sui.sui_excepts import (
    SuiFileNotFound,
    SuiInvalidKeyPair,
    SuiInvalidKeystringLength,
    SuiKeystoreAddressError,
    SuiKeystoreFileError,
    SuiNoKeyPairs,
)
from pysui.sui.sui_constants import (
    PYSUI_EXEC_ENV,
    SCHEME_PRIVATE_KEY_BYTE_LEN,
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
from pysui.sui.sui_types.scalars import SuiTxBytes

_SUI_MS_SIGN_CMD: list[str] = ["keytool", "multi-sig-combine-partial-sig"]
"""Use sui binary keytool for MultiSig signing."""


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
        # Sign hash of transaction intent
        indata = bytearray([0, 0, 0])
        indata.extend(base64.b64decode(tx_data))
        sig_bytes = self.sign(hashlib.blake2b(indata, digest_size=32).digest(), recovery_id)
        # Embelish results
        # flag | sig | public_key
        compound = bytearray([self.scheme])
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

    def new_sign_secure(self, tx_data: Union[str, SuiTxBytes]) -> SuiSignature:
        """New secure sign with intent."""
        tx_data = tx_data if isinstance(tx_data, str) else tx_data.value
        sig = self.private_key.sign_secure(self.public_key, tx_data)
        return SuiSignature(base64.b64encode(sig).decode())

    def serialize(self) -> str:
        """serialize Returns a SUI conforming keystring.

        :return: a base64 encoded string of schema and private key bytes
        :rtype: str
        """
        all_bytes = self.scheme.to_bytes(1, "little") + self.private_key.key_bytes
        return base64.b64encode(all_bytes).decode()

    def serialize_to_bytes(self) -> bytes:
        """serialize_to_bytes Returns a SUI conforming keystring as bytes.

        :return: Bytes of signature scheme + private key
        :rtype: bytes
        """
        return self.scheme.to_bytes(1, "little") + self.private_key.key_bytes

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
        """SECP256R1 signing bytes."""

        def _sigencode_string(r_int: int, s_int: int, order: int) -> bytes:
            """s adjustment to go small."""
            _s_max = 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551
            if s_int > _s_max / 2:
                s_int = _s_max - s_int
            return ecdsa.util.sigencode_string(r_int, s_int, order)

        return self._signing_key.sign_deterministic(data, hashfunc=hashlib.sha256, sigencode=_sigencode_string)


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
        return self._signing_key.sign(data, encoder=RawEncoder).signature


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


class MultiSig:
    """."""

    _MIN_KEYS: int = 2
    _MAX_KEYS: int = 10
    _MAX_WEIGHT: int = 255
    _MAX_THRESHOLD: int = 65535
    _SIGNATURE_SCHEME: SignatureScheme = SignatureScheme.MULTISIG

    def __init__(self, suikeys: list[SuiKeyPair], weights: list[int], threshold: int):
        """__init__ Initiate a MultiSig object.

        Note that Sui multi-sig accepts up to a maximum of ten (10) individual signer keys.

        :param suikeys: The list of keys participating in the multi-sig signing operations.
        :type suikeys: list[SuiKeyPair]
        :param weights: Corresponding weights for each key. Max value of each weight is 255 (8 bit unsigned)
        :type weights: list[int]
        :param threshold: The threshold criteria for this MultiSig. Max value is 65,535 (16 bit unsigned)
        :type threshold: int
        """
        if (
            len(suikeys) in range(self._MIN_KEYS, self._MAX_KEYS)
            and len(suikeys) == len(weights)
            and threshold <= self._MAX_THRESHOLD
            and max(weights) <= self._MAX_WEIGHT
        ):
            self._keys: list[SuiKeyPair] = suikeys
            self._weights: list[int] = weights
            self._threshold: int = threshold
            self._schema: SignatureScheme = SignatureScheme.MULTISIG
            self._address: SuiAddress = self._multi_sig_address()
            self._public_keys: list[SuiPublicKey] = [x.public_key for x in self._keys]
        else:
            raise ValueError("Invalid arguments provided to constructor")

    def _multi_sig_address(self) -> SuiAddress:
        """multi_sig_address Generates the unique address derived from the keys in the MultiSig.

        :return: A unique address that can be used to participate as recipeint and sender in transactions.
        :rtype: SuiAddress
        """
        # Build the digest to generate a SuiAddress (hash) from
        digest = self._schema.to_bytes(1, "little")
        digest += self._threshold.to_bytes(2, "little")
        for index, kkeys in enumerate(self._keys):
            digest += kkeys.public_key.scheme_and_key()
            digest += self._weights[index].to_bytes(1, "little")
        return SuiAddress(hashlib.blake2b(digest, digest_size=32).hexdigest())

    @property
    def scheme(self) -> SignatureScheme:
        """Return the MultiSig signature scheme."""
        return self._SIGNATURE_SCHEME

    @property
    @versionchanged(version="0.16.1", reason="Return add as str to align with non MultiSig SuiAddress behavior")
    def address(self) -> str:
        """Return the address string generated from the initial keys."""
        return self._address.address

    @property
    @versionadded(version="0.16.1", reason="Provide ability to get MultiSig as SuiAddress")
    def as_sui_address(self) -> SuiAddress:
        """Return the address as SuiAddress."""
        return self._address

    @property
    def public_keys(self) -> list[SuiPublicKey]:
        """Return a copy of the list of SuiPublicKeys used in this MultiSig."""
        return self._public_keys.copy()

    @property
    def weights(self) -> list[int]:
        """Return a copy of the list of weights used in this MultiSig."""
        return self._weights.copy()

    @property
    def threshold(self) -> int:
        """Return the threshold amount used in this MultiSig."""
        return self._threshold

    def _validate_signers(self, pub_keys: list[SuiPublicKey]) -> list[int]:
        """Validate pubkeys part of multisig and have enough weight."""
        # Must be subset of full ms list
        if len(pub_keys) <= len(self._public_keys):
            hit_indexes = [i for i, j in enumerate(pub_keys) if j in self._public_keys]
            # If all inbound pubkeys have reference to item in ms list
            if len(hit_indexes) == len(pub_keys):
                if sum([self._weights[x] for x in hit_indexes]) >= self._threshold:
                    return hit_indexes
        return None

    def sign(self, tx_bytes: Union[str, SuiTxBytes], pub_keys: list[SuiPublicKey]) -> Union[int, SuiSignature]:
        """sign Signs transaction bytes for operation that changes objects owned by MultiSig address.

        :param tx_bytes: Transaction bytes base64 string from 'unsafe...' result or Transaction BCS
        :type tx_bytes: Union[str, SuiTxBytes]
        :param pub_keys: List of SuiPublicKeys to sign the transaction bytes
        :type pub_keys: list[SuiPublicKey]
        :raises ValueError: If pubkeys fail verification as member of MultiSig or threshold constraint
        :return: The new signature produced from MultiSig
        :rtype: SuiSignature
        """
        # Validate the pub_keys align to self._keys
        key_indx = self._validate_signers(pub_keys)
        if key_indx:
            tx_bytes = tx_bytes if isinstance(tx_bytes, str) else tx_bytes.value
            # Build the command line for `sui keytool multi-sig-combine-partial-sig`
            # Public keys of all keys
            pk_args = ["--pks"]
            pk_args.extend([base64.b64encode(x.public_key.scheme_and_key()).decode() for x in self._keys])
            # all weights
            weight_args = ["--weights"]
            weight_args.extend([str(x) for x in self._weights])
            # all threshold
            threshold_args = ["--threshold", str(self._threshold)]
            # Get the signatures
            sig_args = ["--sigs"]
            sig_args.extend([self._keys[x].new_sign_secure(tx_bytes).value for x in key_indx])
            # Build command line
            invoke_args = _SUI_MS_SIGN_CMD.copy()
            invoke_args.insert(0, os.environ[PYSUI_EXEC_ENV])
            invoke_args.extend(pk_args)
            invoke_args.extend(weight_args)
            invoke_args.extend(threshold_args)
            invoke_args.extend(sig_args)
            # Invoke signing
            result = subprocess.run(invoke_args, capture_output=True, text=True)
            if result.returncode == 0:
                sargs = ast.literal_eval(result.stdout.split()[-1])
                return SuiSignature(sargs)
            return result.returncode
        raise ValueError("Invalid signer pub_keys")

    def serialize(self) -> str:
        """serialize Serializes the MultiSig object to base64 string.

        :return: Base64 string of serialized MultiSig
        :rtype: str
        """
        # Build from scheme and counts,keystrings,weights and threshold
        all_bytes = self.scheme.to_bytes(1, "little") + len(self._keys).to_bytes(1, "little")
        for key in self._keys:
            all_bytes += key.serialize_to_bytes()
        for assoc_weight in self._weights:
            all_bytes += assoc_weight.to_bytes(2, "little")
        all_bytes += self._threshold.to_bytes(2, "little")
        return base64.b64encode(all_bytes).decode()

    @classmethod
    def deserialize(cls, ser_str: str) -> Union[ValueError, "MultiSig"]:
        """deserialize Deserializes a MultSig base64 string to object instance.

        :param ser_str: base64 encoded string
        :type ser_str: str
        :raises ValueError: If invalid base64 or undecodeable ser_str
        :return: The MultiSig instance
        :rtype: MultiSig
        """
        try:
            ms_bytes = base64.b64decode(ser_str)
            assert SignatureScheme(ms_bytes[0]) == cls._SIGNATURE_SCHEME
            count = int(ms_bytes[1])
            kes_index = 2
            wei_index = kes_index + (count * SCHEME_PRIVATE_KEY_BYTE_LEN)
            # Get the keystrings
            key_block: list[SuiKeyPair] = []
            for idex in range(count):
                start = kes_index + (idex * SCHEME_PRIVATE_KEY_BYTE_LEN)
                key_block.append(
                    keypair_from_keystring(
                        base64.b64encode(ms_bytes[start : start + SCHEME_PRIVATE_KEY_BYTE_LEN]).decode()
                    )
                )
            # Get the weights
            weight_block: list[int] = []
            for idex in range(count):
                start = wei_index + (idex * 2)
                weight_block.append(int.from_bytes(ms_bytes[start : start + 2], "little"))
            # Get the threshold
            threshold = int.from_bytes(ms_bytes[-2:], "little")
            return MultiSig(key_block, weight_block, threshold)
        except binascii.Error as berr:
            raise ValueError(f"{berr.args}") from berr


# Utility functions
def _valid_mnemonic(mnemonics: Union[str, list[str]] = "") -> str:
    """_valid_mnemonic Validate, or create, mnemonic word string.

    :param mnemonics: space separated word string (12) or list of words(12), defaults to ""
    :type mnemonics: Union[str, list[str]], optional
    :raises ValueError: If the validation of supplied mnemonics fails
    :return: mnemonic word (24) string separated by spaces
    :rtype: str
    """
    if mnemonics:
        if isinstance(mnemonics, list):
            mnemonics = " ".join(mnemonics)

        if MnemonicValidator(Bip39MnemonicDecoder()).IsValid(mnemonics):
            return mnemonics
        raise ValueError(f"{mnemonics} is not a valid mnemonic phrase.")
    return bip_utils.Bip39MnemonicGenerator().FromWordsNumber(bip_utils.Bip39WordsNum.WORDS_NUM_24).ToStr()


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
    mnemonic_phrase = _valid_mnemonic(mnemonics)
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
    mnemonic_phrase = _valid_mnemonic(mnemonics)
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
    mnemonic_phrase = _valid_mnemonic(mnemonics)
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


@versionadded(version="0.16.1", reason="Localize key management")
def load_keys_and_addresses(
    keystore_file: str,
) -> Union[tuple[dict[str, KeyPair], dict[str, SuiAddress], dict[str, KeyPair]], Exception]:
    """load_keys_and_addresses Load keys and addresses.

    :param keystore_file: The current in use keystore file path
    :type keystore_file: str
    :raises SuiNoKeyPairs: If empty
    :raises SuiKeystoreFileError: If error reading file
    :raises SuiKeystoreAddressError: JSON error loading keyfile
    :raises SuiFileNotFound: If the file does not exists
    :return: Cross reference maps
    :rtype: Union[tuple[dict[str, KeyPair], dict[str, SuiAddress], dict[str, KeyPair]], Exception]
    """
    if os.path.exists(keystore_file):
        try:
            with open(keystore_file, encoding="utf8") as keyfile:
                _keystrings = json.load(keyfile)
                _keypairs: dict[str, KeyPair] = {}
                _addresses: dict[str, SuiAddress] = {}
                _address_keypair: dict[str, KeyPair] = {}
                if len(_keystrings) > 0:
                    for keystr in _keystrings:
                        kpair = keypair_from_keystring(keystr)
                        _keypairs[keystr] = kpair
                        addy = SuiAddress.from_keypair_string(kpair.to_b64())
                        _addresses[addy.address] = addy
                        _address_keypair[addy.address] = kpair
                    return _keypairs, _addresses, _address_keypair
                else:
                    raise SuiNoKeyPairs()
        except IOError as exc:
            raise SuiKeystoreFileError(exc) from exc
        except json.JSONDecodeError as exc:
            raise SuiKeystoreAddressError(exc) from exc
    else:
        raise SuiFileNotFound(str(keystore_file))


# pylint:disable=line-too-long,invalid-name
if __name__ == "__main__":
    pass
