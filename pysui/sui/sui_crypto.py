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
import base64
import binascii
import hashlib
import json
from enum import IntEnum
from typing import Optional, Union
from deprecated.sphinx import versionadded, versionchanged, deprecated
import pysui_fastcrypto as pfc


from pysui.abstracts import KeyPair, PrivateKey, PublicKey, SignatureScheme
from pysui.sui.sui_constants import (
    SUI_BECH32_HRP,
    PRIVATE_KEY_BYTE_LEN,
    SCHEME_PRIVATE_KEY_BYTE_LEN,
    SUI_HEX_ADDRESS_STRING_LEN,
    SUI_KEYPAIR_LEN,
    ED25519_DEFAULT_KEYPATH,
    ED25519_PUBLICKEY_BYTES_LEN,
    SECP256K1_DEFAULT_KEYPATH,
    SECP256K1_PUBLICKEY_BYTES_LEN,
    SECP256R1_DEFAULT_KEYPATH,
)

from pysui.sui.sui_types import SuiSignature, SuiAddress
from pysui.sui.sui_types.bcs import (
    MsBitmap,
    MsCompressedSig,
    MsEd25519PublicKey,
    MsNewPublicKey,
    MsSecp256k1PublicKey,
    MsSecp256r1PublicKey,
    MultiSignature,
)
from pysui.sui.sui_types.scalars import SuiTxBytes


class IntentScope(IntEnum):
    TransactionData = 0  # Used for a user signature on a transaction data.
    TransactionEffects = 1  # Used for an authority signature on transaction effects.
    CheckpointSummary = 2  # Used for an authority signature on a checkpoint summary.
    PersonalMessage = 3  # Used for a user signature on a personal message.
    SenderSignedTransaction = (
        4  # Used for an authority signature on a user signed transaction.
    )
    ProofOfPossession = 5  # Used as a signature representing an authority's proof of possession of its authority protocol key.
    HeaderDigest = 6  # Used for narwhal authority signature on header digest.
    BridgeEventUnused = (
        7  # for bridge purposes but it's currently not included in messages.
    )
    ConsensusBlock = 8  # Used for consensus authority signature on block's digest.
    DiscoveryPeers = 9  # Used for reporting peer addresses in discovery.


class SuiPublicKey(PublicKey):
    """SuiPublicKey Sui Basic public key."""

    @versionadded(version="0.78.0", reason="Support standalone public key.")
    @classmethod
    def from_serialized(cls, indata: str) -> PublicKey:
        """Convert base64 string to public key."""
        key_list = list(base64.b64decode(indata))
        sig = SignatureScheme(key_list[0])
        return SuiPublicKey(sig, bytes(key_list[1::]))

    @property
    def pub_key(self) -> str:
        """Return self as base64 encoded string."""
        return self.to_b64()

    @property
    def scheme(self) -> SignatureScheme:
        """Get the keys scheme."""
        return self._scheme

    @versionadded(
        version="0.78.0",
        reason="Support standalone public key serialization to base64.",
    )
    def serialize(self) -> str:
        """Serialize public key to base64 keystring."""
        return base64.b64encode(self.scheme_and_key()).decode()

    @versionadded(
        version="0.78.0", reason="Support signature verification using public key."
    )
    def verify_personal_message(self, message: str, signature: str) -> bool:
        """Verify personal message with signature, returning true/false."""
        from pysui.sui.sui_txn.transaction_builder import PureInput

        # Hash the message with intent
        intent_msg = bytearray([IntentScope.PersonalMessage, 0, 0])
        intent_msg.extend(PureInput.pure(list(base64.b64decode(message))))
        hd1 = hashlib.blake2b(intent_msg, digest_size=32).digest()
        sigbytes = bytes(list(base64.b64decode(signature))[1:65])
        return pfc.verify_pubk(
            self.scheme,
            self.key_bytes,
            base64.b64encode(hd1).decode(),
            base64.b64encode(sigbytes).decode(),
        )


