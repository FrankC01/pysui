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

"""Testing crypto capabilities (no transactions)."""

import pytest
from pysui import SuiAddress
from pysui.abstracts.client_keypair import SignatureScheme
from pysui.sui.sui_crypto import (
    create_new_address,
    create_new_keypair,
    emphemeral_keys_and_addresses,
    keypair_from_keystring,
    recover_key_and_address,
)


KEYSTRING_LIST: list[str] = [
    "AIUPxQveY18QxhDDdTO0D0OD6PNV+et50068d1g/rIyl",
    "AOM6UAQrFe7r9nNDGRlWwj1o7m1cGK6mDZ3efRJJmvcG",
    "ASh0NQrbB6bVUXzT+nL0eL/pYpFxA004+yJVr+ESLyKD",
    "Ap2UtlPaemem6P6cfpg8jNKKlnmrWlqhNH3TNl46zEyK",
    "AdWV+84ut+b9phzm7ZBISKYDSFk7Weqs07wk4DsMxlRY",
]

ADDRESS_OUT_LIST: list[str] = [
    "0x62416c2bd475c99cc8dfe75d1ae78a0e99ed8f7833ff0f5f36726c96bdd4b5d2",
    "0xa9e2db385f055cc0215a3cde268b76270535b9443807514f183be86926c219f4",
    "0xa9fe7b9cab7ce187c768a9b16e95dbc5953a99ec461067a73a6b1c4288873e28",
    "0xb0d73b5bcb842853c3e5367325ccfd15a81a141842f9d798c793f2d597cc65c5",
    "0x0c2bbc042e4ce750ee98ce017bee8ddbfc8b70da00979374bf9c0964ce02e3ed",
]


def test_emphemeral_creates():
    """test_emphemeral_creates validate round trip in keystrings."""
    dict_keystr, _dict_addy, _dict_addy_key = emphemeral_keys_and_addresses(
        KEYSTRING_LIST
    )
    # Should match on keystrings
    for idex, kstr in enumerate(dict_keystr.keys()):
        assert kstr in KEYSTRING_LIST
        assert idex == KEYSTRING_LIST.index(kstr)
        assert kstr == dict_keystr[kstr].serialize()
        assert dict_keystr[kstr].serialize() in KEYSTRING_LIST
        assert (
            SuiAddress.from_keypair_string(dict_keystr[kstr].to_b64()).address
            == ADDRESS_OUT_LIST[idex]
        )


def test_keypair_create():
    """Various supported keytypes."""
    phrase, kp = create_new_keypair()
    assert len(phrase.split(" ")) == 12
    phrase, kp = create_new_keypair(SignatureScheme.SECP256K1, 18)
    assert len(phrase.split(" ")) == 18
    phrase, kp = create_new_keypair(SignatureScheme.SECP256R1, 24)
    assert len(phrase.split(" ")) == 24


def test_signing():
    """Test signature match for well known signature."""
    sktr = "ADEvd+Ah9oM1yOWMsP7G5KvK8glo4b52PqXRCIK0/i13vgcgDBTSmWoY2Iqd6SvKwXTnHW+KCdNRJIhA2jrdygjXa5x6KXqRZvWuDKnnWwILWd1coaxO7+cGQ8YL6A9VzA=="
    kp = keypair_from_keystring("AOM6UAQrFe7r9nNDGRlWwj1o7m1cGK6mDZ3efRJJmvcG")
    res = kp.new_sign_secure(
        "AAAEAAgAypo7AAAAAAAIAMqaOwAAAAABADREBHzUuo0veOkm9ajjcxYq1NxsLgXSYcC7/X4oFhoaoAUAAAAAAAAgETqmuazrgq7B72tOG6cWceUT75gM8kRFwBGLgqg0TqwAIKni2zhfBVzAIVo83iaLdicFNblEOAdRTxg76Gkmwhn0AgIBAgACAQAAAQEAAQIDAAAAAAMAAAEAAQMAqeLbOF8FXMAhWjzeJot2JwU1uUQ4B1FPGDvoaSbCGfQBATMSrQ+9XmatOs8Nr2zvl1ByFb9anfD2TqJE6569i++gBQAAAAAAACCluoNkyH4V37zDuDBiLgc+AsTvGv/xJ1WIMIN++yeywKni2zhfBVzAIVo83iaLdicFNblEOAdRTxg76Gkmwhn06AMAAAAAAABYtksAAAAAAAA="
    )
    assert res.value == sktr


def test_recover_same():
    """Test key recovery."""
    # Get a unique key
    phrase, kp, addy = create_new_address(SignatureScheme.ED25519)
    # Use the phrase and identical path
    ophr, kpr, addyr = recover_key_and_address(
        SignatureScheme.ED25519, phrase, "m/44'/784'/0'/0'/0'"
    )
    assert kp.serialize() == kpr.serialize()
    assert addy.address == addyr.address


def test_bad_keypair_create():
    """Exceptions in create."""
    # Not even a signature scheme
    with pytest.raises(ValueError) as exc_info:
        phrase, kp = create_new_keypair(17)
        assert str(exc_info) == "Not a Sui signature scheme type"

    # Bad keypair scheme
    with pytest.raises(ValueError) as exc_info:
        phrase, kp = create_new_keypair(SignatureScheme.MULTISIG)
        assert str(exc_info) == "Signature Scheme MULTISIG not supported"
    # Bad wordcount
    with pytest.raises(ValueError) as exc_info:
        phrase, kp = create_new_keypair(SignatureScheme.ED25519, 16)
        assert (
            str(exc_info)
            == "Word count must be one of integer {12, 15, 18, 21, 24}"
        )
    with pytest.raises(ValueError) as exc_info:
        phrase, kp = create_new_keypair(SignatureScheme.ED25519, "16")
        assert (
            str(exc_info)
            == "Word count must be one of integer {12, 15, 18, 21, 24}"
        )
