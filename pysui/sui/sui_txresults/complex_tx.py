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

"""Types return from complext transactions."""

from dataclasses import dataclass, field
from typing import Any, Optional, Union
from dataclasses_json import DataClassJsonMixin, LetterCase, config
from deprecated.sphinx import versionadded
from pysui.sui.sui_txresults.common import GenericOwnerRef, GenericRef, SuiTxReturnType
from pysui.sui.sui_types.collections import EventID


@dataclass
class TxGasData(SuiTxReturnType, DataClassJsonMixin):
    """Transaction Data."""

    budget: int
    owner: str
    price: int
    payment: list[GenericRef]


@dataclass
class ChangeEpoch(SuiTxReturnType, DataClassJsonMixin):
    """A system transaction that will update epoch information on-chain."""

    kind: str
    computational_charge: int
    epoch: int
    epoch_start_timestamp_ms: int
    storage_charge: int
    storage_rebate: int


@dataclass
class Genesis(SuiTxReturnType, DataClassJsonMixin):
    """A system transaction used for initializing the initial state of the chain."""

    kind: str
    objects: list[str]


@dataclass
class ConsensusCommitPrologue(SuiTxReturnType, DataClassJsonMixin):
    """A system transaction marking the start of a series of transactions scheduled as part of a checkpoint."""

    kind: str
    commit_timestamp_ms: int
    epoch: int
    prologue_round: int = field(metadata=config(field_name="round"))


@dataclass
class ProgrammableTransaction(SuiTxReturnType, DataClassJsonMixin):
    """A series of commands where the results of one command can be used in future commands."""

    kind: str
    transactions: list[dict]
    inputs: list[Any]


@dataclass
class TransactionData(SuiTxReturnType, DataClassJsonMixin):
    """Transaction Data."""

    sender: str
    message_version: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    gas_data: TxGasData = field(metadata=config(letter_case=LetterCase.CAMEL))
    transaction: dict = field(default_factory=dict)

    def __post_init__(self):
        """Post init processing.

        Resolves the transaction kind
        """
        if self.transaction:
            tx_kind = self.transaction["kind"]
            match tx_kind:
                case "ChangeEpoch":
                    self.transaction = ChangeEpoch.from_dict(self.transaction)
                case "Genesis":
                    self.transaction = Genesis.from_dict(self.transaction)
                case "ProgrammableTransaction":
                    self.transaction = ProgrammableTransaction.from_dict(self.transaction)
                case "ConsensusCommitPrologue":
                    self.transaction = ConsensusCommitPrologue.from_dict(self.transaction)
                case _:
                    raise ValueError(f"{tx_kind} unknown Transaction Kind")


@dataclass
class MultiSigPublicKey(SuiTxReturnType, DataClassJsonMixin):
    """Multi-sig Public Key info if used to sign transactions."""

    pk_map: dict[str, str]
    threshold: int


@dataclass
class MultiSig(SuiTxReturnType, DataClassJsonMixin):
    """Defined for multi-sig transaction signing."""

    bitmap: str
    multisig_pk: MultiSigPublicKey
    sigs: list[dict[str, str]]

    def __post_init__(self):
        """."""


@dataclass
class Transaction(SuiTxReturnType, DataClassJsonMixin):
    """Transaction encapsulates single and multi-sig signatures as well as specific transaction data."""

    data: TransactionData
    tx_signatures: list[Union[str, dict]] = field(metadata=config(letter_case=LetterCase.CAMEL))

    def __post_init__(self):
        """Post process to reconcile signatures."""
        hydrate = []
        for sig in self.tx_signatures:
            if isinstance(sig, str):
                hydrate.append(sig)
            elif isinstance(sig, dict):
                hydrate.append(MultiSig.from_dict(sig))
            else:
                print(f"No idea {sig}")
                hydrate.append(sig)
        self.tx_signatures = hydrate


@dataclass
class Event(SuiTxReturnType, DataClassJsonMixin):
    """Result of various get and result API."""

    bcs: str
    package_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    parsed_json: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    sender: str
    transaction_module: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    event_type: str = field(metadata=config(field_name="type"))
    event_id: dict = field(metadata=config(field_name="id"))
    # timestamp_ms: Optional[int] = field(metadata=config(letter_case=LetterCase.CAMEL))
    timestamp_ms: Optional[str] = field(metadata=config(letter_case=LetterCase.CAMEL), default="")


@dataclass
class EventBlock(SuiTxReturnType, DataClassJsonMixin):
    """Collection of events."""

    events: list[Event]

    @classmethod
    def factory(cls, in_data: list[dict]) -> "EventBlock":
        """Process array of Events."""
        return cls.from_dict({"events": in_data})