@versionchanged(version="0.33.0", reason="Converted to use pysui-fastcrypto")
class SuiPrivateKey(PrivateKey):
    """SuiPrivateKey Sui Basic private/signing key."""

    def sign_secure(self, tx_data: str) -> list:
        """sign_secure Sign transaction intent.

        :param public_key: PublicKey from signer/private key
        :type public_key: SuiPublicKey
        :param tx_data: Transaction bytes being signed
        :type tx_data: str
        :return: Singed transaction as list of u8 bytes
        :rtype: list
        """
        return pfc.sign_digest(
            self.scheme,
            self.key_bytes,
            tx_data,
            [IntentScope.TransactionData, 0, 0],
        )

    @versionadded(version="0.71.0", reason="Signing personal messages")
    def sign_secure_personal_message(self, message: str) -> list:
        """sign_secure_personal_message for exchange.

        This method length encodes the message and prefixes with PersonalMessage intent.

        :param tx_data: Base64 encoded message
        :type tx_data: str
        :return: Signed message as list of u8 bytes
        :rtype: list
        """
        from pysui.sui.sui_txn.transaction_builder import PureInput

        tx_data = base64.b64encode(
            bytes(PureInput.pure(list(base64.b64decode(message))))
        ).decode("utf-8")
        return pfc.sign_digest(
            self.scheme,
            self.key_bytes,
            tx_data,
            [IntentScope.PersonalMessage, 0, 0],
        )

    @versionadded(version="0.33.0", reason="Hide private key")
    def __repr__(self) -> str:
        """To string."""
        return "Private Key"


