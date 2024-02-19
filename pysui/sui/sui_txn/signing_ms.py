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
from pysui.sui.sui_crypto import MultiSig, SuiPublicKey, BaseMultiSig
from pysui.sui.sui_txresults.single_tx import SuiCoinObject
from pysui.sui.sui_types.collections import SuiArray
from pysui.sui.sui_types.scalars import SuiSignature, SuiString

from pysui.sui.sui_types import bcs


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
@versionadded(version="0.21.1", reason="Support subset pubkey address generation")
@versionchanged(version="0.35.0", reason="Change msig to BaseMultiSig")
class SigningMultiSig:
    """Wraps the mutli-sig along with pubkeys to use in SuiTransaction."""

    def __init__(self, msig: BaseMultiSig, pub_keys: list[SuiPublicKey]):
        """."""
        self.multi_sig = msig
        self.pub_keys = pub_keys
        self.indicies = msig.validate_signers(pub_keys)
        self._address = self.multi_sig.address
        self._can_sign_msg = isinstance(msig, MultiSig)

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
    def sponsor(self, new_sponsor: Union[SuiAddress, SigningMultiSig]):
        """Set the sponsor to used to pay for transaction. This also signs the transaction."""
        assert isinstance(new_sponsor, (SuiAddress, SigningMultiSig))
        self._sponsor = new_sponsor

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

    @versionchanged(version="0.21.2", reason="Fix regression on MultiSig signing.")
    def get_signatures(
        self, *, client: SyncClient, tx_bytes: str
    ) -> SuiArray[SuiSignature]:
        """Get all the signatures needed for the transaction."""
        sig_list: list[SuiSignature] = []
        for signer in self._get_potential_signatures():
            if isinstance(signer, SuiAddress):
                sig_list.append(
                    client.config.keypair_for_address(signer).new_sign_secure(tx_bytes)
                )
            else:
                if signer._can_sign_msg:
                    sig_list.append(signer.multi_sig.sign(tx_bytes, signer.pub_keys))
                else:
                    raise ValueError("BaseMultiSig can not sign in execution")
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
    ):
        """__init__ Create a signer block.

        :param sender: The primary sender/signer, defaults to None
        :type sender: Optional[Union[SuiAddress, SigningMultiSig]], optional
        :param sponsor: An optional sponsor for transaction, defaults to None
        :type sponsor: Optional[Union[SuiAddress, SigningMultiSig]], optional
        """
        super().__init__(sender=sender, sponsor=sponsor)

    @versionadded(version="0.30.0", reason="Refactored from get_gas_object.")
    def _get_payer(self) -> Union[str, ValueError]:
        """Get the payer for the transaction."""
        # Either a sponsor (priority) or sender will pay for this
        who_pays = self._sponsor if self._sponsor else self._sender
        # If both not set, Fail
        if not who_pays:
            raise ValueError(
                "Both SuiTransaction sponor and sender are null. Complete at least one before execute."
            )
        if isinstance(who_pays, SuiAddress):
            who_pays = who_pays.address
        else:
            who_pays = who_pays.signing_address

        return who_pays

    @property
    def payer_address(self) -> str:
        """Fetch payer address."""
        return self._get_payer()

    @versionadded(version="0.30.0", reason="Refactored from get_gas_object.")
    @versionadded(version="0.39.0", reason="Change object_in_use type.")
    def _get_gas_data(
        self,
        payer: str,
        owner_coins: list[SuiCoinObject],
        budget: int,
        objects_in_use: dict,
        merge_coin: bool,
        gas_price: int,
    ) -> Union[bcs.GasData, ValueError]:
        """Find the gas to pay for transaction."""
        # Scan for a single coin not in use that satisfies budget
        # but always accumulate and break if we meet threshold based on budget
        have_single = None
        owner_gas: list[SuiCoinObject] = []
        threshold: int = 0
        for o_gas in owner_coins:
            # Eliminate any gas in use for commands
            if o_gas.object_id not in objects_in_use:
                # If the potential for one coin that satisfied budget exists
                if int(o_gas.balance) >= budget and not have_single:
                    have_single = o_gas
                owner_gas.append(o_gas)
                threshold += int(o_gas.balance)
                # If we have enough coins to satisfy budget
                if threshold >= budget:
                    break

        # If a merge_to_gas was part of transaction commands,
        # use the first object
        gas_data: list = None
        if self._merge_to_gas:
            use_coin = owner_coins[0]
            gas_data = [
                bcs.ObjectReference(
                    bcs.Address.from_str(use_coin.coin_object_id),
                    int(use_coin.version),
                    bcs.Digest.from_str(use_coin.digest),
                )
            ]

        # Otherwise, if we have one object that satisfies the budget
        elif have_single:
            gas_data = [
                bcs.ObjectReference(
                    bcs.Address.from_str(have_single.coin_object_id),
                    int(have_single.version),
                    bcs.Digest.from_str(have_single.digest),
                )
            ]
        # Else check that we meet the threshold
        elif threshold >= budget:
            # If we do and merge_gas_budget was specified on the SuiTransaction
            if merge_coin:
                gas_data = [
                    bcs.ObjectReference(
                        bcs.Address.from_str(x.object_id),
                        int(x.version),
                        bcs.Digest.from_str(x.digest),
                    )
                    for x in owner_gas
                ]
            else:
                raise ValueError(
                    f"{payer} has enough gas but merge_gas_budget not set on transaction."
                )

        else:
            raise ValueError(f"{payer} has nothing to pay with.")

        return bcs.GasData(
            gas_data,
            bcs.Address.from_str(payer),
            int(gas_price),
            int(budget),
        )

    @versionchanged(version="0.21.1", reason="Corrected when using multisig senders.")
    @versionchanged(
        version="0.28.0", reason="Use _ConsolidateSui if coins needed for gas."
    )
    @versionchanged(
        version="0.30.0",
        reason="Leverage multiple gas objects passed for paying in transaction.",
    )
    @versionchanged(
        version="0.39.0",
        reason="Change object_in_use type",
    )
    def get_gas_object(
        self,
        *,
        client: SyncClient,
        budget: int,
        objects_in_use: dict,
        merge_coin: bool,
        gas_price: int,
    ) -> Union[bcs.GasData, ValueError]:
        """Produce a gas object from either the sponsor or the sender."""
        # Either a sponsor (priority) or sender will pay for this
        who_pays = self._get_payer()
        # Get current gas objects for payer
        gas_result = client.get_gas(who_pays)
        if gas_result.is_ok():
            owner_coins: list[SuiCoinObject] = gas_result.result_data.data
        else:
            raise ValueError(
                f"Error {gas_result.result_string} attemepting to fetch gas objects for {who_pays}"
            )
        return self._get_gas_data(
            who_pays,
            owner_coins,
            budget,
            objects_in_use,
            merge_coin,
            gas_price,
        )

    @versionadded(version="0.26.0", reason="Added to support async operations")
    @versionchanged(
        version="0.28.0", reason="Use _ConsolidateSui if coins needed for gas."
    )
    @versionchanged(
        version="0.30.0",
        reason="Leverage multiple gas objects passed for paying in transaction.",
    )
    @versionchanged(
        version="0.39.0",
        reason="Change object_in_use registry type.",
    )
    async def get_gas_object_async(
        self,
        *,
        client: AsyncClient,
        budget: int,
        objects_in_use: dict,
        merge_coin: bool,
        gas_price: int,
    ) -> bcs.GasData:
        """Produce a gas object from either the sponsor or the sender."""
        # Either a sponsor (priority) or sender will pay for this
        who_pays = self._get_payer()
        # Get current gas objects for payer
        gas_result = await client.get_gas(who_pays)
        if gas_result.is_ok():
            owner_coins: list[SuiCoinObject] = gas_result.result_data.data
        else:
            raise ValueError(
                f"Error {gas_result.result_string} attemepting to fetch gas objects for {who_pays}"
            )
        return self._get_gas_data(
            who_pays,
            owner_coins,
            budget,
            objects_in_use,
            merge_coin,
            gas_price,
        )