@dataclass
class GasCostSummary(SuiTxReturnType, DataClassJsonMixin):
    """Gas used."""

    computation_cost: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    storage_cost: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    storage_rebate: int = field(metadata=config(letter_case=LetterCase.CAMEL))

    @property
    def total(self) -> int:
        """Totals all components of gas cost."""
        return int(self.computation_cost) + int(self.storage_cost) + int(self.storage_rebate)

    @property
    def total_after_rebate(self) -> int:
        """All cost after rebate removed."""
        return self.total - int(self.storage_rebate)


@dataclass
class Status(SuiTxReturnType, DataClassJsonMixin):
    """Status of transaction."""

    status: str
    error: Optional[str] = None
    succeeded: bool = field(init=False)

    def __post_init__(self):
        """Post init processing."""
        self.succeeded = self.status == "success"


# pylint: disable=too-many-instance-attributes


@dataclass
class Effects(SuiTxReturnType, DataClassJsonMixin):
    """Effects Certification."""

    status: Status
    message_version: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    gas_used: GasCostSummary = field(metadata=config(letter_case=LetterCase.CAMEL))
    transaction_digest: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    gas_object: GenericOwnerRef = field(metadata=config(letter_case=LetterCase.CAMEL))
    modified_at_versions: Optional[list[dict]] = field(
        metadata=config(letter_case=LetterCase.CAMEL), default_factory=list
    )
    dependencies: list[str] = field(default_factory=list)
    mutated: Optional[list[GenericOwnerRef]] = field(default_factory=list)
    created: Optional[list[GenericOwnerRef]] = field(default_factory=list)
    deleted: Optional[list[GenericRef]] = field(default_factory=list)
    wrapped: Optional[list[GenericRef]] = field(default_factory=list)
    unwrapped: Optional[list[GenericOwnerRef]] = field(default_factory=list)
    unwrapped_then_deleted: Optional[list[GenericOwnerRef]] = field(
        metadata=config(letter_case=LetterCase.CAMEL), default_factory=list
    )
    shared_objects: Optional[list[GenericRef]] = field(
        metadata=config(letter_case=LetterCase.CAMEL), default_factory=list
    )
    executed_epoch: Optional[int] = field(metadata=config(letter_case=LetterCase.CAMEL), default_factory=int)
    events_digest: Optional[str] = field(metadata=config(letter_case=LetterCase.CAMEL), default_factory=int)

    def __post_init__(self):
        """Post init processing.

        Hydrate relevant Events and other types
        """


@dataclass
class TxResponse(SuiTxReturnType, DataClassJsonMixin):
    """Transaction Result."""

    digest: str
    raw_transaction: Optional[str] = field(metadata=config(letter_case=LetterCase.CAMEL), default_factory=str)
    balance_changes: Optional[list[dict]] = field(metadata=config(letter_case=LetterCase.CAMEL), default_factory=dict)
    object_changes: Optional[list[dict]] = field(metadata=config(letter_case=LetterCase.CAMEL), default_factory=dict)
    transaction: Optional[dict] = field(default_factory=dict)
    errors: Optional[list[str]] = field(default_factory=list)
    effects: Optional[dict] = field(default_factory=dict)
    events: Optional[list[Event]] = field(default_factory=list)
    checkpoint: Optional[int] = field(default_factory=int)
    confirmed_local_execution: Optional[bool] = field(
        metadata=config(letter_case=LetterCase.CAMEL), default_factory=bool
    )
    timestamp_ms: Optional[int] = field(metadata=config(letter_case=LetterCase.CAMEL), default=0)

    def __post_init__(self):
        """Post init processing.

        Post process events lookup and transaction data
        """
        if self.effects:
            self.effects = Effects.from_dict(self.effects)
        if self.transaction:
            self.transaction = Transaction.from_dict(self.transaction)

    @property
    def succeeded(self) -> bool:
        """Check if transaction result is successful."""
        return self.effects.status.succeeded

    @property
    def status(self) -> str:
        """Get underlying status string."""
        if self.succeeded:
            return "success"
        return f"{self.effects.status.status} - {self.effects.status.error}"


# pylint: enable=too-many-instance-attributes


@dataclass
class TxResponseArray(SuiTxReturnType, DataClassJsonMixin):
    """From sui_multiGetTransactions."""

    transactions: list[TxResponse]

    @classmethod
    def factory(cls, in_data: list) -> "TxResponseArray":
        """."""
        return cls.from_dict({"transactions": in_data})


