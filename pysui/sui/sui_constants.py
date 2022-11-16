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


"""Sui Constants."""

SUI_COIN_DENOMINATOR: int = 1000000000

SUI_HEX_ADDRESS_STRING_LEN: int = 42
"""Length of valid address string with '0x' prefix."""
SUI_ADDRESS_STRING_LEN: int = 40
"""Length of valid address string without '0x' prefix."""

SUI_KEYPAIR_LEN: int = 88
"""Length of keypair string."""

# ED25519 from keystring bytes
ED25519_KEYPAIR_BYTES_LEN: int = 64
"""Length of ED25519 keypair bytes."""
ED25519_PUBLICKEY_BYTES_LEN: int = 32
"""Length of ED25519 public key bytes."""
ED25519_PRIVATEKEY_BYTES_LEN: int = 32
"""Length of ED25519 private key bytes."""

# SECP256K1 from address bytes
SECP256K1_KEYPAIR_BYTES_LEN: int = 65
"""Length of SECP256K1 keypair bytes."""
SECP256K1_PUBLICKEY_BYTES_LEN: int = 33
"""Length of SECP256K1 public key bytes."""
SECP256K1_PRIVATEKEY_BYTES_LEN: int = 32
"""Length of SECP256K1 private key bytes."""
