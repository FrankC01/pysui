#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""PrivateFundsTransaction — Confidential Transfer transaction builder.

Subclass of :class:`~pysui.sui.sui_common.async_txn.AsyncSuiTransaction` that adds
the Confidential Transfer (Private Funds) programmable-transaction operations.

Instances are created through the protocol client factory with
``client.transaction(private_fund=True)`` (GraphQL protocol only); the factory runs
the ``pysui-crypto`` capability gate before construction, so neither ``__init__`` nor
the per-operation methods re-gate.
"""

from typing import Union

from pysui.sui.sui_common.async_txn import AsyncSuiTransaction
from pysui.private_transfer.config import PrivateFundsConfig
from pysui.private_transfer import utils
from pysui.sui.sui_common.instrumentation import instrumented
from pysui.sui.sui_bcs import bcs
import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot


class PrivateFundsTransaction(AsyncSuiTransaction):
    """Confidential Transfer transaction builder.

    Extends :class:`AsyncSuiTransaction` with Private Funds operations
    (registration, wrap, merge, transfer, unwrap, key/auditor management).

    The active Private Funds network configuration is resolved eagerly at
    construction from the owning client's :class:`PysuiConfiguration`
    (``self.client.config``) and held for the transaction's lifetime.
    """

    def __init__(self, **kwargs) -> None:
        """Initialize the Private Funds transaction builder.

        The pysui-crypto capability gate is enforced by the client factory
        (``client.transaction(private_fund=True)``) prior to construction, so it
        is not repeated here.

        :param kwargs: Keyword arguments forwarded to
            :class:`AsyncSuiTransaction` (``client`` required; optional
            ``initial_sender``, ``initial_sponsor``, ``compress_inputs``,
            ``builder``, ``arg_parser``, ``object_cache``).
        """
        super().__init__(**kwargs)
        self._pf_config: PrivateFundsConfig = PrivateFundsConfig(
            pysui_config=self.client.config
        )

    @property
    def private_funds_config(self) -> PrivateFundsConfig:
        """Return the resolved Private Funds configuration for this transaction.

        :return: The Private Funds configuration bound to the active profile.
        :rtype: PrivateFundsConfig
        """
        return self._pf_config

    @instrumented(
        "pysui.private_transfer.transaction.PrivateFundsTransaction.register_private_funds"
    )
    async def register_private_funds(
        self, *, coin_type: str, owner: str, elgamal_public_key: bytes
    ) -> None:
        """Build the one-time Confidential Transfer account-registration PTB.

        Assembles the complete atomic registration transaction for ``owner`` under
        coin type ``T`` (``coin_type``): create the account, authorize the sender,
        register the owner's ElGamal public key with no auditors, and share the
        account. This is the entire transaction — the caller drives simulation or
        execution of the built builder afterward.

        :param coin_type: The confidential coin type ``T`` (fully-qualified type string).
        :type coin_type: str
        :param owner: The Sui address being registered (the account owner).
        :type owner: str
        :param elgamal_public_key: The owner's 32-byte ElGamal (Confidential Transfer)
            public key; passed to ``ristretto255::g_from_bytes`` to build the on-chain
            ``group_ops::Element<G>`` value.
        :type elgamal_public_key: bytes
        """
        group = self._pf_config.active_group
        package_id = group.package_id
        confidential_token = utils.confidential_token_id(
            package_id=package_id,
            token_registry_id=group.token_registry,
            coin_type=coin_type,
        )
        account = await self.move_call(
            target=f"{package_id}::contra::new_account",
            arguments=[group.account_registry, owner],
        )
        auth = await self.move_call(
            target=f"{package_id}::contra::authorize_as_sender",
            arguments=[confidential_token],
            type_arguments=[coin_type],
        )
        key_encryption = await self.move_call(
            target="0x1::option::none",
            arguments=[],
            type_arguments=[f"{package_id}::auditors::KeyEncryption"],
        )
        public_key = await self.move_call(
            target="0x2::ristretto255::g_from_bytes",
            arguments=[elgamal_public_key],
        )
        await self.move_call(
            target=f"{package_id}::contra::register",
            arguments=[account, auth, confidential_token, public_key, key_encryption],
            type_arguments=[coin_type],
        )
        await self.move_call(
            target=f"{package_id}::contra::share_account",
            arguments=[account],
        )

    @instrumented(
        "pysui.private_transfer.transaction.PrivateFundsTransaction.wrap_private_funds"
    )
    async def wrap_private_funds(
        self,
        *,
        coin_type: Union[str, bcs.TypeTag],
        receiver_address: Union[str, bcs.Address],
        coin_to_wrap: Union[str, bcs.Argument, sui_prot.Object],
        memo: Union[str, bytes] = b"",
    ) -> None:
        """Build the Confidential Transfer wrap PTB for a whole coin.

        Deposits the entire ``coin_to_wrap`` into ``receiver_address``'s plaintext
        ``public_balance`` — pure Move bookkeeping, no ElGamal key or proof. Wrapped
        value must be merged (``merge_private_funds``) before it can be spent
        confidentially. The whole coin is consumed; pre-split for a partial wrap.

        ``receiver_address`` must already be registered for ``coin_type``
        (``register_private_funds``); wrap aborts otherwise.

        :param coin_type: The confidential coin type ``T`` (type string or ``bcs.TypeTag``).
        :type coin_type: Union[str, bcs.TypeTag]
        :param receiver_address: The recipient's Sui address (``0x`` hex string or ``bcs.Address``).
        :type receiver_address: Union[str, bcs.Address]
        :param coin_to_wrap: The ``Coin<T>`` object to consume — an object id string, a
            ``bcs.Argument``, or an already-resolved ``sui_prot.Object``.
        :type coin_to_wrap: Union[str, bcs.Argument, sui_prot.Object]
        :param memo: Optional opaque metadata emitted in the on-chain wrap event
            (``str`` is utf-8 encoded; defaults to empty).
        :type memo: Union[str, bytes]
        """
        group = self._pf_config.active_group
        package_id = group.package_id
        coin_type_str = (
            coin_type.type_tag_to_str()
            if isinstance(coin_type, bcs.TypeTag)
            else coin_type
        )
        confidential_token = utils.confidential_token_id(
            package_id=package_id,
            token_registry_id=group.token_registry,
            coin_type=coin_type_str,
        )
        pool = utils.pool_id(
            package_id=package_id,
            confidential_token_id=confidential_token,
        )
        receiver = utils.account_id(
            package_id=package_id,
            account_registry_id=group.account_registry,
            owner=receiver_address,
        )
        auth = await self.move_call(
            target=f"{package_id}::contra::authorize_as_sender",
            arguments=[confidential_token],
            type_arguments=[coin_type_str],
        )
        await self.move_call(
            target=f"{package_id}::contra::wrap",
            arguments=[
                receiver,
                auth,
                confidential_token,
                "0x403",
                pool,
                coin_to_wrap,
                memo,
            ],
            type_arguments=[coin_type_str],
        )

    @instrumented(
        "pysui.private_transfer.transaction.PrivateFundsTransaction.merge_private_funds"
    )
    async def merge_private_funds(
        self,
        *,
        coin_type: Union[str, bcs.TypeTag],
        account: str,
    ) -> None:
        """Build the Confidential Transfer merge PTB for an owner's account.

        Folds all pending (encrypted) deposits and the plaintext ``public_balance``
        for ``coin_type`` into the confidential ``active`` balance of ``account``,
        zeroing ``public_balance``. Must be done before wrapped/deposited value can
        be spent in a confidential transfer. Owner-only: the transaction sender must
        be the account owner (any ``Auth<T>`` for the owner is accepted).

        :param coin_type: The confidential coin type ``T`` (type string or ``bcs.TypeTag``).
        :type coin_type: Union[str, bcs.TypeTag]
        :param account: The owner's ``Account`` object id (``0x`` hex string).
        :type account: str
        """
        group = self._pf_config.active_group
        package_id = group.package_id
        coin_type_str = (
            coin_type.type_tag_to_str()
            if isinstance(coin_type, bcs.TypeTag)
            else coin_type
        )
        confidential_token = utils.confidential_token_id(
            package_id=package_id,
            token_registry_id=group.token_registry,
            coin_type=coin_type_str,
        )
        auth = await self.move_call(
            target=f"{package_id}::contra::authorize_as_sender",
            arguments=[confidential_token],
            type_arguments=[coin_type_str],
        )
        await self.move_call(
            target=f"{package_id}::contra::merge",
            arguments=[account, auth],
            type_arguments=[coin_type_str],
        )