@versionchanged(version="0.33.0", reason="Converted to use pysui-fastcrypto")
class SuiKeyPair(KeyPair):
    """SuiKeyPair Sui Basic keypair."""

    def __init__(self) -> None:
        """__init__ Default keypair initializer."""
        self._scheme: SignatureScheme = SignatureScheme.ED25519
        self._private_key: Union[SuiPrivateKey, None] = None
        self._public_key: Union[SuiPublicKey, None] = None

    @property
    def private_key(self) -> Union[SuiPrivateKey, None]:
        """Return the Private Key."""
        return self._private_key

    @property
    def public_key(self) -> Union[SuiPublicKey, None]:
        """Return the Public Key."""
        return self._public_key

    @property
    def scheme(self) -> SignatureScheme:
        """Get the keys scheme."""
        return self._scheme

    @versionchanged(version="0.33.0", reason="Changes to SuiPrivateKey")
    def new_sign_secure(self, tx_data: str) -> SuiSignature:
        """New secure sign with intent."""
        assert self.private_key, "Can not sign with invalid private key"
        sig = bytearray(self.private_key.sign_secure(tx_data))
        return SuiSignature(base64.b64encode(sig).decode())

    @versionadded(version="0.71.0", reason="Personal message with intent.")
    def sign_personal_message(self, message: str) -> str:
        """."""
        assert self.private_key, "Can not sign with invalid private key"
        sig = bytearray(self.private_key.sign_secure_personal_message(message))
        return base64.b64encode(sig).decode()

    @versionadded(version="0.71.0", reason="Verify personal message with intent.")
    def verify_personal_message(self, message: str, sig: str) -> bool:
        """Verify the personal message with IntentMessage."""
        from pysui.sui.sui_txn.transaction_builder import PureInput

        # Hash the message with intent
        intent_msg = bytearray([IntentScope.PersonalMessage, 0, 0])
        intent_msg.extend(PureInput.pure(list(base64.b64decode(message))))
        hd1 = hashlib.blake2b(intent_msg, digest_size=32).digest()
        sigbytes = bytes(list(base64.b64decode(sig))[1:65])
        return pfc.verify(
            self.scheme,
            self.private_key.key_bytes,
            base64.b64encode(hd1).decode(),
            base64.b64encode(sigbytes).decode(),
        )

    @versionchanged(version="0.34.0", reason="Added to verify signature of message")
    @deprecated(version="0.71.0", reason="Use verify_personal_message instead")
    def verify_signature(self, message: str, sig: str) -> bool:
        """Verify arbitrary message (base64) with signature (base64), returning bool."""
        return pfc.verify(self.scheme, self.private_key.key_bytes, message, sig)

    def serialize_to_bytes(self) -> bytes:
        """serialize_to_bytes Returns a SUI conforming keystring as bytes.

        :return: Bytes of signature scheme + private key
        :rtype: bytes
        """
        assert self.private_key, "Can not serialize_to_bytes with invalid private key"
        return self.scheme.to_bytes(1, "little") + self.private_key.key_bytes

    def serialize(self) -> str:
        """serialize Returns a SUI conforming keystring.

        :return: a base64 encoded string of schema and private key bytes
        :rtype: str
        """
        return base64.b64encode(self.serialize_to_bytes()).decode()

    @versionadded(version="0.76.0", reason="Export bech32 private key.")
    def to_bech32(self) -> str:
        """Convert private key to bech32 format

        :return: bech32 formated private key
        :rtype: str
        """
        return pfc.encode_bech32(self.serialize_to_bytes(), SUI_BECH32_HRP)

    def to_bytes(self) -> bytes:
        """Convert keypair to bytes."""
        assert self.private_key, "Can not convert to bytes with invalid private key"
        assert self.public_key, "Can not convert to bytessign with invalid private key"
        all_bytes = (
            self.scheme.to_bytes(1, "little")
            + self.public_key.key_bytes
            + self.private_key.key_bytes
        )
        return all_bytes

    @classmethod
    def from_bytes(cls, indata: bytes) -> KeyPair:
        """Convert bytes to keypair."""
        raise ValueError("from_bytes is legacy.")

    @versionadded(version="0.33.0", reason="Converted to use pysui-fastcrypto")
    @classmethod
    def from_pfc_bytes(
        cls, scheme: SignatureScheme, pub_bytes: bytes, prv_bytes: bytes
    ) -> "SuiKeyPair":
        """Convert bytes to keypair."""
        len_prv = len(prv_bytes)
        len_pub = len(pub_bytes)
        assert (
            len_prv == PRIVATE_KEY_BYTE_LEN
        ), f"Expected {PRIVATE_KEY_BYTE_LEN} private key length, found {len_prv}"
        if scheme is SignatureScheme.ED25519:
            assert (
                len_pub == ED25519_PUBLICKEY_BYTES_LEN
            ), f"Expected {ED25519_PUBLICKEY_BYTES_LEN} private key length, found {len_pub}"
        elif scheme is SignatureScheme.SECP256K1 or scheme is SignatureScheme.SECP256K1:
            assert (
                len_pub == SECP256K1_PUBLICKEY_BYTES_LEN
            ), f"Expected {SECP256K1_PUBLICKEY_BYTES_LEN} private key length, found {len_pub}"

        sui_kp = SuiKeyPair()
        sui_kp._scheme = scheme
        sui_kp._public_key = SuiPublicKey(scheme, pub_bytes)
        sui_kp._private_key = SuiPrivateKey(scheme, prv_bytes)
        return sui_kp

    @versionchanged(version="0.33.0", reason="Converted to use pysui-fastcrypto")
    @classmethod
    def from_b64(cls, indata: str) -> "SuiKeyPair":
        """Generate KeyPair from base64 keystring."""
        signature, pub_list, prv_list = pfc.keys_from_keystring(indata)
        return cls.from_pfc_bytes(
            SignatureScheme(signature),
            bytes(pub_list),
            bytes(prv_list),
        )

    @versionadded(version="0.57.0", reason="Support bech32 private key encoding")
    @classmethod
    def from_bech32(cls, indata: str) -> "KeyPair":
        """Convert bech32 encoded string to keypair."""
        signature, pub_list, prv_list = pfc.decode_bech32(indata, SUI_BECH32_HRP)
        if signature == 255:
            raise ValueError(f"Invalid HRP or variant {indata}")
        return cls.from_pfc_bytes(
            SignatureScheme(signature),
            bytes(pub_list),
            bytes(prv_list),
        )

    @versionchanged(version="0.33.0", reason="Hide private key")
    def __repr__(self) -> str:
        """To string."""
        return f"PubKey {self._public_key}, PrivKey `Private`"


