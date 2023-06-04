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

"""Simplify routines for test usage."""

from pysui.abstracts.client_keypair import KeyPair, SignatureScheme
from pysui.sui.sui_config import SuiConfig
from pysui.sui.sui_crypto import MultiSig
from pysui.sui.sui_txresults.single_tx import SuiCoinObject
from pysui.sui.sui_types.address import SuiAddress
from pysui.sui.sui_clients.sync_client import SuiClient

STANDARD_BUDGET: str = "5500000"


def first_addy_keypair_for(
    *, cfg: SuiConfig, sigtype: SignatureScheme = SignatureScheme.ED25519, not_in: list[str] = None
) -> tuple[str, KeyPair]:
    """Get first address and keypair that matches keypair scheme."""
    not_in = not_in if not_in else []
    filtered = [(k, v) for (k, v) in cfg.addresses_and_keys.items() if v.scheme == sigtype]
    if filtered:
        for candidate in filtered:
            if candidate[0] not in not_in:
                return candidate
    raise ValueError(f"No keypair type of {sigtype.as_str()}")


def gas_not_in(client: SuiClient, for_addy: SuiAddress = None, not_in: list[str] = None) -> SuiCoinObject:
    """Get gas object that is not in collection."""
    for_addy = for_addy if for_addy else client.config.active_address
    result = client.get_gas(for_addy)
    not_in = not_in if not_in else []
    if result.is_ok():
        for agas in result.result_data.data:
            if agas.coin_object_id not in not_in:
                return agas
    else:
        print(result.result_string)
    raise ValueError(result.result_string)


def gen_ms(config: SuiConfig) -> MultiSig:
    """."""
    _, ed_key = first_addy_keypair_for(cfg=config)
    _, k1_key = first_addy_keypair_for(cfg=config, sigtype=SignatureScheme.SECP256K1)
    _, r1_key = first_addy_keypair_for(cfg=config, sigtype=SignatureScheme.SECP256R1)
    multi_sig = MultiSig([ed_key, k1_key, r1_key], [1, 2, 3], 3)
    return multi_sig
