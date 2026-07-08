#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""PrivateFundsTransaction — Confidential Transfer transaction builder.

Subclass of :class:`~pysui.sui.sui_common.async_txn.AsyncSuiTransaction` that adds
the Confidential Transfer (Private Funds) programmable-transaction operations.

Instances are created through the protocol client factory with
``client.transaction(private_fund=True)`` (GraphQL protocol only); the factory runs
the ``pysui-crypto`` capability gate before construction, so ``__init__`` does not
re-gate. Per-operation methods call :func:`~pysui.private_transfer._ext.raise_for_crypto`
first as a defense-in-depth guard.
"""

from pysui.sui.sui_common.async_txn import AsyncSuiTransaction
from pysui.private_transfer.config import PrivateFundsConfig
from pysui.private_transfer import utils
from pysui.private_transfer._ext import raise_for_crypto


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
        raise_for_crypto()
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