class BaseMultiSig:
    """."""

    _MIN_KEYS: int = 2
    _MAX_KEYS: int = 10
    _MAX_WEIGHT: int = 255
    _MAX_THRESHOLD: int = 2549
    _COMPRESSED_SIG_LEN: int = 65

    def __init__(
        self,
        sui_pub_keys: list[SuiPublicKey],
        weights: list[int],
        threshold: int,
    ):
        """Validating initialization of components."""
        if (
            len(sui_pub_keys) in range(self._MIN_KEYS, self._MAX_KEYS)
            and len(sui_pub_keys) == len(weights)
            and threshold <= self._MAX_THRESHOLD
            and max(weights) <= self._MAX_WEIGHT
            and sum(weights) >= threshold
        ):
            self._scheme: SignatureScheme = SignatureScheme.MULTISIG
            self._weights: list[int] = weights
            self._public_keys = sui_pub_keys
            self._threshold: int = threshold
            self._address: SuiAddress = self._multi_sig_address()
        else:
            raise ValueError("Invalid arguments provided to constructor")

    def _multi_sig_address(self) -> SuiAddress:
        """multi_sig_address Generates the unique address derived from the keys in the MultiSig.

        :return: A unique address that can be used to participate as recipeint and sender in transactions.
        :rtype: SuiAddress
        """
        # Build the digest to generate a SuiAddress (hash) from
        digest = self._scheme.to_bytes(1, "little")
        digest += self._threshold.to_bytes(2, "little")
        for index, kkeys in enumerate(self._public_keys):
            digest += kkeys.scheme_and_key()  # type: ignore
            digest += self._weights[index].to_bytes(1, "little")
        return SuiAddress(hashlib.blake2b(digest, digest_size=32).hexdigest())

    @property
    def scheme(self) -> SignatureScheme:
        """Return the MultiSig signature scheme."""
        return SignatureScheme.MULTISIG

    @property
    @versionchanged(
        version="0.16.1",
        reason="Return add as str to align with non MultiSig SuiAddress behavior",
    )
    def address(self) -> str:
        """Return the address string generated from the initial keys."""
        return self._address.address

    @property
    @versionadded(
        version="0.16.1",
        reason="Provide ability to get MultiSig as SuiAddress",
    )
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

    @versionchanged(
        version="0.21.1", reason="Exposed as public for use by SuiTransaction"
    )
    def validate_signers(
        self, pub_keys: list[SuiPublicKey]
    ) -> Union[list[int], ValueError]:
        """Validate pubkeys part of multisig and have enough weight."""
        # Must be subset of full ms list
        if len(pub_keys) <= len(self._public_keys):
            hit_indexes = [self._public_keys.index(i) for i in pub_keys]
            # If all inbound pubkeys have reference to item in ms list
            if len(hit_indexes) == len(pub_keys):
                if sum([self._weights[x] for x in hit_indexes]) >= self._threshold:
                    return hit_indexes
        raise ValueError("Keys and weights for signing do not meet thresholds")

    def _new_publickey(self) -> list[MsNewPublicKey]:
        """Generate MultiSig BCS representation of PublicKey."""
        # Generate new BCS PublicKeys from the FULL compliment of original public keys
        pks: list[MsNewPublicKey] = []
        for index, kkeys in enumerate(self._public_keys):
            pkb = kkeys.key_bytes  # type: ignore
            if kkeys.scheme == SignatureScheme.ED25519:
                npk = MsNewPublicKey(
                    "Ed25519",
                    MsEd25519PublicKey(list(pkb), self._weights[index]),
                )
            elif kkeys.scheme == SignatureScheme.SECP256K1:
                npk = MsNewPublicKey(
                    "Secp256k1",
                    MsSecp256k1PublicKey(list(pkb), self._weights[index]),
                )
            elif kkeys.scheme == SignatureScheme.SECP256R1:
                npk = MsNewPublicKey(
                    "Secp256r1",
                    MsSecp256r1PublicKey(list(pkb), self._weights[index]),
                )
            pks.append(npk)
        return pks

    def _signature(
        self,
        pub_keys: list[SuiPublicKey],
        compressed_sigs: list[MsCompressedSig],
    ) -> SuiSignature:
        """."""
        key_indices = self.validate_signers(pub_keys)
        # Generate the public keys used position bitmap
        # then build the signature
        bm_pks: int = 0
        for index in key_indices:
            bm_pks |= 1 << index
        serialized_rbm: MsBitmap = MsBitmap(bm_pks)

        msig_signature = MultiSignature(
            self._scheme,
            compressed_sigs,
            serialized_rbm,
            self._new_publickey(),
            self.threshold,
        )
        return SuiSignature(base64.b64encode(msig_signature.serialize()).decode())

    def signature_from(
        self, pub_keys: list[SuiPublicKey], signatures: list[SuiSignature]
    ) -> SuiSignature:
        """signature_from Creates a multisig signature from signed bytes.

        :param pub_keys: List of public keys associated to keypairs that created signatures
        :type pub_keys: list[SuiPublicKey]
        :param signatures: Signatures from signed transaction bytes digest
        :type signatures: list[SuiSignature]
        :return: A multisig signature
        :rtype: SuiSignature
        """
        compressed: list[MsCompressedSig] = []
        for index in signatures:
            sig = str(index.value)
            compressed.append(
                MsCompressedSig(
                    list(base64.b64decode(sig)[0 : self._COMPRESSED_SIG_LEN])
                )
            )
        return self._signature(pub_keys, compressed)


