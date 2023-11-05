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

"""SuiTransaction Serialize/Deserialize model."""

from functools import partial, reduce
from pysui import SuiConfig, SuiAddress, SyncClient, handle_result
from pysui.sui.sui_crypto import MultiSig
from pysui.sui.sui_txn.signing_ms import SignerBlock, SigningMultiSig
from pysui.sui.sui_txn.transaction_builder import (
    ProgrammableTransactionBuilder,
)
from pysui.sui.sui_txresults.common import GenericRef
from pysui.sui.sui_txresults.single_tx import (
    AddressOwner,
    ImmutableOwner,
    SharedOwner,
)
import pysui.sui.sui_types.bcs as bcs
from pysui.sui.sui_types.scalars import SuiU16


def _ser_single_signer(cfg: SuiConfig, addy: SuiAddress) -> bcs.TxSender:
    """Serialize a single, simple signer (sender or sponsor)."""
    kp = cfg.keypair_for_address(addy)
    pk = kp.public_key
    return bcs.TxSender(
        "Single",
        bcs.TxSenderSingle(
            bcs.Address.from_str(addy.address),
            bcs.MsNewPublicKey.from_pubkey(pk),
        ),
    )


def _ser_multi_signer(sms: SigningMultiSig) -> bcs.TxSender:
    """Serialize a multi-sig signer (sender or sponsor)."""
    msig = sms.multi_sig
    base_address = sms.signing_address
    base_pkeys = msig.public_keys
    weights = msig.weights
    threshold = msig.threshold
    bm_pks: int = 0
    for index in sms.indicies:
        bm_pks |= 1 << index
    return bcs.TxSender(
        "Multi",
        bcs.TxSenderMulti(
            bcs.Address.from_str(base_address),
            [
                bcs.Address.from_str(SuiAddress.from_bytes(i.scheme_and_key()).address)
                for i in base_pkeys
            ],
            [
                bcs.MsNewPublicKey.from_pubkey(i, weights[d])
                for d, i in enumerate(base_pkeys)
            ],
            threshold,
            bcs.MsBitmap(bm_pks),
        ),
    )


def ser_sender_and_sponsor(
    signer_block: SignerBlock, config: SuiConfig
) -> tuple[bcs.TxSender, bcs.TxSender]:
    """Serialize sender and/or sponsor."""
    # Determine sender
    if isinstance(signer_block.sender, SuiAddress):
        sender = _ser_single_signer(config, signer_block.sender)
    elif isinstance(signer_block.sender, SigningMultiSig):
        sender = _ser_multi_signer(signer_block.sender)
    else:
        sender = bcs.TxSender("NotSet")

    if isinstance(signer_block.sponsor, SuiAddress):
        sponsor = _ser_single_signer(config, signer_block.sender)
    elif isinstance(signer_block.sponsor, SigningMultiSig):
        sponsor = _ser_multi_signer(signer_block.sponsor)
    else:
        sponsor = bcs.TxSender("NotSet")

    return sender, sponsor


def ser_transaction_builder(
    builder: ProgrammableTransactionBuilder,
) -> bcs.TxTransaction:
    """Serialize the transaction builder data."""
    freq = [bcs.TxStringInt(x, y) for x, y in builder.command_frequency.items()]
    obj_in_use = [
        bcs.TxStringString(x[0], x[1]) for x in builder.objects_registry.items()
    ]
    return bcs.TxTransaction(
        freq, obj_in_use, list(builder.inputs.keys()), builder.commands
    )


def _de_ser_single_signer(tx_send: bcs.TxSenderSingle, cfg: SuiConfig) -> SuiAddress:
    """."""
    addy = tx_send.Address.to_sui_address()
    kp = cfg.keypair_for_address(addy)
    pub_bytes = bytes(tx_send.SigningPublicKeys.value.PublicKey)
    assert pub_bytes == kp.public_key.key_bytes
    return addy


def _bits(n: int) -> int:
    """Multi-sig Bitmap bits peeler."""
    while n:
        b = n & (~n + 1)
        yield b - 1
        n ^= b


