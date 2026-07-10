#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Confidential Transfer (private funds) example command-line tool.

Exercises pysui private-transfer support (configuration, id derivation, and — as
they are added — registration and rekey) for validation and clarification ahead
of a live Confidential Transfer deployment.  Commands are added incrementally;
the first, ``validate_config``, resolves and validates a
:class:`PrivateFundsConfig` against the active ``PysuiConfiguration`` profile.
"""

import argparse
import asyncio
import base64
import json
import sys
from pathlib import Path

from pysui import (
    PysuiConfiguration,
    SuiRpcResult,
    client_factory,
    AsyncClientBase,
    SimulateTransactionKind,
    ExecuteTransaction,
    GetTransaction,
    GetCoins,
)
from pysui.private_transfer import utils
from pysui.private_transfer._ext import (
    generate_twisted_elgamal_keypair,
    raise_for_crypto,
)
from pysui.private_transfer.config import PrivateFundsConfig

# ---------------------------------------------------------------------------
# Fixed example parameters
# ---------------------------------------------------------------------------

#: Confidential-token coin type ``T`` this example operates on.  The example is
#: fixed to a single known token type; set this to the deployed devnet token
#: type before running ``register_accounts``.
TOKEN_TYPE = "0xb0eaf410ca6c030f450fb0ab96e497c6007c7284f688674e78aedd1c495bd760::pysui_token::PYSUI_TOKEN"

#: Sidecar file name, persisted under the ``--path`` directory (default
#: ``~/.pysui``).  Holds SELF CT identities only, keyed
#: ``network -> sender -> token_type -> {current, history}``.
SIDECAR_FILENAME = "PrivateFundsSidecar.json"


def validate_config(*, args: argparse.Namespace, pysui_config: PysuiConfiguration) -> None:
    """Validate a PrivateFundsConfig against the active PysuiConfiguration profile.

    :param args: Parsed command arguments (uses ``args.path``)
    :type args: argparse.Namespace
    :param pysui_config: The shared pysui configuration driving group resolution
    :type pysui_config: PysuiConfiguration
    """
    try:
        pfconfig = PrivateFundsConfig(pysui_config=pysui_config, from_cfg_path=args.path)
    except ValueError as exc:
        print(f"PrivateFundsConfig validation FAILED: {exc}")
        return
    group = pfconfig.active_group
    print(f"PrivateFundsConfig validated for profile '{pysui_config.active_profile}':")
    print(f"  group name:      {group.name}")
    print(f"  packageId:       {group.package_id}")
    print(f"  tokenRegistry:   {group.token_registry}")
    print(f"  accountRegistry: {group.account_registry}")


def _sidecar_file(*, path: str | None) -> Path:
    """Resolve the sidecar JSON file path.

    :param path: Optional directory (default: ``~/.pysui``)
    :type path: str | None
    :returns: Full path to the sidecar JSON file
    :rtype: Path
    """
    base = Path(path).expanduser() if path else Path("~/.pysui").expanduser()
    return base / SIDECAR_FILENAME


def _load_sidecar(*, sidecar_file: Path) -> dict:
    """Load the sidecar JSON, returning an empty mapping when absent.

    :param sidecar_file: Path to the sidecar JSON file
    :type sidecar_file: Path
    :returns: The parsed sidecar mapping (empty if the file does not exist)
    :rtype: dict
    """
    if sidecar_file.exists():
        return json.loads(sidecar_file.read_text())
    return {}


def _save_sidecar(*, sidecar_file: Path, data: dict) -> None:
    """Persist the sidecar JSON, creating the parent directory as needed.

    :param sidecar_file: Path to the sidecar JSON file
    :type sidecar_file: Path
    :param data: The sidecar mapping to serialise
    :type data: dict
    """
    sidecar_file.parent.mkdir(parents=True, exist_ok=True)
    sidecar_file.write_text(json.dumps(data, indent=2))


async def _append_history(  # pylint: disable=too-many-arguments
    *,
    sidecar: dict,
    sidecar_file: Path,
    network: str,
    address: str,
    coin_type: str,
    digest: str,
    client: AsyncClientBase,
) -> None:
    """Append a ``{digest, timestamp, checkpoint}`` anchor to the sidecar history.

    The execute response returns after quorum certification but before checkpoint
    finality, so ``timestamp`` and ``checkpoint`` are not yet assigned on it. This
    polls :class:`GetTransaction` by ``digest`` (up to 10 attempts, 1s apart) until
    the checkpoint is filled, then records the anchor. If it never resolves within
    the budget it falls through and stores ``null`` timestamp/checkpoint — the
    digest alone is sufficient to reconstruct the detail from chain later.

    :param sidecar: The in-memory sidecar mapping to mutate.
    :type sidecar: dict
    :param sidecar_file: Path to the sidecar JSON file to persist to.
    :type sidecar_file: Path
    :param network: Active network profile key (e.g. ``devnet``).
    :type network: str
    :param address: Sender address the activity is recorded under.
    :type address: str
    :param coin_type: Fully-qualified coin type key.
    :type coin_type: str
    :param digest: Transaction digest from the execute result.
    :type digest: str
    :param client: Active UCI protocol client for the by-digest lookup.
    :type client: AsyncClientBase
    """
    timestamp: str | None = None
    checkpoint: int | None = None
    for _ in range(10):
        result = await client.execute(command=GetTransaction(digest=digest))
        if result.is_ok() and result.result_data is not None and result.result_data.checkpoint is not None:
            executed = result.result_data
            checkpoint = executed.checkpoint
            timestamp = executed.timestamp.isoformat() if executed.timestamp else None
            break
        await asyncio.sleep(1)
    history = sidecar[network][address][coin_type].setdefault("history", [])
    history.append({"digest": digest, "timestamp": timestamp, "checkpoint": checkpoint})
    _save_sidecar(sidecar_file=sidecar_file, data=sidecar)


def register_accounts(*, args: argparse.Namespace, pysui_config: PysuiConfiguration) -> None:
    """Generate CT keypairs and create sidecar entries for one or more addresses.

    For each address supplied on the command line this:

    * confirms the address is known to the active ``PysuiConfiguration`` group,
    * derives the account id and generates a Twisted-ElGamal CT keypair,
    * writes a new sidecar entry, skipping any address already registered for
      :data:`TOKEN_TYPE` (never overwriting an existing keypair).

    No on-chain transaction is submitted; entries are built entirely from
    client-side derivation and local keypair generation.

    :param args: Parsed command arguments (uses ``args.addresses`` and ``args.path``)
    :type args: argparse.Namespace
    :param pysui_config: The shared pysui configuration driving group resolution
    :type pysui_config: PysuiConfiguration
    """
    raise_for_crypto()
    try:
        pfconfig = PrivateFundsConfig(pysui_config=pysui_config, from_cfg_path=args.path)
    except ValueError as exc:
        print(f"PrivateFundsConfig validation FAILED: {exc}")
        return

    group = pfconfig.active_group
    network = pysui_config.active_profile
    known = pysui_config.active_group.address_list

    sidecar_file = _sidecar_file(path=args.path)
    sidecar = _load_sidecar(sidecar_file=sidecar_file)
    net_entry = sidecar.setdefault(network, {})

    print(f"register_accounts on '{network}' for token type '{TOKEN_TYPE}':")
    changed = False
    for address in args.addresses:
        if address not in known:
            print(f"  {address}: NOT in PysuiConfiguration group — skipping")
            continue
        addr_entry = net_entry.setdefault(address, {})
        if TOKEN_TYPE in addr_entry:
            print(f"  {address}: already registered for token type — skipping")
            continue
        acct_id = utils.account_id(
            package_id=group.package_id,
            account_registry_id=group.account_registry,
            owner=address,
        )
        keypair = generate_twisted_elgamal_keypair()
        addr_entry["account_id"] = acct_id
        addr_entry[TOKEN_TYPE] = {
            "current": {
                "pf_private": base64.b64encode(keypair["private_key"]).decode("ascii"),
                "pf_public": base64.b64encode(keypair["public_key"]).decode("ascii"),
                "registered_auditor_version": None,
            },
            "history": [],
        }
        changed = True
        print(f"  {address}: registered (account_id={acct_id})")

    if changed:
        _save_sidecar(sidecar_file=sidecar_file, data=sidecar)
        print(f"Sidecar updated: {sidecar_file}")
    else:
        print(f"No changes; sidecar not written ({sidecar_file}).")


def handle_result(result: SuiRpcResult) -> SuiRpcResult:
    """Print an execution or simulation result and return it unchanged.

    :param result: The result returned from ``client.execute``.
    :type result: SuiRpcResult
    :returns: The same result, unchanged.
    :rtype: SuiRpcResult
    """
    if result.is_ok():
        if hasattr(result.result_data, "to_json"):
            print(result.result_data.to_json(indent=2))
        else:
            print(result.result_data)
    else:
        print(result.result_string)
        if result.result_data and hasattr(result.result_data, "to_json"):
            print(result.result_data.to_json(indent=2))
        else:
            print(result.result_data)
    return result


async def register_private_funds(*, args: argparse.Namespace, pysui_config: PysuiConfiguration) -> None:
    """Register a single address on-chain for Confidential Transfers.

    Resolves the address's Twisted-ElGamal public key from the sidecar (which
    ``register_accounts`` must have populated), builds the registration PTB via
    :meth:`PrivateFundsTransaction.register_private_funds`, then either simulates
    or executes it per ``--mode``.

    :param args: Parsed CLI arguments (``address``, ``token_type``, ``mode``, ``path``).
    :type args: argparse.Namespace
    :param pysui_config: The shared pysui configuration.
    :type pysui_config: PysuiConfiguration
    """
    address = args.address
    coin_type = args.token_type
    network = pysui_config.active_profile
    sidecar_file = _sidecar_file(path=args.path)
    sidecar = _load_sidecar(sidecar_file=sidecar_file)
    entry = sidecar.get(network, {}).get(address, {}).get(coin_type, {}).get("current", {})
    pf_public = entry.get("pf_public")
    if not pf_public:
        raise SystemExit(
            f"No sidecar entry with a public key for address {address} "
            f"(network {network}, token {coin_type}) in {sidecar_file}. "
            f"Run the 'register_accounts' command first."
        )
    elgamal_public_key = base64.b64decode(pf_public)

    client = client_factory(pysui_config)
    try:
        # contra::register_internal asserts auth.owner == account.owner, and
        # authorize_as_sender binds Auth.owner to the tx sender: the owner must sign.
        txn = await client.transaction(
            private_fund=True,
            initial_sender=address,
            initial_sponsor=args.sponsor,
        )
        await txn.register_private_funds(coin_type=coin_type, owner=address, elgamal_public_key=elgamal_public_key)

        if args.mode == "simulate":
            handle_result(
                await client.execute(
                    command=SimulateTransactionKind(
                        tx_kind=await txn.raw_kind(),
                        tx_meta={"sender": address},
                        gas_selection=True,
                    )
                )
            )
        else:
            txdict = await txn.build_and_sign()
            result = await client.execute(command=ExecuteTransaction(**txdict))
            handle_result(result)
            if result.is_ok() and result.result_data.effects.status.success:
                await _append_history(
                    sidecar=sidecar,
                    sidecar_file=sidecar_file,
                    network=network,
                    address=address,
                    coin_type=coin_type,
                    digest=result.result_data.digest,
                    client=client,
                )
    finally:
        await client.close()


async def wrap_private_funds(*, args: argparse.Namespace, pysui_config: PysuiConfiguration) -> None:
    """Wrap a whole coin (or a split amount) into a receiver's confidential public balance.

    Fetches the sender's coins of ``token_type``. For ``--coin`` the named whole coin is
    wrapped; for ``--amount`` a coin of exactly that value is wrapped, splitting in-PTB
    when no coin matches the amount exactly. The sender must have a sidecar entry for
    ``token_type`` on this network; the receiver is assumed already registered on-chain.
    Simulates by default.

    :param args: Parsed CLI arguments for the wrap subcommand.
    :type args: argparse.Namespace
    :param pysui_config: The active pysui configuration.
    :type pysui_config: PysuiConfiguration
    """
    sender = args.sender or pysui_config.active_address
    receiver = args.receiver
    token_type = args.token_type
    memo = args.memo if args.memo is not None else b""
    network = pysui_config.active_profile

    # Gate: the sender must have a sidecar entry for this token_type on this network.
    sidecar_file = _sidecar_file(path=args.path)
    sidecar = _load_sidecar(sidecar_file=sidecar_file)
    if not sidecar.get(network, {}).get(sender, {}).get(token_type, {}):
        raise SystemExit(
            f"Sender {sender} has no sidecar entry for {token_type} on {network}; "
            "run register_accounts / register_private_funds first."
        )

    client = client_factory(pysui_config)
    try:
        # Fetch the sender's coins of this type (needed for both --coin and --amount).
        coins_result = await client.execute_for_all(
            command=GetCoins(
                owner=sender,
                coin_type=f"0x2::coin::Coin<{token_type}>",
            )
        )
        if not coins_result.is_ok():
            handle_result(coins_result)
            raise SystemExit(f"Failed to fetch {token_type} coins for sender {sender}.")
        coins = coins_result.result_data.objects

        txn = await client.transaction(
            private_fund=True,
            initial_sender=sender,
            initial_sponsor=args.sponsor,
        )

        if args.coin is not None:
            coin_to_wrap = next((c for c in coins if c.object_id == args.coin), None)
            if coin_to_wrap is None:
                raise SystemExit(f"Coin {args.coin} is not among sender {sender}'s {token_type} coins.")
        else:
            amount = args.amount
            total = sum(c.balance for c in coins)
            if total < amount:
                raise SystemExit(f"Insufficient balance for {amount}: sender {sender} holds {total}.")
            exact = next((c for c in coins if c.balance == amount), None)
            if exact is not None:
                coin_to_wrap = exact
            else:
                fundable = next((c for c in coins if c.balance > amount), None)
                if fundable is None:
                    raise SystemExit(
                        f"No single coin has at least {amount} to split from " f"(total {total}); merge coins first."
                    )
                coin_to_wrap = await txn.split_coin(coin=fundable, amounts=[amount])

        await txn.wrap_private_funds(
            coin_type=token_type,
            receiver_address=receiver,
            coin_to_wrap=coin_to_wrap,
            memo=memo,
        )

        if args.mode == "simulate":
            handle_result(
                await client.execute(
                    command=SimulateTransactionKind(
                        tx_kind=await txn.raw_kind(),
                        tx_meta={"sender": sender},
                        gas_selection=True,
                    )
                )
            )
        else:
            txdict = await txn.build_and_sign()
            result = await client.execute(command=ExecuteTransaction(**txdict))
            handle_result(result)
            if result.is_ok() and result.result_data.effects.status.success:
                await _append_history(
                    sidecar=sidecar,
                    sidecar_file=sidecar_file,
                    network=network,
                    address=sender,
                    coin_type=token_type,
                    digest=result.result_data.digest,
                    client=client,
                )
    finally:
        await client.close()


async def merge_private_funds(*, args: argparse.Namespace, pysui_config: PysuiConfiguration) -> None:
    """Merge a sender's pending + public confidential deposits into their active balance.

    Applies all pending (encrypted) and plaintext ``public_balance`` deposits for
    ``token_type`` into the sender's confidential ``active`` balance, making them
    spendable in a confidential transfer. Owner-only: the sender must be the account
    owner. Simulates by default.

    :param args: Parsed CLI arguments for the merge subcommand.
    :type args: argparse.Namespace
    :param pysui_config: The active pysui configuration.
    :type pysui_config: PysuiConfiguration
    """
    sender = args.sender or pysui_config.active_address
    token_type = args.token_type
    network = pysui_config.active_profile

    sidecar_file = _sidecar_file(path=args.path)
    sidecar = _load_sidecar(sidecar_file=sidecar_file)
    addr_entry = sidecar.get(network, {}).get(sender, {})
    if not addr_entry.get(token_type, {}):
        raise SystemExit(
            f"Sender {sender} has no sidecar entry for {token_type} on {network}; "
            "run register_accounts / register_private_funds first."
        )
    account_id = addr_entry.get("account_id")
    if not account_id:
        raise SystemExit(f"Sender {sender} has no account_id in sidecar for {network}; " "run register_accounts first.")

    client = client_factory(pysui_config)
    try:
        txn = await client.transaction(
            private_fund=True,
            initial_sender=sender,
            initial_sponsor=args.sponsor,
        )
        await txn.merge_private_funds(coin_type=token_type, account=account_id)

        if args.mode == "simulate":
            handle_result(
                await client.execute(
                    command=SimulateTransactionKind(
                        tx_kind=await txn.raw_kind(),
                        tx_meta={"sender": sender},
                        gas_selection=True,
                    )
                )
            )
        else:
            txdict = await txn.build_and_sign()
            result = await client.execute(command=ExecuteTransaction(**txdict))
            handle_result(result)
            if result.is_ok() and result.result_data.effects.status.success:
                await _append_history(
                    sidecar=sidecar,
                    sidecar_file=sidecar_file,
                    network=network,
                    address=sender,
                    coin_type=token_type,
                    digest=result.result_data.digest,
                    client=client,
                )
    finally:
        await client.close()


async def transfer_private_funds(*, args: argparse.Namespace, pysui_config: PysuiConfiguration) -> None:
    """Transfer confidential amounts from the sender's active balance to one or more recipients.

    Debits the sender's confidential ``active`` balance by the batch total and credits each
    recipient's ``pending`` balance. ``--recipient``, ``--amount`` and ``--memo`` are parallel
    lists of equal length whose order is the on-chain submission order. The sender's ElGamal
    keypair is read from the sidecar; each recipient's public key and the sender's current
    encrypted balance are read on-chain. Recipients must ``merge_private_funds`` before the
    value is spendable. All parties must already be registered for ``token_type``.
    Simulates by default.

    :param args: Parsed CLI arguments for the transfer subcommand.
    :type args: argparse.Namespace
    :param pysui_config: The active pysui configuration.
    :type pysui_config: PysuiConfiguration
    """
    sender = args.sender or pysui_config.active_address
    token_type = args.token_type
    network = pysui_config.active_profile

    if not len(args.recipient) == len(args.amount) == len(args.memo):
        raise SystemExit(
            "--recipient, --amount and --memo must be the same length (got "
            f"{len(args.recipient)}, {len(args.amount)}, {len(args.memo)})."
        )
    recipients = list(zip(args.recipient, args.amount, args.memo))

    sidecar_file = _sidecar_file(path=args.path)
    sidecar = _load_sidecar(sidecar_file=sidecar_file)
    addr_entry = sidecar.get(network, {}).get(sender, {})
    token_entry = addr_entry.get(token_type, {})
    if not token_entry:
        raise SystemExit(
            f"Sender {sender} has no sidecar entry for {token_type} on {network}; "
            "run register_accounts / register_private_funds first."
        )
    account_id = addr_entry.get("account_id")
    if not account_id:
        raise SystemExit(f"Sender {sender} has no account_id in sidecar for {network}; " "run register_accounts first.")
    current = token_entry.get("current", {})
    pf_private = current.get("pf_private")
    pf_public = current.get("pf_public")
    if not pf_private or not pf_public:
        raise SystemExit(f"Sender {sender} has no pf_private/pf_public keypair in sidecar for {token_type}.")

    client = client_factory(pysui_config)
    try:
        txn = await client.transaction(
            private_fund=True,
            initial_sender=sender,
            initial_sponsor=args.sponsor,
        )
        await txn.transfer_private_funds(
            coin_type=token_type,
            sender_account=account_id,
            recipients=recipients,
            sender_private_key=base64.b64decode(pf_private),
            sender_public_key=base64.b64decode(pf_public),
        )

        if args.mode == "simulate":
            handle_result(
                await client.execute(
                    command=SimulateTransactionKind(
                        tx_kind=await txn.raw_kind(),
                        tx_meta={"sender": sender},
                        gas_selection=True,
                    )
                )
            )
        else:
            txdict = await txn.build_and_sign()
            result = await client.execute(command=ExecuteTransaction(**txdict))
            handle_result(result)
            if result.is_ok() and result.result_data.effects.status.success:
                await _append_history(
                    sidecar=sidecar,
                    sidecar_file=sidecar_file,
                    network=network,
                    address=sender,
                    coin_type=token_type,
                    digest=result.result_data.digest,
                    client=client,
                )
    finally:
        await client.close()


async def unwrap_private_funds(*, args: argparse.Namespace, pysui_config: PysuiConfiguration) -> None:
    """Unwrap a confidential amount into an ordinary Coin<T> and transfer it to a recipient.

    Debits the sender's confidential ``active`` balance by ``--amount`` and withdraws that
    value from the token's ``Pool<T>`` as a plaintext ``Coin<T>``, which is transferred to
    ``--recipient`` (default: the sender). The amount is public on chain; only the residual
    confidential balance stays encrypted.

    Unwrap draws on the ``active`` balance only. Run ``merge_private_funds`` first, as its
    own transaction, if value is still sitting in ``pending`` or ``public_balance`` --
    ``account_balances`` will show it. The sender's Twisted-ElGamal keypair is read from the
    sidecar; the current encrypted balance is read on-chain. Simulates by default.

    :param args: Parsed CLI arguments for the unwrap subcommand.
    :type args: argparse.Namespace
    :param pysui_config: The active pysui configuration.
    :type pysui_config: PysuiConfiguration
    """
    sender = args.sender or pysui_config.active_address
    recipient = args.recipient or sender
    token_type = args.token_type
    network = pysui_config.active_profile

    sidecar_file = _sidecar_file(path=args.path)
    sidecar = _load_sidecar(sidecar_file=sidecar_file)
    addr_entry = sidecar.get(network, {}).get(sender, {})
    token_entry = addr_entry.get(token_type, {})
    if not token_entry:
        raise SystemExit(
            f"Sender {sender} has no sidecar entry for {token_type} on {network}; "
            "run register_accounts / register_private_funds first."
        )
    account_id = addr_entry.get("account_id")
    if not account_id:
        raise SystemExit(f"Sender {sender} has no account_id in sidecar for {network}; " "run register_accounts first.")
    current = token_entry.get("current", {})
    pf_private = current.get("pf_private")
    pf_public = current.get("pf_public")
    if not pf_private or not pf_public:
        raise SystemExit(f"Sender {sender} has no pf_private/pf_public keypair in sidecar for {token_type}.")

    client = client_factory(pysui_config)
    try:
        txn = await client.transaction(
            private_fund=True,
            initial_sender=sender,
            initial_sponsor=args.sponsor,
        )
        unwrapped_coin = await txn.unwrap_private_funds(
            coin_type=token_type,
            account=account_id,
            amount=args.amount,
            account_private_key=base64.b64decode(pf_private),
            account_public_key=base64.b64decode(pf_public),
        )
        await txn.transfer_objects(transfers=[unwrapped_coin], recipient=recipient)

        if args.mode == "simulate":
            handle_result(
                await client.execute(
                    command=SimulateTransactionKind(
                        tx_kind=await txn.raw_kind(),
                        tx_meta={"sender": sender},
                        gas_selection=True,
                    )
                )
            )
        else:
            txdict = await txn.build_and_sign()
            result = await client.execute(command=ExecuteTransaction(**txdict))
            handle_result(result)
            if result.is_ok() and result.result_data.effects.status.success:
                await _append_history(
                    sidecar=sidecar,
                    sidecar_file=sidecar_file,
                    network=network,
                    address=sender,
                    coin_type=token_type,
                    digest=result.result_data.digest,
                    client=client,
                )
    finally:
        await client.close()


async def account_balances(*, args: argparse.Namespace, pysui_config: PysuiConfiguration) -> None:
    """Print an owner's decrypted Confidential Transfer balances for a coin type.

    Reads the owner's ``account_id`` and ElGamal private key from the sidecar, fetches
    the on-chain ``TokenAccount<T>``, and prints the plaintext ``active``, ``pending``
    and ``public_balance``. ``active`` is spendable; ``pending`` is value received but
    not yet merged; ``public_balance`` is the plaintext deposit balance. Read-only.

    :param args: Parsed CLI arguments for the account_balances subcommand.
    :type args: argparse.Namespace
    :param pysui_config: The active pysui configuration.
    :type pysui_config: PysuiConfiguration
    """
    owner = args.owner or pysui_config.active_address
    token_type = args.token_type
    network = pysui_config.active_profile

    sidecar_file = _sidecar_file(path=args.path)
    sidecar = _load_sidecar(sidecar_file=sidecar_file)
    addr_entry = sidecar.get(network, {}).get(owner, {})
    token_entry = addr_entry.get(token_type, {})
    if not token_entry:
        raise SystemExit(
            f"Owner {owner} has no sidecar entry for {token_type} on {network}; "
            "run register_accounts / register_private_funds first."
        )
    account_id = addr_entry.get("account_id")
    if not account_id:
        raise SystemExit(f"Owner {owner} has no account_id in sidecar for {network}; " "run register_accounts first.")
    pf_private = token_entry.get("current", {}).get("pf_private")
    if not pf_private:
        raise SystemExit(f"Owner {owner} has no pf_private key in sidecar for {token_type}.")

    client = client_factory(pysui_config)
    try:
        pf_config = PrivateFundsConfig(pysui_config=pysui_config)
        active, pending, public_balance = await utils.account_balances(
            client=client,
            package_id=pf_config.active_group.package_id,
            account_id=account_id,
            coin_type=token_type,
            private_key=base64.b64decode(pf_private),
        )
        print(f"Owner:           {owner}")
        print(f"Account:         {account_id}")
        print(f"Coin type:       {token_type}")
        print(f"active:          {active}")
        print(f"pending:         {pending}")
        print(f"public_balance:  {public_balance}")
    finally:
        await client.close()


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser and register all subcommands.

    :returns: The configured argument parser
    :rtype: argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog="ucs_private_funds_example",
        description="Confidential Transfer (private funds) example commands.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser(
        "validate_config",
        help="Validate PrivateFundsConfig against the active PysuiConfiguration profile.",
    )
    validate.add_argument(
        "--path",
        default=None,
        help="Optional directory containing PrivateFundsConfig.json (default: ~/.pysui).",
    )
    register = subparsers.add_parser(
        "register_accounts",
        help="Generate CT keypairs and create sidecar entries for one or more addresses.",
    )
    register.add_argument(
        "addresses",
        nargs="+",
        help="One or more Sui addresses (each must exist in the active PysuiConfiguration group).",
    )
    register.add_argument(
        "--path",
        default=None,
        help="Optional directory for PrivateFundsConfig.json and the sidecar (default: ~/.pysui).",
    )
    register_pf = subparsers.add_parser(
        "register_private_funds",
        help="Register a single address on-chain for Confidential Transfers (simulate or execute).",
    )
    register_pf.add_argument(
        "address",
        help="The Sui address to register (must have a sidecar entry from 'register_accounts').",
    )
    register_pf.add_argument(
        "token_type",
        help="The confidential coin type (T) to register for; must match a sidecar entry for the address.",
    )
    register_pf.add_argument(
        "--sponsor",
        default=None,
        help="Optional sponsor Sui address that pays gas (default: the sender). Sponsor's keypair must exist in the PysuiConfiguration.",
    )
    register_pf.add_argument(
        "--mode",
        choices=["simulate", "execute"],
        default="simulate",
        help="Simulate (default) or execute the registration transaction.",
    )
    register_pf.add_argument(
        "--path",
        default=None,
        help="Optional directory containing the sidecar (default: ~/.pysui).",
    )
    wrap_pf = subparsers.add_parser(
        "wrap_private_funds",
        help="Wrap a coin (or split amount) into a receiver's confidential public balance (simulate or execute).",
    )
    wrap_pf.add_argument(
        "--sender",
        default=None,
        help="Sender / coin-owner Sui address (default: active PysuiConfiguration address).",
    )
    wrap_pf.add_argument(
        "--sponsor",
        default=None,
        help="Optional sponsor Sui address that pays gas (default: the sender). Sponsor's keypair must exist in the PysuiConfiguration.",
    )
    wrap_pf.add_argument(
        "--receiver",
        required=True,
        help="Recipient Sui address (assumed already registered for token_type).",
    )
    wrap_pf.add_argument(
        "--token-type",
        required=True,
        help="The confidential coin type (T) to wrap.",
    )
    coin_source = wrap_pf.add_mutually_exclusive_group(required=True)
    coin_source.add_argument(
        "--coin",
        default=None,
        help="Object id of a whole Coin<T> to wrap (whole coin consumed).",
    )
    coin_source.add_argument(
        "--amount",
        type=int,
        default=None,
        help="Amount to wrap; a coin with >= amount is used whole (if exact) or split.",
    )
    wrap_pf.add_argument(
        "--memo",
        default=None,
        help="Optional memo string emitted in the on-chain wrap event.",
    )
    wrap_pf.add_argument(
        "--mode",
        choices=["simulate", "execute"],
        default="simulate",
        help="Simulate (default) or execute the wrap transaction.",
    )
    wrap_pf.add_argument(
        "--path",
        default=None,
        help="Optional directory containing the sidecar (default: ~/.pysui).",
    )
    merge_pf = subparsers.add_parser(
        "merge_private_funds",
        help="Merge a sender's pending + public deposits into their active balance (simulate or execute).",
    )
    merge_pf.add_argument(
        "--sender",
        default=None,
        help="Sender / account-owner Sui address (default: active PysuiConfiguration address).",
    )
    merge_pf.add_argument(
        "--sponsor",
        default=None,
        help="Optional sponsor Sui address that pays gas (default: the sender). Sponsor's keypair must exist in the PysuiConfiguration.",
    )
    merge_pf.add_argument(
        "--token-type",
        required=True,
        help="The confidential coin type (T) to merge.",
    )
    merge_pf.add_argument(
        "--mode",
        choices=["simulate", "execute"],
        default="simulate",
        help="Simulate (default) or execute the merge transaction.",
    )
    merge_pf.add_argument(
        "--path",
        default=None,
        help="Optional directory containing the sidecar (default: ~/.pysui).",
    )
    transfer_pf = subparsers.add_parser(
        "transfer_private_funds",
        help="Transfer a confidential amount to a recipient's pending balance (simulate or execute).",
    )
    transfer_pf.add_argument(
        "--sender",
        default=None,
        help="Sender / account-owner Sui address (default: active PysuiConfiguration address).",
    )
    transfer_pf.add_argument(
        "--sponsor",
        default=None,
        help="Optional sponsor Sui address that pays gas (default: the sender). Sponsor's keypair must exist in the PysuiConfiguration.",
    )
    transfer_pf.add_argument(
        "--recipient",
        nargs="+",
        required=True,
        help="Recipient Sui address(es) in submission order; each must already be registered for token_type.",
    )
    transfer_pf.add_argument(
        "--token-type",
        required=True,
        help="The confidential coin type (T) to transfer.",
    )
    transfer_pf.add_argument(
        "--amount",
        type=int,
        nargs="+",
        required=True,
        help="Plaintext amount per recipient; must match --recipient in length and order.",
    )
    transfer_pf.add_argument(
        "--memo",
        nargs="+",
        required=True,
        help="Memo per recipient; must match --recipient in length and order.",
    )
    transfer_pf.add_argument(
        "--mode",
        choices=["simulate", "execute"],
        default="simulate",
        help="Simulate (default) or execute the transfer transaction.",
    )
    transfer_pf.add_argument(
        "--path",
        default=None,
        help="Optional directory containing the sidecar (default: ~/.pysui).",
    )
    unwrap_pf = subparsers.add_parser(
        "unwrap_private_funds",
        help="Unwrap a confidential amount from the sender's active balance into an ordinary Coin<T> (simulate or execute).",
    )
    unwrap_pf.add_argument(
        "--sender",
        default=None,
        help="Sender / account-owner Sui address (default: active PysuiConfiguration address).",
    )
    unwrap_pf.add_argument(
        "--sponsor",
        default=None,
        help="Optional sponsor Sui address that pays gas (default: the sender). Sponsor's keypair must exist in the PysuiConfiguration.",
    )
    unwrap_pf.add_argument(
        "--recipient",
        default=None,
        help="Recipient of the unwrapped Coin<T> (default: --sender).",
    )
    unwrap_pf.add_argument(
        "--token-type",
        required=True,
        help="The confidential coin type (T) to unwrap.",
    )
    unwrap_pf.add_argument(
        "--amount",
        type=int,
        required=True,
        help="Plaintext amount to unwrap from the sender's confidential active balance.",
    )
    unwrap_pf.add_argument(
        "--mode",
        choices=["simulate", "execute"],
        default="simulate",
        help="Simulate (default) or execute the unwrap transaction.",
    )
    unwrap_pf.add_argument(
        "--path",
        default=None,
        help="Optional directory containing the sidecar (default: ~/.pysui).",
    )
    balances_pf = subparsers.add_parser(
        "account_balances",
        help="Print an owner's decrypted active, pending and public balances (read-only).",
    )
    balances_pf.add_argument(
        "--owner",
        default=None,
        help="Account-owner Sui address (default: active PysuiConfiguration address).",
    )
    balances_pf.add_argument(
        "--token-type",
        required=True,
        help="The confidential coin type (T) to report.",
    )
    balances_pf.add_argument(
        "--path",
        default=None,
        help="Optional directory containing the sidecar (default: ~/.pysui).",
    )
    return parser


async def main(*, pysui_config: PysuiConfiguration) -> None:
    """Parse arguments and dispatch to the selected command.

    :param pysui_config: The shared pysui configuration
    :type pysui_config: PysuiConfiguration
    """
    args = build_parser().parse_args()
    if args.command == "validate_config":
        validate_config(args=args, pysui_config=pysui_config)
    elif args.command == "register_accounts":
        register_accounts(args=args, pysui_config=pysui_config)
    elif args.command == "register_private_funds":
        await register_private_funds(args=args, pysui_config=pysui_config)
    elif args.command == "wrap_private_funds":
        await wrap_private_funds(args=args, pysui_config=pysui_config)
    elif args.command == "merge_private_funds":
        await merge_private_funds(args=args, pysui_config=pysui_config)
    elif args.command == "transfer_private_funds":
        await transfer_private_funds(args=args, pysui_config=pysui_config)
    elif args.command == "unwrap_private_funds":
        await unwrap_private_funds(args=args, pysui_config=pysui_config)
    elif args.command == "account_balances":
        await account_balances(args=args, pysui_config=pysui_config)
    # Future async commands dispatch with await, e.g.:
    # elif args.command == "transfer":
    #     await transfer(args=args, pysui_config=pysui_config)


if __name__ == "__main__":
    if len(sys.argv) == 1:

        # Optionally force a specific command + arguments (uncomment one):
        # sys.argv = ["ucs_private_funds_example.py", "validate_config"]
        # sys.argv = [
        #     "ucs_private_funds_example.py",
        #     "validate_config",
        #     "--path",
        #     "~/.pwallet",
        # ]
        # sys.argv = [
        #     "ucs_private_funds_example.py",
        #     "register_accounts",
        #     "0xa9e2db385f055cc0215a3cde268b76270535b9443807514f183be86926c219f4",
        #     "0xa9fe7b9cab7ce187c768a9b16e95dbc5953a99ec461067a73a6b1c4288873e28",
        # ]
        # sys.argv = [
        #     "ucs_private_funds_example.py",
        #     "register_private_funds",
        #     "0xa9e2db385f055cc0215a3cde268b76270535b9443807514f183be86926c219f4",
        #     "0xb0eaf410ca6c030f450fb0ab96e497c6007c7284f688674e78aedd1c495bd760::pysui_token::PYSUI_TOKEN",
        #     # "--mode",
        #     # "execute",
        # ]
        # Default run when invoked with no CLI args (e.g. from the debugger);
        # real command-line arguments take precedence when provided.
        # sys.argv = [
        #     "ucs_private_funds_example.py",
        #     "wrap_private_funds",
        #     "--receiver",
        #     "0xa9e2db385f055cc0215a3cde268b76270535b9443807514f183be86926c219f4",
        #     "--token-type",
        #     "0xb0eaf410ca6c030f450fb0ab96e497c6007c7284f688674e78aedd1c495bd760::pysui_token::PYSUI_TOKEN",
        #     "--amount",
        #     "10000000",
        #     # "--sender",
        #     # "0x...",
        #     # "--coin",
        #     # "0x...",
        #     "--memo",
        #     "hello",
        #     "--mode",
        #     "execute",
        # ]
        # sys.argv = [
        #     "ucs_private_funds_example.py",
        #     "merge_private_funds",
        #     "--token-type",
        #     "0xb0eaf410ca6c030f450fb0ab96e497c6007c7284f688674e78aedd1c495bd760::pysui_token::PYSUI_TOKEN",
        #     # "--sender",
        #     # "0x...",
        #     "--mode",
        #     "execute",
        # ]
        # --recipient / --amount / --memo are parallel lists of equal length,
        # in on-chain submission order.
        # sys.argv = [
        #     "ucs_private_funds_example.py",
        #     "transfer_private_funds",
        #     "--recipient",
        #     "0xa9e2db385f055cc0215a3cde268b76270535b9443807514f183be86926c219f4",
        #     "--token-type",
        #     "0xb0eaf410ca6c030f450fb0ab96e497c6007c7284f688674e78aedd1c495bd760::pysui_token::PYSUI_TOKEN",
        #     "--amount",
        #     "10000000",
        #     "--memo",
        #     "transfer test",
        #     # "--sender",
        #     # "0x...",
        #     "--mode",
        #     "simulate",
        #     # "execute",
        # ]
        # Unwrap draws on `active` only -- run merge_private_funds first, as its
        # own transaction, if value is still in `pending` or `public_balance`.
        # sys.argv = [
        #     "ucs_private_funds_example.py",
        #     "unwrap_private_funds",
        #     "--token-type",
        #     "0xb0eaf410ca6c030f450fb0ab96e497c6007c7284f688674e78aedd1c495bd760::pysui_token::PYSUI_TOKEN",
        #     "--amount",
        #     "10000000",
        #     # "--sender",
        #     # "0x...",
        #     # "--recipient",
        #     # "0x...",
        #     "--mode",
        #     # "simulate",
        #     "execute",
        # ]
        # sys.argv = [
        #     "ucs_private_funds_example.py",
        #     "account_balances",
        #     "--token-type",
        #     "0xb0eaf410ca6c030f450fb0ab96e497c6007c7284f688674e78aedd1c495bd760::pysui_token::PYSUI_TOKEN",
        #     # "--owner",
        #     # "0x...",
        # ]
        # sys.argv = [
        #     "ucs_private_funds_example.py",
        #     "register_accounts",
        #     "0xADDRESS_ONE",
        #     "--path",
        #     "~/.pwallet",
        # ]
        pass

    _pysui_config = PysuiConfiguration(
        # Uncomment one group:
        # group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP,
        group_name=PysuiConfiguration.SUI_GRPC_GROUP,
        profile_name="devnet",
        # profile_name="testnet",
        # profile_name="mainnet",
    )
    asyncio.run(main(pysui_config=_pysui_config))