class MultiSig(BaseMultiSig):
    """Multi signature support."""

    def __init__(self, suikeys: list[SuiKeyPair], weights: list[int], threshold: int):
        """__init__ Initiate a MultiSig object.

        Note that Sui multi-sig accepts up to a maximum of ten (10) individual signer keys.

        :param suikeys: The list of keys participating in the multi-sig signing operations.
        :type suikeys: list[SuiKeyPair]
        :param weights: Corresponding weights for each key. Max value of each weight is 255 (8 bit unsigned)
        :type weights: list[int]
        :param threshold: The threshold criteria for this MultiSig. Max value is 2549 (16 bit unsigned)
        :type threshold: int
        """
        super().__init__([kp.public_key for kp in suikeys], weights, threshold)
        self._keys = suikeys

    @property
    def full_keys(self) -> list[SuiKeyPair]:
        """."""
        return self._keys.copy()

    @versionadded(version="0.21.1", reason="Support for inline multisig signing")
    def _compressed_signatures(
        self, tx_bytes: str, key_indices: list[int]
    ) -> list[MsCompressedSig]:
        """Creates compressed signatures from each of the signing keys present."""
        compressed: list[MsCompressedSig] = []
        for index in key_indices:
            sig_t = self._keys[index].new_sign_secure(tx_bytes)
            sig = str(sig_t.value)
            compressed.append(
                MsCompressedSig(
                    list(base64.b64decode(sig)[0 : self._COMPRESSED_SIG_LEN])
                )
            )
        return compressed

    @versionadded(version="0.21.1", reason="Full signature creation without binaries.")
    @versionchanged(
        version="0.31.0",
        reason="Roaring bitmap no longer required in Sui 1.4.x and above.",
    )
    def sign(
        self, tx_bytes: Union[str, SuiTxBytes], pub_keys: list[SuiPublicKey]
    ) -> SuiSignature:
        """sign Signs transaction bytes for operation that changes objects owned by MultiSig address."""
        # Validate the pub_keys alignment with self._keys
        # key_indices = self._validate_signers(pub_keys)
        # Generate BCS compressed signatures for the subset of keys
        tx_bytes = tx_bytes if isinstance(tx_bytes, str) else tx_bytes.value  # type: ignore
        compressed_sigs: list[MsCompressedSig] = self._compressed_signatures(
            str(tx_bytes), self.validate_signers(pub_keys)
        )
        return self._signature(pub_keys, compressed_sigs)

    def serialize(self) -> str:
        """serialize Serializes the MultiSig object to base64 string.

        :return: Base64 string of serialized MultiSig
        :rtype: str
        """
        # Build from scheme and counts,keystrings,weights and threshold
        all_bytes = self.scheme.to_bytes(1, "little") + len(self._keys).to_bytes(
            1, "little"
        )
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
            assert SignatureScheme(ms_bytes[0]) == SignatureScheme.MULTISIG
            count = int(ms_bytes[1])
            kes_index = 2
            wei_index = kes_index + (count * SCHEME_PRIVATE_KEY_BYTE_LEN)
            # Get the keystrings
            key_block: list[SuiKeyPair] = []
            for idex in range(count):
                start = kes_index + (idex * SCHEME_PRIVATE_KEY_BYTE_LEN)
                key_block.append(
                    keypair_from_keystring(
                        base64.b64encode(
                            ms_bytes[start : start + SCHEME_PRIVATE_KEY_BYTE_LEN]
                        ).decode()
                    )
                )
            # Get the weights
            weight_block: list[int] = []
            for idex in range(count):
                start = wei_index + (idex * 2)
                weight_block.append(
                    int.from_bytes(ms_bytes[start : start + 2], "little")
                )
            # Get the threshold
            threshold = int.from_bytes(ms_bytes[-2:], "little")
            return MultiSig(key_block, weight_block, threshold)
        except binascii.Error as berr:
            raise ValueError(f"{berr.args}") from berr