def _de_ser_multi_signer(
    tx_send: bcs.TxSenderMulti, config: SuiConfig
) -> SigningMultiSig:
    """."""
    # Addresses of multi-sig members
    mc_addys = [x.to_sui_address() for x in tx_send.MultiSigKeyAddress]
    # Pubkey bytes of multi-sig members
    mc_pubbytes = [bytes(x.value.PublicKey) for x in tx_send.MultiSigPublicKeys]
    # Weights of multi-sig members
    mc_weights = [x.value.Weight for x in tx_send.MultiSigPublicKeys]
    # Resolve keypairs in addresses
    mc_kps = [config.keypair_for_address(x) for x in mc_addys]
    # Confirm pubkey byte matches
    for i in range(len(mc_kps)):
        assert mc_pubbytes[i] == mc_kps[i].public_key.key_bytes, "PublicKey mismatch"
    # Create the multi-sig
    msig = MultiSig(mc_kps, mc_weights, tx_send.Threshold)
    # Confirm the addresses match
    assert msig.address == tx_send.MutliSigAddress.to_address_str()
    # Create the signing multi-sig
    indices = [bit for bit in _bits(tx_send.SigningKeyIndexes.Bitmap)]
    smsig = SigningMultiSig(msig, [mc_kps[x].public_key for x in indices])
    assert indices == smsig.indicies, "Multi-sig indices mismatch"

    return smsig


def deser_sender_and_sponsor(
    sender: bcs.TxSender, sponsor: bcs.TxSender, config: SuiConfig
) -> SignerBlock:
    """."""
    sblock = SignerBlock()
    # Peel off sender
    if sender.enum_name == "Single":
        sblock.sender = _de_ser_single_signer(sender.value, config)
    elif sender.enum_name == "Multi":
        sblock.sender = _de_ser_multi_signer(sender.value, config)
    # Peel of sponsor
    if sponsor.enum_name == "Single":
        sblock.sponsor = _de_ser_single_signer(sponsor.value, config)
    elif sponsor.enum_name == "Multi":
        sblock.sponsor = _de_ser_multi_signer(sponsor.value, config)
    return sblock


def _deser_inputs(
    obj_dict: dict, objs_in_use: dict, accum: dict, input: bcs.BuilderArg
) -> dict:
    """."""
    if input.enum_name == "Pure":
        accum[input] = bcs.CallArg(input.enum_name, input.value)
    elif input.enum_name == "Object":
        obj_addy = input.value.to_address_str()
        if obj_addy in obj_dict:
            item = obj_dict[obj_addy]
            if isinstance(item.owner, (AddressOwner, ImmutableOwner)):
                obj_ref = GenericRef(item.object_id, item.version, item.digest)
                b_obj_arg = bcs.ObjectArg(
                    objs_in_use[item.object_id],
                    bcs.ObjectReference.from_generic_ref(obj_ref),
                )
            elif isinstance(item.owner, SharedOwner):
                b_obj_arg = bcs.ObjectArg(
                    "SharedObject",
                    bcs.SharedObjectReference.from_object_read(item),
                )
            else:
                raise ValueError(
                    f"{item} is not an object_ref or shared object known object"
                )
            accum[input] = bcs.CallArg(input.enum_name, b_obj_arg)
        else:
            raise ValueError(f"{obj_addy} not a known object")
    return accum


def deser_transaction_builder(
    tx_builder: bcs.TxTransaction,
    builder: ProgrammableTransactionBuilder,
    config: SuiConfig,
):
    """."""
    freq_dict = {el.Key: el.Value for el in tx_builder.Frequencies}
    objs_in_use = {x.Key: x.Value for x in tx_builder.ObjectsInUse}
    # objs_in_use = [x.to_address_str() for x in tx_builder.ObjectsInUse]
    client = SyncClient(config)
    # Resolve any objects in use
    obj_list = list(objs_in_use.keys())
    data_objs_dict = {
        dobj.object_id: dobj for dobj in handle_result(client.get_objects_for(obj_list))
    }
    # Make inputs dictionary
    inputs = reduce(
        partial(_deser_inputs, data_objs_dict, objs_in_use), tx_builder.Inputs, {}
    )
    builder.command_frequency = freq_dict
    builder.inputs = inputs
    builder.objects_registry = objs_in_use
    builder.commands = tx_builder.Commands.copy()
