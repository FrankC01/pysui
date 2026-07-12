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
from pysui.private_transfer import _ext
from pysui.private_transfer import pf_bcs
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

    async def _token_account(
        self, *, coin_type: str, account_id: str
    ) -> pf_bcs.TokenAccount:
        """Fetch the owner's ``TokenAccount<T>`` using this transaction's client.

        Thin delegation to :func:`pysui.private_transfer.utils._token_account`, which
        performs the dynamic-field read and BCS deserialization.

        :param coin_type: The confidential coin type ``T`` (fully-qualified type string).
        :type coin_type: str
        :param account_id: The owner's derived ``Account`` object id (``0x`` hex string).
        :type account_id: str
        :raises ValueError: If the dynamic field query fails, or no
            ``TokenAccount<T>`` for ``coin_type`` is hung off ``account_id``.
        :return: The deserialized ``TokenAccount<T>``.
        :rtype: pf_bcs.TokenAccount
        """
        return await utils._token_account(
            client=self.client,
            package_id=self._pf_config.active_group.package_id,
            account_id=account_id,
            coin_type=coin_type,
        )

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

    @instrumented(
        "pysui.private_transfer.transaction.PrivateFundsTransaction.transfer_private_funds"
    )
    async def transfer_private_funds(
        self,
        *,
        coin_type: Union[str, bcs.TypeTag],
        sender_account: str,
        recipients: list[tuple[Union[str, bcs.Address], int, Union[str, bytes]]],
        sender_private_key: bytes,
        sender_public_key: bytes,
    ) -> None:
        """Build the Confidential Transfer PTB moving amounts to one or more recipients.

        Calls ``contra::batched_transfer`` with parallel ``receiver_pks`` and
        ``receiver_amounts`` vectors, then one ``contra::add_to_batch`` per recipient in
        submission order, then ``contra::finalize``. Each recipient's ``pending`` balance
        is credited and the sender's ``active`` balance is debited by the batch total;
        recipients must ``merge_private_funds`` before the value is spendable.

        The order of ``recipients`` is the submission order: it fixes both the
        ``receiver_amounts`` vector and the ``add_to_batch`` sequence, which the on-chain
        batch consumes positionally.

        The plaintext ``new_balance`` is computed client-side as
        ``current_balance - sum(amounts)``: pysui-crypto is a pure prover and performs no
        overspend check, so the sender's balance is decrypted here and the transfer
        rejected locally when the total exceeds it.

        Sender and every recipient must already be registered for ``coin_type``.

        :param coin_type: The confidential coin type ``T`` (type string or ``bcs.TypeTag``).
        :type coin_type: Union[str, bcs.TypeTag]
        :param sender_account: The sender's derived ``Account`` object id (``0x`` hex string).
        :type sender_account: str
        :param recipients: Ordered ``(recipient_address, amount, memo)`` triples. The memo
            is emitted in that recipient's on-chain transfer event.
        :type recipients: list[tuple[Union[str, bcs.Address], int, Union[str, bytes]]]
        :param sender_private_key: The sender's 32-byte ElGamal private key.
        :type sender_private_key: bytes
        :param sender_public_key: The sender's 32-byte ElGamal public key.
        :type sender_public_key: bytes
        :raises ValueError: If ``recipients`` is empty, or the batch total exceeds the
            sender's decrypted active balance.
        """
        if not recipients:
            raise ValueError("recipients must contain at least one (address, amount, memo) triple")

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

        sender_ta = await self._token_account(
            coin_type=coin_type_str, account_id=sender_account
        )
        old_active_balance = _flatten_encrypted_amount(amount=sender_ta.active.amount)

        recipient_accounts: list[str] = []
        recipient_pks: list[bytes] = []
        amounts: list[int] = []
        memos: list[bytes] = []
        for recipient_address, amount, memo in recipients:
            recipient_account = utils.account_id(
                package_id=package_id,
                account_registry_id=group.account_registry,
                owner=recipient_address,
            )
            recipient_ta = await self._token_account(
                coin_type=coin_type_str, account_id=recipient_account
            )
            recipient_accounts.append(recipient_account)
            recipient_pks.append(bytes(recipient_ta.pk.bytes))
            amounts.append(amount)
            memos.append(memo.encode("utf-8") if isinstance(memo, str) else memo)

        batch_total = sum(amounts)
        current_balance = _ext.decrypt_balance(
            sender_private_key, old_active_balance, _ext.get_bsgs_table()
        )
        if batch_total > current_balance:
            raise ValueError(
                f"Insufficient confidential balance: have {current_balance}, need {batch_total}"
            )
        new_balance = current_balance - batch_total

        session_id = utils.session_id(
            package_id=package_id,
            account_id=sender_account,
            coin_type=coin_type_str,
        )
        proofs = _ext.batched_transfer_proofs(
            sender_private_key,
            sender_public_key,
            old_active_balance,
            list(zip(recipient_pks, amounts)),
            new_balance,
            session_id,
        )

        auth = await self.move_call(
            target=f"{package_id}::contra::authorize_as_sender",
            arguments=[confidential_token],
            type_arguments=[coin_type_str],
        )
        receiver_pks = await self.move_call(
            target=f"{package_id}::decode::g_vector",
            arguments=[recipient_pks],
        )
        encrypted_amounts = [
            await self.move_call(
                target=f"{package_id}::decode::encrypted_amount",
                arguments=[_chunk32(blob=each)],
            )
            for each in proofs["encrypted_amounts"]
        ]
        receiver_amounts = await self.make_move_vector(
            items=encrypted_amounts,
            item_type=f"{package_id}::encrypted_amount::EncryptedAmount",
        )
        consistency_proofs = [
            await self.move_call(
                target=f"{package_id}::decode::consistency_proof",
                arguments=[_chunk32(blob=each)],
            )
            for each in proofs["consistency_proofs"]
        ]
        consistency_proof_vector = await self.make_move_vector(
            items=consistency_proofs,
            item_type=f"{package_id}::encrypted_amount::ConsistencyProof",
        )
        well_formed_proofs = await self.move_call(
            target=f"{package_id}::encrypted_amount::new_well_formed_proof",
            arguments=[proofs["range_proofs"], consistency_proof_vector],
        )
        total_sender_handle = await self.move_call(
            target="0x2::ristretto255::g_from_bytes",
            arguments=[proofs["total_sender_handle"]],
        )
        consistency_proof = await self.move_call(
            target=f"{package_id}::decode::elgamal_proof",
            arguments=[_chunk32(blob=proofs["sender_total_consistency_proof"])],
        )
        seed_point = await self.move_call(
            target="0x2::ristretto255::g_from_bytes",
            arguments=[proofs["seed_point"]],
        )
        new_balance_amount = await self.move_call(
            target=f"{package_id}::decode::encrypted_amount",
            arguments=[_chunk32(blob=proofs["new_balance_amount"])],
        )
        balance_proof = await self.move_call(
            target=f"{package_id}::decode::ddh_proof",
            arguments=[_chunk32(blob=proofs["balance_proof"])],
        )
        batch = await self.move_call(
            target=f"{package_id}::contra::batched_transfer",
            arguments=[
                sender_account,
                auth,
                confidential_token,
                "0x403",
                receiver_pks,
                receiver_amounts,
                well_formed_proofs,
                total_sender_handle,
                consistency_proof,
                seed_point,
                new_balance_amount,
                balance_proof,
            ],
            type_arguments=[coin_type_str],
        )
        for recipient_account, memo_bytes in zip(recipient_accounts, memos):
            batch = await self.move_call(
                target=f"{package_id}::contra::add_to_batch",
                arguments=[batch, recipient_account, memo_bytes, "0x403"],
                type_arguments=[coin_type_str],
            )
        await self.move_call(
            target=f"{package_id}::contra::finalize",
            arguments=[batch],
            type_arguments=[coin_type_str],
        )

    @instrumented(
        "pysui.private_transfer.transaction.PrivateFundsTransaction.unwrap_private_funds"
    )
    async def unwrap_private_funds(
        self,
        *,
        coin_type: Union[str, bcs.TypeTag],
        account: str,
        amount: int,
        account_private_key: bytes,
        account_public_key: bytes,
    ) -> bcs.Argument:
        """Build the Confidential Transfer unwrap PTB and return the withdrawn coin.

        Calls ``contra::unwrap`` to take ``amount`` out of ``account``'s confidential
        ``active`` balance and returns the resulting ordinary ``Coin<T>`` as a PTB result.
        The coin is not consumed here: the caller composes it, typically with
        ``transfer_objects``. The ``amount`` is a plaintext ``u64`` and is therefore public
        on chain; only the residual balance stays encrypted.

        Unwrap draws on the ``active`` balance only. Value credited to ``pending`` by an
        inbound ``transfer_private_funds``, or to ``public_balance`` by ``wrap_private_funds``,
        is invisible here until ``merge_private_funds`` folds it into ``active``. Because
        merge rewrites the ``active`` ciphertext that the balance proof is bound to, the
        merge must land in a **separate transaction** before this one is built.

        The plaintext new balance is computed client-side as ``active_balance - amount``:
        pysui-crypto is a pure prover and performs no overspend check, so the balance is
        decrypted here and the unwrap rejected locally when ``amount`` exceeds it.

        The transaction sender must be ``account``'s owner.

        :param coin_type: The confidential coin type ``T`` (type string or ``bcs.TypeTag``).
        :type coin_type: Union[str, bcs.TypeTag]
        :param account: The owner's ``Account`` object id (``0x`` hex string).
        :type account: str
        :param amount: The plaintext amount to withdraw from the confidential active balance.
        :type amount: int
        :param account_private_key: The account's 32-byte Twisted-ElGamal private key. This is
            the confidential-transfer keypair, not the owner's Sui signing key.
        :type account_private_key: bytes
        :param account_public_key: The account's 32-byte Twisted-ElGamal public key. This is
            the confidential-transfer keypair, not the owner's Sui signing key.
        :type account_public_key: bytes
        :raises ValueError: If ``amount`` exceeds the decrypted confidential active balance.
        :return: The unwrapped ``Coin<T>`` as a PTB result argument.
        :rtype: bcs.Argument
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

        owner_ta = await self._token_account(
            coin_type=coin_type_str, account_id=account
        )
        old_active_balance = _flatten_encrypted_amount(amount=owner_ta.active.amount)

        active_balance = _ext.decrypt_balance(
            account_private_key, old_active_balance, _ext.get_bsgs_table()
        )
        if amount > active_balance:
            raise ValueError(
                f"Insufficient confidential active balance: have {active_balance}, need {amount}"
            )
        new_balance = active_balance - amount

        session_id = utils.session_id(
            package_id=package_id,
            account_id=account,
            coin_type=coin_type_str,
        )
        proofs = _ext.unwrap_proofs(
            account_private_key,
            account_public_key,
            old_active_balance,
            amount,
            new_balance,
            session_id,
        )

        auth = await self.move_call(
            target=f"{package_id}::contra::authorize_as_sender",
            arguments=[confidential_token],
            type_arguments=[coin_type_str],
        )
        new_balance_amount = await self.move_call(
            target=f"{package_id}::decode::encrypted_amount",
            arguments=[_chunk32(blob=proofs["new_balance_amount"])],
        )
        consistency_proof = await self.move_call(
            target=f"{package_id}::decode::consistency_proof",
            arguments=[_chunk32(blob=proofs["consistency_proofs"][0])],
        )
        consistency_proof_vector = await self.make_move_vector(
            items=[consistency_proof],
            item_type=f"{package_id}::encrypted_amount::ConsistencyProof",
        )
        new_balance_proof = await self.move_call(
            target=f"{package_id}::encrypted_amount::new_well_formed_proof",
            arguments=[proofs["range_proofs"], consistency_proof_vector],
        )
        balance_proof = await self.move_call(
            target=f"{package_id}::decode::ddh_proof",
            arguments=[_chunk32(blob=proofs["balance_proof"])],
        )
        return await self.move_call(
            target=f"{package_id}::contra::unwrap",
            arguments=[
                account,
                auth,
                confidential_token,
                "0x403",
                pool,
                new_balance_amount,
                new_balance_proof,
                amount,
                balance_proof,
            ],
            type_arguments=[coin_type_str],
        )

    @instrumented(
        "pysui.private_transfer.transaction.PrivateFundsTransaction."
        "rotate_account_private_funds_keys"
    )
    async def rotate_account_private_funds_keys(
        self,
        *,
        coin_type: str,
        account: str,
        old_private: bytes,
        old_public: bytes,
        new_private: bytes,
        new_public: bytes,
    ) -> None:
        """Build the Confidential Transfer key-rotation (rekey) PTB for coin type ``T``.

        Assembles the single ``set_public_key<T>`` transaction that rotates the
        owner's Twisted-ElGamal (Confidential Transfer) keypair for the existing,
        registered ``account``: re-encrypt the ``active`` balance from the old
        public key to the new one without decrypting it. This is the entire
        transaction -- the caller drives simulation or execution of the built
        builder afterward.

        Permissionless rekey only. This method authorizes via
        ``authorize_as_sender``, which is valid only for tokens whose policy
        leaves the ``PERMISSIONED_REGISTER`` operation permissionless (the same
        gate ``register`` uses). Tokens whose policy makes registration/rekey
        permissioned require a different authorization path and are not supported
        by this method.

        Given the old and new keypairs, this method fetches the account's current
        ``active`` balance, derives the ``session_id``, and runs ``rekey_proofs``
        internally to produce the rotated handles and proof before assembling the
        PTB. The caller generates the new keypair and, on successful execution,
        persists it in place of the old one; on failure the previous keypair
        remains in effect.

        This method enforces one precondition itself: it raises ``ValueError`` if
        the account has pending deposits (``pending != 0``), which must be folded
        into ``active`` via ``merge_private_funds`` first. The caller is
        responsible for the remaining preconditions: the ``account`` is registered
        and has zero auditors (m = 0); ``key_encryption`` is passed on-chain as
        ``None`` for the m = 0 scope.

        :param coin_type: The confidential coin type ``T`` (fully-qualified type string).
        :type coin_type: str
        :param account: The existing shared ``Account`` object id (0x hex string).
            The owner is the implicit transaction signer, not a parameter.
        :type account: str
        :param old_private: The account's current 32-byte Twisted-ElGamal private key.
        :type old_private: bytes
        :param old_public: The account's current 32-byte Twisted-ElGamal public key.
        :type old_public: bytes
        :param new_private: The new 32-byte Twisted-ElGamal private key to rotate to.
        :type new_private: bytes
        :param new_public: The new 32-byte Twisted-ElGamal public key to rotate to.
        :type new_public: bytes
        """
        group = self._pf_config.active_group
        package_id = group.package_id
        _, pending, _ = await utils.account_balances(
            client=self.client,
            package_id=package_id,
            account_id=account,
            coin_type=coin_type,
            private_key=old_private,
        )
        if pending != 0:
            raise ValueError(
                "Pending deposits present; run merge_private_funds before rekey"
            )
        owner_ta = await self._token_account(
            coin_type=coin_type, account_id=account
        )
        old_active_balance = _flatten_encrypted_amount(amount=owner_ta.active.amount)
        session_id = utils.session_id(
            package_id=package_id,
            account_id=account,
            coin_type=coin_type,
        )
        proofs = _ext.rekey_proofs(
            old_private,
            old_public,
            new_private,
            new_public,
            old_active_balance,
            session_id,
        )
        confidential_token = utils.confidential_token_id(
            package_id=package_id,
            token_registry_id=group.token_registry,
            coin_type=coin_type,
        )
        auth = await self.move_call(
            target=f"{package_id}::contra::authorize_as_sender",
            arguments=[confidential_token],
            type_arguments=[coin_type],
        )
        new_pk = await self.move_call(
            target="0x2::ristretto255::g_from_bytes",
            arguments=[new_public],
        )
        handles = await self.move_call(
            target=f"{package_id}::decode::g_vector",
            arguments=[proofs["new_handles"]],
        )
        proof = await self.move_call(
            target=f"{package_id}::decode::batched_ddh_proof",
            arguments=[_chunk32(blob=proofs["rekey_proof"])],
        )
        key_encryption = await self.move_call(
            target="0x1::option::none",
            arguments=[],
            type_arguments=[f"{package_id}::auditors::KeyEncryption"],
        )
        await self.move_call(
            target=f"{package_id}::contra::set_public_key",
            arguments=[
                account,
                auth,
                confidential_token,
                new_pk,
                handles,
                proof,
                key_encryption,
            ],
            type_arguments=[coin_type],
        )


def _chunk32(*, blob: bytes) -> list[bytes]:
    """Split a byte blob into consecutive 32-byte parts.

    The ``contra::decode`` Move functions accept ``vector<vector<u8>>`` whose parts
    are the 32-byte group elements and scalars of the composite crypto type.

    :param blob: A byte string whose length is a multiple of 32.
    :type blob: bytes
    :raises ValueError: If ``blob`` is not a multiple of 32 bytes.
    :return: The 32-byte parts, in order.
    :rtype: list[bytes]
    """
    if len(blob) % 32:
        raise ValueError(f"Expected a multiple of 32 bytes, got {len(blob)}")
    return [blob[index : index + 32] for index in range(0, len(blob), 32)]


def _flatten_encrypted_amount(*, amount: pf_bcs.EncryptedAmount) -> bytes:
    """Flatten a deserialized ``EncryptedAmount`` to its 256-byte wire form.

    pysui-crypto expects the encrypted balance as four 64-byte limbs, each limb the
    concatenation ``ciphertext || decryption_handle``. BCS deserialization yields the
    group elements as length-prefixed vectors, so they are re-concatenated here.

    :param amount: The deserialized ``EncryptedAmount``.
    :type amount: pf_bcs.EncryptedAmount
    :return: The flat 256-byte encrypted amount.
    :rtype: bytes
    """
    flattened = bytearray()
    for limb in (amount.l0, amount.l1, amount.l2, amount.l3):
        flattened.extend(bytes(limb.ciphertext.bytes))
        flattened.extend(bytes(limb.decryption_handle.bytes))
    return bytes(flattened)