def gen_mnemonic_phrase(word_counts: int) -> str:
    """gen_mnemonic_phrase Generates a unique string of words of count word_counts.

    :param word_counts: Can be one of 12, 15, 18, 21, 24
    :type word_counts: int
    :raises ValueError: If word count not in set
    :return: The string of words with space separators
    :rtype: str
    """
    if not word_counts in {12, 15, 18, 21, 24}:
        raise ValueError("Word count must be one of integer {12, 15, 18, 21, 24}")

    return pfc.generate_mnemonic_phrase(str(word_counts))


@versionchanged(
    version="0.33.0",
    reason="Requires word count, no longer allows phrase.",
)
def create_new_keypair(
    scheme: Optional[SignatureScheme] = SignatureScheme.ED25519,
    word_counts: Optional[int] = 12,
    derv_path="",
) -> tuple[str, KeyPair]:
    """create_new_keypair Generate a new keypair.

    :param keytype: One of ED25519, SECP256K1 or SECP256R1 key type, defaults to SignatureScheme.ED25519
    :type keytype: SignatureScheme, optional
    :param word_counts: count of words to generate mnemonic phrase, defaults to 12
    :type word_counts: int, optional
    :param derv_path: derivation path coinciding with key type, defaults to None
    :type derv_path: str, optional
    :raises NotImplementedError: If invalid keytype is provided
    :return: mnemonic words and new keypair
    :rtype: tuple[str, KeyPair]
    """
    if not isinstance(scheme, SignatureScheme):
        raise ValueError(f"Not a Sui signature scheme type")
    if scheme > 2:
        raise ValueError(f"Signature Scheme {scheme.name} not supported")
    if not word_counts in {12, 15, 18, 21, 24}:
        raise ValueError("Word count must be one of integer {12, 15, 18, 21, 24}")
    derv_path = (
        derv_path
        or [
            ED25519_DEFAULT_KEYPATH,
            SECP256K1_DEFAULT_KEYPATH,
            SECP256R1_DEFAULT_KEYPATH,
        ][scheme]
    )

    phrase, pub_list, prv_list = pfc.generate_new_keypair(
        scheme, derv_path, str(word_counts)
    )
    return str(phrase), SuiKeyPair.from_pfc_bytes(
        scheme, bytes(pub_list), bytes(prv_list)
    )


