#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Pysui Signing Block builder that works with GraphQL connection."""

from typing import Optional, Union
from pysui import PysuiConfiguration
from pysui.sui.sui_crypto import MultiSig, BaseMultiSig, SuiPublicKey

import pysui.sui.sui_pgql.pgql_types as pgql_type


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


class SignerBlock:
    """."""

    def __init__(
        self,
        *,
        sender: Optional[Union[str, SigningMultiSig]] = None,
        sponsor: Optional[Union[str, SigningMultiSig]] = None,
    ):
        """__init__ Create a signer block.

        :param sender: The primary sender/signer, defaults to None
        :type sender: Optional[Union[str, SigningMultiSig]], optional
        :param sponsor: An optional sponsor for transaction, defaults to None
        :type sponsor: Optional[Union[str, SigningMultiSig]], optional
        """
        self._sender = sender
        self._sponsor = sponsor
        self._merge_to_gas: bool = False

    @property
    def sender(self) -> Union[str, SigningMultiSig]:
        """Return the current sender used in signing."""
        return self._sender

    @property
    def sender_str(self) -> str:
        """Return the current sender used in signing."""
        return (
            self._sender
            if isinstance(self._sender, str)
            else self._sender.signing_address
        )

    @sender.setter
    def sender(self, new_sender: Union[str, SigningMultiSig]):
        """Set the sender to use in signing the transaction."""
        assert isinstance(new_sender, (str, SigningMultiSig))
        self._sender = new_sender

    @property
    def sponsor(self) -> Union[None, Union[str, SigningMultiSig]]:
        """Get who, if any, may be acting as payer of transaction."""
        return self._sponsor

    @property
    def sponsor_str(self) -> Union[str, None]:
        """Return the current sender used in signing."""
        if not self._sponsor:
            return None
        return (
            self._sponsor
            if isinstance(self._sponsor, str)
            else self._sponsor.signing_address
        )

    @sponsor.setter
    def sponsor(self, new_sponsor: Union[str, SigningMultiSig]):
        """Set the sponsor to used to pay for transaction. This also signs the transaction."""
        assert isinstance(new_sponsor, (str, SigningMultiSig))
        self._sponsor = new_sponsor

    def _get_payer(self) -> Union[str, ValueError]:
        """Get the payer for the transaction."""
        # Either a sponsor (priority) or sender will pay for this
        who_pays = self._sponsor if self._sponsor else self._sender
        # If both not set, Fail
        if not who_pays:
            raise ValueError(
                "Both SuiTransaction sponor and sender are null. Complete at least one before execute."
            )
        if isinstance(who_pays, str):
            who_pays = who_pays
        else:
            who_pays = who_pays.signing_address

        return who_pays

    @property
    def payer_address(self) -> str:
        """Fetch payer address."""
        return self._get_payer()

    def _get_potential_signatures(
        self,
    ) -> list[Union[str, SigningMultiSig]]:
        """Internal flattening of signers."""
        result_list = []
        if self.sender:
            result_list.append(self.sender)
        if self.sponsor:
            result_list.append(self._sponsor)
        return result_list

    def get_signatures(self, *, config: PysuiConfiguration, tx_bytes: str) -> list[str]:
        """Get all the signatures needed for the transaction."""
        sig_list: list[str] = []
        for signer in self._get_potential_signatures():
            if isinstance(signer, str):

                sig_list.append(
                    config.active_group.keypair_for_address(
                        address=signer
                    ).new_sign_secure(tx_bytes)
                )
            else:
                if signer._can_sign_msg:
                    sig_list.append(signer.multi_sig.sign(tx_bytes, signer.pub_keys))
                else:
                    raise ValueError("BaseMultiSig can not sign for execution")
        return [x.value for x in sig_list]
