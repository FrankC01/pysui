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
# pylint: disable=too-many-instance-attributes

"""Transaction MultiSig Signing."""

from typing import Optional, Union
from deprecated.sphinx import versionadded, versionchanged

from pysui import SuiAddress, SyncClient, handle_result, ObjectID, AsyncClient
from pysui.sui.sui_builders.base_builder import sui_builder
from pysui.sui.sui_builders.exec_builders import _MoveCallTransactionBuilder
from pysui.sui.sui_crypto import MultiSig, SuiPublicKey
from pysui.sui.sui_txresults.single_tx import SuiCoinObject
from pysui.sui.sui_types.collections import SuiArray
from pysui.sui.sui_types.scalars import SuiSignature, SuiString

from pysui.sui.sui_types import bcs

_PAY_GAS: int = 4000000


@versionadded(version="0.28.0", reason="Deprecating PayAllSui builder.")
class _ConsolidateSui(_MoveCallTransactionBuilder):
    """_ConsolidateSui When executed, Send all SUI coins to one recipient."""

    @sui_builder()
    def __init__(
        self,
        *,
        signer: SuiAddress,
        input_coins: SuiArray[ObjectID],
        recipient: SuiAddress,
        gas_budget: SuiString,
    ) -> None:
        """__init__ PayAllSui Builder initializer.

        :param signer: the transaction signer's Sui address
        :type signer: SuiAddress
        :param input_coins: the Sui coins to be used in this transaction, including the coin for gas payment.
        :type input_coins: SuiArray[ObjectID]
        :param recipient: the recipient Sui address
        :type recipient: SuiAddress
        :param gas_budget: the gas budget, the transaction will fail if the gas cost exceed the budget
        :type gas_budget: SuiString
        """
        super().__init__("unsafe_payAllSui")


@versionadded(version="0.17.0", reason="Standardize on signing permutations")
@versionadded(
    version="0.21.1", reason="Support subset pubkey address generation"
)
class SigningMultiSig:
    """Wraps the mutli-sig along with pubkeys to use in SuiTransaction."""

    def __init__(self, msig: MultiSig, pub_keys: list[SuiPublicKey]):
        """."""
        self.multi_sig = msig
        self.pub_keys = pub_keys
        self.indicies = msig.validate_signers(pub_keys)
        self._address = self.multi_sig.address

    @property
    def signing_address(self) -> str:
        """."""
        return self._address


@versionadded(version="0.26.0", reason="Refactor for Async support.")
class _SignerBlockBase:
    """."""

    def __init__(
        self,
        *,
        sender: Optional[Union[SuiAddress, SigningMultiSig]] = None,
        sponsor: Optional[Union[SuiAddress, SigningMultiSig]] = None,
        # additional_signers: Optional[list[Union[SuiAddress, SigningMultiSig]]] = None,
    ):
        """__init__ Create a signer block.

        :param sender: The primary sender/signer, defaults to None
        :type sender: Optional[Union[SuiAddress, SigningMultiSig]], optional
        :param sponsor: An optional sponsor for transaction, defaults to None
        :type sponsor: Optional[Union[SuiAddress, SigningMultiSig]], optional
        """
        self._sender = sender
        self._sponsor = sponsor
        self._merge_to_gas: bool = False
        # self._merge_to_gas:list = []
        # self._additional_signers = additional_signers if additional_signers else []

    def _merging_to_gas(self):
        """."""
        self._merge_to_gas = True

    @property
    def sender(self) -> Union[SuiAddress, SigningMultiSig]:
        """Return the current sender used in signing."""
        return self._sender

    @sender.setter
    def sender(self, new_sender: Union[SuiAddress, SigningMultiSig]):
        """Set the sender to use in signing the transaction."""
        assert isinstance(new_sender, (SuiAddress, SigningMultiSig))
        self._sender = new_sender

    @property
    def sponsor(self) -> Union[None, Union[SuiAddress, SigningMultiSig]]:
        """Get who, if any, may be acting as payer of transaction."""
        return self._sponsor

    @sponsor.setter
    def sponser(self, new_sponsor: Union[SuiAddress, SigningMultiSig]):
        """Set the sponsor to used to pay for transaction. This also signs the transaction."""
        assert isinstance(new_sponsor, (SuiAddress, SigningMultiSig))
        self._sponsor = new_sponsor

    # @property
    # def additional_signers(self) -> list[Union[SuiAddress, SigningMultiSig]]:
    #     """Gets the list of additional signers although Sui doesn't seem to support at the moment."""
    #     return self._additional_signers

    # @additional_signers.setter
    # def additional_signers(self, new_additional_signers: list[Union[SuiAddress, SigningMultiSig]]):
    #     """sets the list of additional signers although Sui doesn't seem to support at the moment."""
    #     new_additional_signers = new_additional_signers if new_additional_signers else []
    #     for additional_signer in new_additional_signers:
    #         assert isinstance(additional_signer, (SuiAddress, SigningMultiSig))
    #     self._additional_signers = new_additional_signers

    # def add_additioinal_signer(self, additional_signer: Union[SuiAddress, SigningMultiSig]):
    #     """Add another signer to the additional_signers list."""
    #     assert isinstance(additional_signer, (SuiAddress, SigningMultiSig))
    #     self._additional_signers.append(additional_signer)

    def _get_potential_signatures(
        self,
    ) -> list[Union[SuiAddress, SigningMultiSig]]:
        """Internal flattening of signers."""
        result_list = []
        if self.sender:
            result_list.append(self.sender)
        if self.sponsor:
            result_list.append(self._sponsor)
        return result_list
        # result_list.extend(self.additional_signers)
        # return result_list

    @versionchanged(
        version="0.21.2", reason="Fix regression on MultiSig signing."
    )
    def get_signatures(
        self, *, client: SyncClient, tx_bytes: str
    ) -> SuiArray[SuiSignature]:
        """Get all the signatures needed for the transaction."""
        sig_list: list[SuiSignature] = []
        for signer in self._get_potential_signatures():
            if isinstance(signer, SuiAddress):
                sig_list.append(
                    client.config.keypair_for_address(signer).new_sign_secure(
                        tx_bytes
                    )
                )
            else:
                sig_list.append(
                    signer.multi_sig.sign(tx_bytes, signer.pub_keys)
                )
        return SuiArray(sig_list)