@versionchanged(
    version="0.33.0",
    reason="Using pysui-fastcrypto.",
)
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
    mnemonics = " ".join(mnemonics) if mnemonics is list else mnemonics
    pub_list, prv_list = pfc.keys_from_mnemonics(keytype, derv_path, mnemonics)
    new_kp = SuiKeyPair.from_pfc_bytes(keytype, bytes(pub_list), bytes(prv_list))
    return mnemonics, new_kp, SuiAddress.from_bytes(new_kp.to_bytes())  # type: ignore


@versionchanged(
    version="0.33.0",
    reason="Requires word count, no longer allows phrase.",
)
def create_new_address(
    keytype: SignatureScheme,
    word_counts: Optional[int] = 12,
    derv_path=None,
) -> tuple[str, KeyPair, SuiAddress]:
    """create_new_address Create a new keypair and address for a key type.

    :param keytype: One of ED25519, SECP256K1 or SECP256R1 key type
    :type keytype: SignatureScheme
    :param word_counts: count of words to generate mnemonic phrase, defaults to 12
    :type word_counts: int, optional
    :param derv_path: derivation path coinciding with key type, defaults to None
    :type derv_path: str, optional
    :return: mnemonic words, new keypair and derived sui address
    :rtype: tuple[str, KeyPair, SuiAddress]
    """
    mnem, new_kp = create_new_keypair(keytype, word_counts, derv_path)
    return mnem, new_kp, SuiAddress.from_bytes(new_kp.to_bytes())


@versionchanged(
    version="0.33.0",
    reason="Using pysui-fastcrypto.",
)
@versionchanged(version="0.57.0", reason="Support bech32 keystring encoding")
def keypair_from_keystring(keystring: str) -> SuiKeyPair:
    """keypair_from_keystring Parse keystring to keypair.

    :param keystring: base64 or bech32 keystring encoding
    :type keystring: str
    :raises SuiInvalidKeystringLength: If base64 invalid keypair string length
    :raises NotImplementedError: If invalid keytype signature in string
    :return: keypair derived from keystring
    :rtype: KeyPair
    """
    if keystring.startswith(SUI_BECH32_HRP):
        return SuiKeyPair.from_bech32(keystring)
    if len(keystring) != SUI_KEYPAIR_LEN:
        raise ValueError(
            f"Invalid keystring length, found {len(keystring)} expected {SUI_KEYPAIR_LEN}"
        )
    return SuiKeyPair.from_b64(keystring)