@dataclass
class DryRunTxResult(SuiTxReturnType, DataClassJsonMixin):
    """From sui_dryRunTransaction."""

    effects: Effects
    events: list[Event]
    input: dict
    object_changes: list[dict] = field(metadata=config(letter_case=LetterCase.CAMEL))
    balance_changes: list[dict] = field(metadata=config(letter_case=LetterCase.CAMEL))

    def __post_init__(self):
        """Post init processing.

        Post process events lookup
        """


@dataclass
class TxInspectionResult(SuiTxReturnType, DataClassJsonMixin):
    """From sui_devInspectTransaction and sui_devInspectMoveCall."""

    effects: Effects
    events: list[Event]
    results: Optional[list[dict]] = field(default_factory=list)
    error: Optional[str] = field(default_factory=str)

    def __post_init__(self):
        """Post init processing.

        Post process events lookup
        """

    @classmethod
    def factory(cls, in_data: dict) -> "TxInspectionResult":
        """."""
        return cls.from_dict(in_data)


@dataclass
class TransactionBytes(DataClassJsonMixin):
    """From pre-signed execution (i.e. sui_moveCall, sui_pay, etc.)."""

    gas: list[GenericRef]
    input_objects: list[dict] = field(metadata=config(letter_case=LetterCase.CAMEL))
    tx_bytes: str = field(metadata=config(letter_case=LetterCase.CAMEL))


@dataclass
class ECMHLiveObjectSetDigest(DataClassJsonMixin):
    """From sui_getCheckpoint."""

    digest: list[int]


@dataclass
class EndOfEpoch(DataClassJsonMixin):
    """From sui_getCheckpoint."""

    epoch_commitments: list[ECMHLiveObjectSetDigest] = field(metadata=config(letter_case=LetterCase.CAMEL))
    next_epoch_protocol_version: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    next_epoch_committee: Optional[list[int]] = field(
        metadata=config(letter_case=LetterCase.CAMEL), default_factory=list
    )


# pylint: disable=too-many-instance-attributes
@dataclass
class Checkpoint(DataClassJsonMixin):
    """From sui_getCheckpoint."""

    checkpoint_commitments: list[ECMHLiveObjectSetDigest] = field(metadata=config(letter_case=LetterCase.CAMEL))
    digest: str
    epoch: str
    epoch_rolling_gas_cost_summary: GasCostSummary = field(metadata=config(letter_case=LetterCase.CAMEL))
    validator_signature: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    network_total_transactions: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    sequence_number: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    timestamp_ms: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    previous_digest: str = field(default_factory=str, metadata=config(letter_case=LetterCase.CAMEL))
    end_of_epoch_data: Optional[dict] = field(default_factory=dict)
    transactions: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Post init processing.

        Post process end_of_epoch_data
        """
        if self.end_of_epoch_data:
            self.end_of_epoch_data = EndOfEpoch.from_dict(self.end_of_epoch_data)


# pylint: enable=too-many-instance-attributes


@dataclass
class Checkpoints(DataClassJsonMixin):
    """From sui_getCheckpoints."""

    data: list[Checkpoint]
    has_next_page: bool = field(metadata=config(letter_case=LetterCase.CAMEL))
    next_cursor: Optional[str] = field(metadata=config(letter_case=LetterCase.CAMEL))


@dataclass
@versionadded(version="0.17.0", reason="Support Sui 0.32.0 RPC API return type.")
class NameServices(DataClassJsonMixin):
    """From suix_resolveNameServiceNames."""

    data: list[str]
    has_next_page: bool = field(metadata=config(letter_case=LetterCase.CAMEL))
    next_cursor: Optional[str] = field(metadata=config(letter_case=LetterCase.CAMEL))


@dataclass
class SubscribedEventParms(SuiTxReturnType, DataClassJsonMixin):
    """From sui_subscribeEvents."""

    subscription: int
    # result: EventEnvelope
    result: Event


@dataclass
class SubscribedEvent(SuiTxReturnType, DataClassJsonMixin):
    """From sui_subscribeEvents."""

    jsonrpc: str
    method: str
    params: SubscribedEventParms


@dataclass
class TransactionQueryEnvelope(DataClassJsonMixin):
    """from suix_queryTransactionBlocks."""

    data: list[TxResponse]
    has_next_page: bool = field(metadata=config(field_name="hasNextPage"))
    next_cursor: Union[None, str] = field(metadata=config(field_name="nextCursor"))


@dataclass
class EventQueryEnvelope(DataClassJsonMixin):
    """From suix_queryEvents."""

    # data: list[EventEnvelope]
    data: list[Event]
    has_next_page: bool = field(metadata=config(field_name="hasNextPage"))
    next_cursor: Union[None, EventID] = field(metadata=config(field_name="nextCursor"))
