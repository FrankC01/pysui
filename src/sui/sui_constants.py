"""Sui Constants."""


SUI_HEX_ADDRESS_STRING_LEN = 42
"""Length of valid address string with '0x' prefix."""
SUI_ADDRESS_STRING_LEN = 40
"""Length of valid address string without '0x' prefix."""

SUI_KEYPAIR_LEN = 88
"""Length of keypair string."""

# ED25519 from keystring bytes
ED25519_KEYPAIR_BYTES_LEN = 64
"""Length of ED25519 keypair bytes."""
ED25519_PUBLICKEY_BYTES_LEN = 32
"""Length of ED25519 public key bytes."""
ED25519_PRIVATEKEY_BYTES_LEN = 32
"""Length of ED25519 private key bytes."""

# SECP256K1 from address bytes
SECP256K1_KEYPAIR_BYTES_LEN = 65
"""Length of SECP256K1 keypair bytes."""
SECP256K1_PUBLICKEY_BYTES_LEN = 33
"""Length of SECP256K1 public key bytes."""
SECP256K1_PRIVATEKEY_BYTES_LEN = 32
"""Length of SECP256K1 private key bytes."""
