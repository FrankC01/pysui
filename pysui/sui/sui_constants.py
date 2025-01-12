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


"""Sui Constants."""

SUI_COIN_DENOMINATOR: int = 1_000_000_000

# Runtime environment keys
PYSUI_EXEC_ENV: str = "SUI_EXEC"
"""Holds the fully qualified path to the active sui binary."""
PYSUI_CLIENT_CONFIG_ENV: str = "SUI_CLIENT_CONFIG"
"""Holds the fully qualified path to the active client.yaml."""
PYSUI_RPC_VERSION: str = "SUI_RPC_VERSION"
"""Holds the RPC version detected at runtime."""

# sui-base configuration and execution constants
SUI_BASE_ACTIVE: str = "~/suibase/workdirs/active"
"""sui-base symbolic link to what configuration is active."""
SUI_BASE_EXEC_PATH: str = "target/debug/sui"
"""sui-base binary location relative to the active configuration workdir."""

# sui binary default
DEFAULT_SUI_BINARY_PATH: str = "~/.cargo/bin/sui"
"""The default fully qualified sui binary path."""

# Config file constants
DEFAULT_SUI_CONFIG_PATH: str = "~/.sui/sui_config/"
DEFAULT_SUI_CLIENT_CONFIG: str = "client.yaml"
DEFAULT_SUI_ALIAS_CONFIG: str = "sui.aliases"
DEFAULT_DEVNET_PATH_STRING: str = "~/.sui/sui_config/client.yaml"
DEFAULT_ALIAS_PATH_STRING: str = "~/.sui/sui_config/sui.aliases"

"""Devnet client configuration default."""
DEVNET_ENVIRONMENT_KEY: str = "devnet"
"""Devnet client configuration environment alias."""
LOCALNET_ENVIRONMENT_KEY: str = "localnet"
"""Localnet client configuration environment alias."""
TESTNET_ENVIRONMENT_KEY: str = "testnet"
"""Testnet client configuration environment alias."""

DEVNET_SUI_URL: str = "https://fullnode.devnet.sui.io:443"
"""Devnet Sui client url."""
# DEVNET_FAUCET_URL: str = "https://faucet.devnet.sui.io/gas"
# """Devnet client faucet url."""
DEVNET_FAUCET_URLV1: str = "https://faucet.devnet.sui.io/v1/gas"
DEVNET_FAUCET_STATUS_URLV1: str = "https://faucet.devnet.sui.io/v1/status/"
"""Devnet client faucet url V1."""
DEVNET_SOCKET_URL: str = "wss://fullnode.devnet.sui.io:443"
"""Devnet socket url."""

LOCALNET_SUI_URL: str = "https://127.0.0.1:9000"
"""Testnet Sui client url."""
LOCALNET_PROXY_SUI_URL: str = "http://0.0.0.0:44340"
"""Testnet Sui proxy client url."""
LOCALNET_FAUCET_URL: str = "http://127.0.0.1:9123/gas"
"""Localnet client faucet url."""
LOCALNET_SOCKET_URL: str = "ws://127.0.0.1:9000"
"""Localnet socket url."""

TESTNET_SUI_URL: str = "https://fullnode.testnet.sui.io:443"
"""Testnet Sui client url."""
TESTNET_FAUCET_URLV1: str = (
    "https://faucet.testnet.sui.io/v1/gas"  # "http://faucet.testnet.sui.io/gas"
)
TESTNET_FAUCET_STATUS_URLV1: str = "https://faucet.testnet.sui.io/v1/status/"
TESTNET_SOCKET_URL: str = "wss://fullnode.testnet.sui.io:443"
"""Testnet socket url."""

MAINNET_SUI_URL: str = "https://fullnode.mainnet.sui.io:443"
"""Testnet Sui client url."""
MAINNET_FAUCET_URL: str = ""
"""Mainnet client faucet url."""
MAINNET_SOCKET_URL: str = "wss://fullnode.mainnet.sui.io:443"
"""Testnet socket url."""

EMPEHMERAL_PATH: str = "ephemeral"
"""A user memory only configuration path"""

EMPEHMERAL_USER: str = "user"
"""A user memory only configuration"""

# Alias length
SUI_MIN_ALIAS_LEN: int = 3
"""Minimal length of an alias name string."""
SUI_MAX_ALIAS_LEN: int = 64
"""Maximum length of an alias name string."""

# Address lengths
SUI_HEX_ADDRESS_STRING_LEN: int = 66
"""Length of valid address string with '0x' prefix."""
SUI_ADDRESS_STRING_LEN: int = 64
"""Length of valid address string without '0x' prefix."""

# Keystring length
SUI_KEYPAIR_LEN: int = 44
"""Length of valid key string base64 string."""

SUI_BECH32_HRP: str = "suiprivkey"
"""Private Key bech32 private key encoding human readable portion"""

PRIVATE_KEY_BYTE_LEN: int = 32
"""Byte length of general private key"""
SCHEME_PRIVATE_KEY_BYTE_LEN: int = PRIVATE_KEY_BYTE_LEN + 1
"""Byte length of general signature scheme and private key"""

# ED25519 Keypair derivation path
# m / purpose' / coin_type' / account' / change' / address_index'
ED25519_DEFAULT_KEYPATH: str = "m/44'/784'/0'/0'/0'"
# ED25519 from keystring bytes
ED25519_KEYPAIR_BYTES_LEN: int = 32
"""Length of ED25519 keypair bytes."""
ED25519_PUBLICKEY_BYTES_LEN: int = 32
"""Length of ED25519 public key bytes."""
ED25519_PRIVATEKEY_BYTES_LEN: int = PRIVATE_KEY_BYTE_LEN
"""Length of ED25519 private key bytes."""

# SECP256K1 Keypair derivation path
# m / purpose' / coin_type' / account' / change / address_index
SECP256K1_DEFAULT_KEYPATH: str = "m/54'/784'/0'/0/0"
# SECP256K1 from address bytes
SECP256K1_KEYPAIR_BYTES_LEN: int = 32
"""Length of SECP256K1 keypair bytes."""
SECP256K1_PUBLICKEY_BYTES_LEN: int = 33
"""Length of SECP256K1 public key bytes."""
SECP256K1_PRIVATEKEY_BYTES_LEN: int = PRIVATE_KEY_BYTE_LEN
"""Length of SECP256K1 private key bytes."""

# SECP256R1 Keypair derivation path
# m / purpose' / coin_type' / account' / change / address_index
SECP256R1_DEFAULT_KEYPATH: str = "m/74'/784'/0'/0/0"
# SECP256R1 from address bytes
SECP256R1_KEYPAIR_BYTES_LEN: int = 32
"""Length of SECP256R1 keypair bytes."""
SECP256R1_PUBLICKEY_BYTES_LEN: int = 33
"""Length of SECP256R1 public key bytes."""
SECP256R1_PRIVATEKEY_BYTES_LEN: int = PRIVATE_KEY_BYTE_LEN
"""Length of SECP256R1 private key bytes."""