@versionchanged(
    version="0.41.0",
    reason="Replace cross-reference matrix instead of individual dicts on return",
)
def load_keys_and_addresses(
    keystore_file: str,
) -> Union[
    list[list[dict]],
    Exception,
]:
    """load_keys_and_addresses Load keys and addresses.

    :param keystore_file: The current in use keystore file path
    :type keystore_file: str
    :raises SuiNoKeyPairs: If empty
    :raises SuiKeystoreFileError: If error reading file
    :raises SuiKeystoreAddressError: JSON error loading keyfile
    :raises SuiFileNotFound: If the file does not exists
    :return: Cross reference matrix [{},{keystring:KeyPair},{publickyestring:keystring},{str:SuiAddress}]
    :rtype: Union[list[list[dict]], Exception]
    """
    if os.path.exists(keystore_file):
        try:
            with open(keystore_file, encoding="utf8") as keyfile:
                _keystrings = json.load(keyfile)
                _cref_matrix: list[list[dict]] = []
                if len(_keystrings) > 0:
                    for keystr in _keystrings:
                        crm_entry = [{}]
                        kpair = keypair_from_keystring(keystr)
                        puks = base64.b64encode(
                            kpair.public_key.scheme_and_key()
                        ).decode()
                        addy = SuiAddress.from_keypair_string(kpair.to_b64())
                        crm_entry.extend(
                            [{keystr: kpair}, {puks: keystr}, {addy.address: addy}]
                        )
                        _cref_matrix.append(crm_entry)
                    return _cref_matrix
                else:
                    raise ValueError("Empty keystring found")
        except IOError as exc:
            raise exc
        except json.JSONDecodeError as exc:
            raise exc
    else:
        raise ValueError(f"{keystore_file} not found")


@versionadded(version="0.33.0", reason="To support wallet exported keys.")
def as_keystrings(inputs: list[Union[str, dict]]) -> list[str]:
    """as_keystrings Returns a list of just keystrings from heterogenous list of keystrings or dicts.

    :param inputs: List of Sui keystrings or Wallet dict for conversion to keystring
    :type inputs: list[Union[str, dict]]
    :return: List of strings in Sui keystring form
    :rtype: list[str]
    """
    results: list[str] = []
    for keyinput in inputs:
        # If dict with specific kv pairs
        if isinstance(keyinput, dict):
            wallet_hex = keyinput["wallet_key"]
            assert (
                len(wallet_hex) == SUI_HEX_ADDRESS_STRING_LEN
            ), f"Invalid wallet_key length, found {len(wallet_hex)} expected {SUI_HEX_ADDRESS_STRING_LEN}"
            assert (
                wallet_hex[0:2] == "0x" or wallet_hex[0:2] == "0X"
            ), "Expected wallet_key to have 0x or 0X prefix"
            scheme = keyinput["key_scheme"]
            assert (
                isinstance(scheme, SignatureScheme) and scheme.value < 3
            ), "Invalid key scheme"
            keybytes = bytearray(scheme.value.to_bytes(1, "little"))
            keybytes.extend(binascii.unhexlify(wallet_hex[2:]))
            keyinput = base64.b64encode(keybytes).decode()
        results.append(keyinput)
    return results


@versionchanged(
    version="0.33.0",
    reason="To support wallet exported keys and/or Sui valid keystrings.",
)
@versionchanged(
    version="0.41.0",
    reason="Replace cross-reference matrix instead of individual dicts on return",
)
def emphemeral_keys_and_addresses(
    keystrings: list[Union[str, dict]],
) -> list[list[dict]]:
    """emphemeral_keys_and_addresses Convert list of keystrings from SuiConfig.user_config().

    :param keystrings: List of Sui keystrings or Wallet dict for conversion to keystring
    :type keystrings: list[Union[str, dict]]
    :return: Cross reference matrix [{},{keystring:KeyPair},{publickyestring:keystring},{str:SuiAddress}]
    :rtype: Union[list[list[dict]], Exception]
    """
    _keystrings = as_keystrings(keystrings)

    _cref_matrix: list[list[dict]] = []
    for keystr in _keystrings:
        kpair = keypair_from_keystring(keystr)
        addy = SuiAddress.from_keypair_string(kpair.to_b64())
        # addy = SuiAddress.from_keypair_string(keystr)
        crm_entry = [{}]
        puks = base64.b64encode(kpair.public_key.scheme_and_key()).decode()
        crm_entry.extend([{keystr: kpair}, {puks: keystr}, {addy.address: addy}])
        _cref_matrix.append(crm_entry)
    return _cref_matrix


if __name__ == "__main__":
    pass