@versionadded(version="0.17.0", reason="Standardize on signing permutations")
@versionchanged(
    version="0.18.0",
    reason="Removed additional_signers as not supported by Sui at the moment.",
)
@versionchanged(version="0.26.0", reason="Refactor to support Async.")
class SignerBlock(_SignerBlockBase):
    """Manages the potential signers and resolving the gas object for paying."""

    def __init__(
        self,
        *,
        sender: Optional[Union[SuiAddress, SigningMultiSig]] = None,
        sponsor: Optional[Union[SuiAddress, SigningMultiSig]] = None,
        # additional_signers: Optional[list[Union[SuiAddress, SigningMultiSig]]] = None,
    ):
        """__init__ Create a signer block.

        :param sender: The primary sender/signer, defaults to None
        :type sender: Optional[Union[SuiAddress, SigningMultiSig]], optional
        :param sponsor: An optional sponsor for transaction, defaults to None
        :type sponsor: Optional[Union[SuiAddress, SigningMultiSig]], optional
        """
        super().__init__(sender=sender, sponsor=sponsor)

    @versionchanged(
        version="0.21.1", reason="Corrected when using multisig senders."
    )
    @versionchanged(
        version="0.28.0", reason="Use _ConsolidateSui if coins needed for gas."
    )
    @versionchanged(
        version="0.30.0",
        reason="Leverage multiple gas objects passed for paying in transaction.",
    )
    def get_gas_object(
        self,
        *,
        client: SyncClient,
        budget: int,
        objects_in_use: list,
        merge_coin: bool,
        gas_price: int,
    ) -> bcs.GasData:
        """Produce a gas object from either the sponsor or the sender."""
        # Either a sponsor (priority) or sender will pay for this
        who_pays = self._sponsor if self._sponsor else self._sender
        # If both not set, Fail
        if not who_pays:
            raise ValueError(
                "Both SuiTransaction sponor and sender are null. Complete at least one before execute."
            )
        if isinstance(who_pays, SuiAddress):
            whose_gas = who_pays.address
            who_pays = who_pays.address
        else:
            whose_gas = who_pays.signing_address  # as_sui_address
            who_pays = who_pays.signing_address
        # who_pays = who_pays if isinstance(who_pays, SuiAddress) else who_pays.multi_sig.as_sui_address
        owner_coins: list[SuiCoinObject] = handle_result(
            client.get_gas(whose_gas)
        ).data
        # Get whatever gas objects below to whoever is paying
        # and filter those not in use
        use_coin: SuiCoinObject = None
        if self._merge_to_gas:
            owner_gas: list[SuiCoinObject] = [owner_coins[0]]
        else:
            owner_gas: list[SuiCoinObject] = [
                x
                for x in owner_coins
                if x.coin_object_id not in objects_in_use
                and int(x.balance) >= budget
            ]

        # If there is no remaining gas but _merge_to_gas is found
        # Find that which satisfies budget
        # If we have a result of the main filter, use first
        if owner_gas:
            use_coin = owner_gas[0]
        # Otherwise if we can merge
        elif merge_coin:
            alt_gas: list[SuiCoinObject] = [
                bcs.ObjectReference(
                    bcs.Address.from_str(x.object_id),
                    int(x.version),
                    bcs.Digest.from_str(x.digest),
                )
                for x in owner_coins
                if x.coin_object_id not in objects_in_use
            ]

            return bcs.GasData(
                alt_gas,
                bcs.Address.from_str(whose_gas),
                int(gas_price),
                int(budget),
            )

            # if alt_gas:
            #     enh_budget = budget + _PAY_GAS
            #     to_pay: list[str] = []
            #     accum_pay: int = 0
            #     for ogas in alt_gas:
            #         to_pay.append(ogas)
            #         accum_pay += int(ogas.balance)
            #         if accum_pay >= enh_budget:
            #             break
            #     if accum_pay >= enh_budget:
            #         handle_result(
            #             client.execute(
            #                 _ConsolidateSui(
            #                     signer=who_pays,
            #                     input_coins=SuiArray(
            #                         [
            #                             ObjectID(x.coin_object_id)
            #                             for x in to_pay
            #                         ]
            #                     ),
            #                     recipient=who_pays,
            #                     gas_budget=str(_PAY_GAS),
            #                 )
            #             )
            #         )
            #         use_coin = to_pay[0]
        # If we have a coin to use, return the GasDataObject
        if use_coin:
            return bcs.GasData(
                [
                    bcs.ObjectReference(
                        bcs.Address.from_str(use_coin.coin_object_id),
                        int(use_coin.version),
                        bcs.Digest.from_str(use_coin.digest),
                    )
                ],
                bcs.Address.from_str(whose_gas),
                int(gas_price),
                int(budget),
            )
        raise ValueError(f"{who_pays} has nothing to pay with.")

    @versionadded(version="0.26.0", reason="Added to support async operations")
    @versionchanged(
        version="0.28.0", reason="Use _ConsolidateSui if coins needed for gas."
    )
    @versionchanged(
        version="0.30.0",
        reason="Leverage multiple gas objects passed for paying in transaction.",
    )
    async def get_gas_object_async(
        self,
        *,
        client: AsyncClient,
        budget: int,
        objects_in_use: list,
        merge_coin: bool,
        gas_price: int,
    ) -> bcs.GasData:
        """Produce a gas object from either the sponsor or the sender."""
        # Either a sponsor (priority) or sender will pay for this
        who_pays = self._sponsor if self._sponsor else self._sender
        # If both not set, Fail
        if not who_pays:
            raise ValueError(
                "Both SuiTransaction sponor and sender are null. Complete those before execute."
            )
        if isinstance(who_pays, SuiAddress):
            whose_gas = who_pays.address
            who_pays = who_pays.address
        else:
            whose_gas = who_pays.signing_address  # as_sui_address
            who_pays = who_pays.signing_address
        # who_pays = who_pays if isinstance(who_pays, SuiAddress) else who_pays.multi_sig.as_sui_address
        owner_coins: list[SuiCoinObject] = handle_result(
            await client.get_gas(whose_gas)
        ).data
        # Get whatever gas objects below to whoever is paying
        # and filter those not in use
        use_coin: SuiCoinObject = None
        if self._merge_to_gas:
            owner_gas: list[SuiCoinObject] = [owner_coins[0]]
        else:
            owner_gas: list[SuiCoinObject] = [
                x
                for x in owner_coins
                if x.coin_object_id not in objects_in_use
                and int(x.balance) >= budget
            ]

        # If there is no remaining gas but _merge_to_gas is found
        # Find that which satisfies budget
        # If we have a result of the main filter, use first
        if owner_gas:
            use_coin = owner_gas[0]
        # Otherwise if we can merge
        elif merge_coin:
            alt_gas: list[SuiCoinObject] = [
                bcs.ObjectReference(
                    bcs.Address.from_str(x.object_id),
                    int(x.version),
                    bcs.Digest.from_str(x.digest),
                )
                for x in owner_coins
                if x.coin_object_id not in objects_in_use
            ]

            return bcs.GasData(
                alt_gas,
                bcs.Address.from_str(whose_gas),
                int(gas_price),
                int(budget),
            )
            # alt_gas: list[SuiCoinObject] = [
            #     x
            #     for x in owner_coins
            #     if x.coin_object_id not in objects_in_use
            # ]
            # if alt_gas:
            #     enh_budget = budget + _PAY_GAS
            #     to_pay: list[str] = []
            #     accum_pay: int = 0
            #     for ogas in alt_gas:
            #         to_pay.append(ogas)
            #         accum_pay += int(ogas.balance)
            #         if accum_pay >= enh_budget:
            #             break
            #     if accum_pay >= enh_budget:
            #         handle_result(
            #             await client.execute(
            #                 _ConsolidateSui(
            #                     signer=who_pays,
            #                     input_coins=SuiAddress(
            #                         [
            #                             ObjectID(x.coin_object_id)
            #                             for x in to_pay
            #                         ]
            #                     ),
            #                     recipient=who_pays,
            #                     gas_budget=str(_PAY_GAS),
            #                 )
            #             )
            #         )
            #         use_coin = to_pay[0]
        # If we have a coin to use, return the GasDataObject
        if use_coin:
            return bcs.GasData(
                [
                    bcs.ObjectReference(
                        bcs.Address.from_str(use_coin.coin_object_id),
                        int(use_coin.version),
                        bcs.Digest.from_str(use_coin.digest),
                    )
                ],
                bcs.Address.from_str(whose_gas),
                gas_price,
                budget,
            )
        raise ValueError(f"{who_pays} has nothing to pay with.")
