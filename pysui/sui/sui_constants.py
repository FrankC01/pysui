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

# Config file constants
DEFAULT_DEVNET_PATH_STRING: str = "~/.sui/sui_config/client.yaml"
"""Devnet client configuration default."""
DEVNET_ENVIRONMENT_KEY: str = "devnet"
"""Devnet client configuration environment alias."""
DEVNET_FAUCET_URL: str = "http://faucet.devnet.sui.io/gas"
"""Devnet client faucet url."""
DEVNET_SOCKET_URL: str = "wss://fullnode.devnet.sui.io:443"
"""Devnet socket url."""

LOCALNET_ENVIRONMENT_KEY: str = "localnet"
"""Localnet client configuration environment alias."""
LOCALNET_FAUCET_URL: str = "http://127.0.0.1:9123/gas"
"""Localnet client faucet url."""
LOCALNET_SOCKET_URL: str = "ws://127.0.0.1:9000"
"""Localnet socket url."""

# Address lengths
SUI_HEX_ADDRESS_STRING_LEN: int = 42
"""Length of valid address string with '0x' prefix."""
SUI_ADDRESS_STRING_LEN: int = 40
"""Length of valid address string without '0x' prefix."""

# Keystring length
SUI_KEYPAIR_LEN: int = 44
"""Length of valid key string base64 string."""

# ED25519 Keypair derivation path
# m / purpose' / coin_type' / account' / change' / address_index'
ED25519_DEFAULT_KEYPATH: str = "m/44'/784'/0'/0'/0'"
# ED25519 from keystring bytes
ED25519_KEYPAIR_BYTES_LEN: int = 32
"""Length of ED25519 keypair bytes."""
ED25519_PUBLICKEY_BYTES_LEN: int = 32
"""Length of ED25519 public key bytes."""
ED25519_PRIVATEKEY_BYTES_LEN: int = 32
"""Length of ED25519 private key bytes."""

# SECP256K1 Keypair derivation path
# m / purpose' / coin_type' / account' / change / address_index
SECP256K1_DEFAULT_KEYPATH: str = "m/54'/784'/0'/0/0"
# SECP256K1 from address bytes
SECP256K1_KEYPAIR_BYTES_LEN: int = 32
"""Length of SECP256K1 keypair bytes."""
SECP256K1_PUBLICKEY_BYTES_LEN: int = 33
"""Length of SECP256K1 public key bytes."""
SECP256K1_PRIVATEKEY_BYTES_LEN: int = 32
"""Length of SECP256K1 private key bytes."""

# SECP256K1 Keypair derivation path
# m / purpose' / coin_type' / account' / change / address_index
SECP256R1_DEFAULT_KEYPATH: str = "m/74'/784'/0'/0/0"
# SECP256R1 from address bytes
SECP256R1_KEYPAIR_BYTES_LEN: int = 32
"""Length of SECP256R1 keypair bytes."""
SECP256R1_PUBLICKEY_BYTES_LEN: int = 33
"""Length of SECP256R1 public key bytes."""
SECP256R1_PRIVATEKEY_BYTES_LEN: int = 32
"""Length of SECP256R1 private key bytes."""
