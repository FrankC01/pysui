#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sui Legacy Configuration (JSON RPC) setup."""

import json
import dataclasses
from typing import Optional
from pathlib import Path
import hashlib
import dataclasses_json
import yaml

from pysui.sui.sui_pgql.config.confgroup import (
    ProfileGroup,
    ProfileKey,
    ProfileAlias,
    Profile,
)
from pysui.sui.sui_crypto import keypair_from_keystring

_DEVNET_SUI_URL: str = "https://fullnode.devnet.sui.io:443"
_DEVNET_FAUCET_URL: str = "https://faucet.devnet.sui.io/v1/gas"
_DEVNET_FAUCET_STATUS_URL: str = "https://faucet.devnet.sui.io/v1/status/"

_TESTNET_SUI_URL: str = "https://fullnode.testnet.sui.io:443"
_TESTNET_FAUCET_URL: str = "https://faucet.testnet.sui.io/v1/gas"
_TESTNET_FAUCET_STATUS_URL: str = "https://faucet.testnet.sui.io/v1/status/"


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class KeystoreFile:
    """Sui default config points to keyfile."""

    File: str


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ConfigEnv:
    """Sui default config environment."""

    alias: str
    rpc: str
    ws: Optional[str] = None
    basic_auth: Optional[str] = None


@dataclasses.dataclass
class ConfigSui(dataclasses_json.DataClassJsonMixin):
    """Sui default config."""

    keystore: KeystoreFile
    active_env: str
    active_address: str
    envs: list[ConfigEnv]


def address_str_from_keystring(indata: str) -> str:
    """From a 44 char keypair string create an address string."""
    #   Check address is legit keypair

    _kp = keypair_from_keystring(indata).to_bytes()
    digest = _kp[0:33] if _kp[0] == 0 else _kp[0:34]
    return format(f"0x{hashlib.blake2b(digest, digest_size=32).hexdigest()}")


def load_client_yaml(client_file: Path, json_rpc_group: str) -> ProfileGroup:
    """."""
    _client_yaml = client_file / "client.yaml"
    _client_alias = client_file / "sui.aliases"
    # Check client.yaml and sui.aliases
    if not _client_yaml.exists() or not _client_alias.exists():
        raise ValueError(f"{client_file} invalid sui configuration")
    # load client.yaml
    cfg_sui = ConfigSui.from_dict(
        yaml.safe_load(_client_yaml.read_text(encoding="utf8"))
    )
    # Check sui.keystore
    keyfile = Path(cfg_sui.keystore.File)
    if not keyfile.exists():
        raise ValueError(f"{cfg_sui.keystore.File} does not exist")
    # Build profiles
    _prf_list: list[Profile] = []
    for senv in cfg_sui.envs:
        _prf: Profile = Profile(senv.alias, senv.rpc)
        if senv.rpc == _DEVNET_SUI_URL:
            _prf.faucet_url = _DEVNET_FAUCET_URL
            _prf.faucet_status_url = _DEVNET_FAUCET_STATUS_URL
        elif senv.rpc == _TESTNET_SUI_URL:
            _prf.faucet_url = _TESTNET_FAUCET_URL
            _prf.faucet_status_url = _TESTNET_FAUCET_STATUS_URL
        _prf_list.append(_prf)

    _prf_keys: list[ProfileKey] = []
    _prf_addy: list[str] = []
    for prvkey in json.loads(keyfile.read_text(encoding="utf8")):
        _prf_keys.append(ProfileKey.from_dict({"private_key_base64": prvkey}))
        _prf_addy.append(address_str_from_keystring(prvkey))

    # Build sui_config group
    prg_group = ProfileGroup(
        json_rpc_group,
        cfg_sui.active_env,
        cfg_sui.active_address,
        [
            ProfileAlias.from_dict(x)
            for x in json.loads(_client_alias.read_text(encoding="utf8"))
        ],
        _prf_keys,
        _prf_addy,
        _prf_list,
    )
    return prg_group