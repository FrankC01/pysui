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
from pysui.sui.sui_txresults.common import CoinRef, GenericOwnerRef, GenericRef, SuiTxReturnType
from pysui.sui.sui_types.collections import EventID


@dataclass
class MoveCallTx(SuiTxReturnType, DataClassJsonMixin):
    """sui_moveCall transaction."""

    function: str
    module: str
    package: str
    arguments: list[Any] = field(default_factory=list)
    type_arguments: list[Any] = field(metadata=config(letter_case=LetterCase.CAMEL), default_factory=list)


@dataclass
class PayTx(SuiTxReturnType, DataClassJsonMixin):
    """sui_pay transaction."""

    coins: list[CoinRef]
    amounts: list[int]
    recipients: list[str]


@dataclass
class PayAllSuiTx(SuiTxReturnType, DataClassJsonMixin):
    """sui_payAllSui transaction."""

    coins: list[CoinRef]
    recipient: str


@dataclass
class PaySuiTx(SuiTxReturnType, DataClassJsonMixin):
    """sui_paySui transaction."""

    coins: list[CoinRef]
    amounts: list[int]
    recipients: list[str]


@dataclass
class PublishTx(SuiTxReturnType, DataClassJsonMixin):
    """sui_publish transaction."""

    disassembled: dict[str, str]


@dataclass
class TransferObjectTx(SuiTxReturnType, DataClassJsonMixin):
    """sui_transferObject transaction."""

    object_ref: GenericRef = field(metadata=config(letter_case=LetterCase.CAMEL))
    recipient: str


@dataclass
class TransferSuiTx(SuiTxReturnType, DataClassJsonMixin):
    """sui_transferSui transaction."""

    recipient: str
    amount: int


@dataclass
class ChangeEpocTx(SuiTxReturnType, DataClassJsonMixin):
    """From sui_executeTransaction forms."""

    computation_charge: int
    epoch: int
    storage_charge: int


@dataclass
class GenesisTx(SuiTxReturnType, DataClassJsonMixin):
    """From sui_executeTransaction forms."""

    objects: list[str]


@dataclass
class AuthSignerInfo(SuiTxReturnType, DataClassJsonMixin):
    """Authorized signer info."""

    epoch: int
    signature: str
    signers_map: list[int]


_TRANSACTION_LOOKUP = {
    "Call": MoveCallTx,
    "Pay": PayTx,
    "PaySui": PaySuiTx,
    "PayAllSui": PayAllSuiTx,
    "Publish": PublishTx,
    "TransferObject": TransferObjectTx,
    "TransferSui": TransferSuiTx,
    "ChangeEpoch": ChangeEpocTx,
    "Genesis": GenesisTx,
}


@dataclass
class TxGasData(SuiTxReturnType, DataClassJsonMixin):
    """Transaction Data."""

    budget: int
    owner: str
    price: int
    payment: GenericRef


@dataclass
class TransactionData(SuiTxReturnType, DataClassJsonMixin):
    """Transaction Data."""

    sender: str
    gas_data: TxGasData = field(metadata=config(letter_case=LetterCase.CAMEL))
    # gas_payment: CoinRef = field(metadata=config(letter_case=LetterCase.CAMEL))
    # gas_budget: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    transactions: list[Any] = None

    def __post_init__(self):
        """Post init processing.

        Loops through the transactions list to resolve hydrating different transaction type classes
        """
        hydrated = []
        for tx_dict in self.transactions:
            key = list(tx_dict.keys())[0]
            hydrated.append(_TRANSACTION_LOOKUP[key].from_dict(tx_dict[key]))
        self.transactions = hydrated


# Events


@dataclass
class CoinBalanceChangeEvent(SuiTxReturnType, DataClassJsonMixin):
    """Event Type."""

    package_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    transaction_module: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    sender: str
    owner: dict
    change_type: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    coin_type: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    coin_object_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    version: int
    amount: int

    def __post_init__(self):
        """Post init processing.

        Convert various to SuiTypes
        """
        self.owner = self.owner["AddressOwner"]


@dataclass
class NewObjectEvent(SuiTxReturnType, DataClassJsonMixin):
    """Event Type."""

    package_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    transaction_module: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    sender: str
    recipient: Union[dict, str]
    version: int
    object_type: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    object_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))

    def __post_init__(self):
        """Post init processing.

        Convert various to SuiTypes
        """
        if isinstance(self.recipient, str):
            if self.recipient == "Immutable":
                self.recipient = self.recipient
            else:
                raise KeyError(f"{self.recipient}")
        else:
            if "AddressOwner" in self.recipient:
                self.recipient = self.recipient["AddressOwner"]
            elif "ObjectOwner" in self.recipient:
                self.recipient = self.recipient["ObjectOwner"]


@dataclass
class TransferObjectEvent(SuiTxReturnType, DataClassJsonMixin):
    """Event Type."""

    package_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    transaction_module: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    sender: str
    recipient: dict
    version: int
    object_type: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    object_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))

    def __post_init__(self):
        """Post init processing.

        Convert various to SuiTypes
        """
        if isinstance(self.recipient, str):
            if self.recipient == "Immutable":
                self.recipient = self.recipient
        else:
            if isinstance(self.recipient, str):
                if self.recipient == "Immutable":
                    self.recipient = self.recipient
                else:
                    raise KeyError(f"{self.recipient}")
            else:
                if "AddressOwner" in self.recipient:
                    self.recipient = self.recipient["AddressOwner"]
                elif "ObjectOwner" in self.recipient:
                    self.recipient = self.recipient["ObjectOwner"]


@dataclass
class MutateObjectEvent(SuiTxReturnType, DataClassJsonMixin):
    """Event Type."""

    package_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    transaction_module: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    sender: str
    object_type: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    object_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    version: int


@dataclass
class DeleteObjectEvent(SuiTxReturnType, DataClassJsonMixin):
    """Event Type."""

    package_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    transaction_module: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    sender: str
    object_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    version: int


@dataclass
class EpochChangeEvent(SuiTxReturnType, DataClassJsonMixin):
    """Event Type."""

    epoch_change: int = field(metadata=config(letter_case=LetterCase.CAMEL))


@dataclass
class NewCheckpointEvent(SuiTxReturnType, DataClassJsonMixin):
    """Event Type."""

    checkpoint: int = field(metadata=config(letter_case=LetterCase.CAMEL))


@dataclass
class PublishEvent(SuiTxReturnType, DataClassJsonMixin):
    """Event Type."""

    package_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    sender: str
    digest: str
    version: int


@dataclass
class MoveEvent(SuiTxReturnType, DataClassJsonMixin):
    """Event Type."""

    package_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    transaction_module: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    sender: str
    event_type: str = field(metadata=config(field_name="type"))
    bcs: str
    fields: dict


_EVENT_LOOKUP = {
    "coinBalanceChange": CoinBalanceChangeEvent,
    "newObject": NewObjectEvent,
    "transferObject": TransferObjectEvent,
    "mutateObject": MutateObjectEvent,
    "deleteObject": DeleteObjectEvent,
    "epochChange": EpochChangeEvent,
    "newCheckPoint": NewCheckpointEvent,
    "publish": PublishEvent,
    "moveEvent": MoveEvent,
}


@dataclass
class GasCostSummary(SuiTxReturnType, DataClassJsonMixin):
    """Gas used."""

    computation_cost: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    storage_cost: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    storage_rebate: int = field(metadata=config(letter_case=LetterCase.CAMEL))


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
    gas_used: GasCostSummary = field(metadata=config(letter_case=LetterCase.CAMEL))
    transaction_digest: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    gas_object: GenericOwnerRef = field(metadata=config(letter_case=LetterCase.CAMEL))
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
    executed_epoch: Optional[int] = field(metadata=config(letter_case=LetterCase.CAMEL), default_factory=None)
    events_digest: Optional[str] = field(metadata=config(letter_case=LetterCase.CAMEL), default_factory=None)

    def __post_init__(self):
        """Post init processing.

        Hydrate relevant Events and other types
        """


@dataclass
class TxResponse(SuiTxReturnType, DataClassJsonMixin):
    """Transaction Result."""

    effects: Effects
    events: list[dict]
    transaction: dict
    checkpoint: Optional[int]
    confirmed_local_execution: Optional[bool] = field(
        metadata=config(letter_case=LetterCase.CAMEL), default_factory=bool
    )
    timestamp_ms: int = field(metadata=config(letter_case=LetterCase.CAMEL), default_factory=int)

    def __post_init__(self):
        """Post init processing.

        Post process events lookup and transaction data
        """
        hydrated = []
        for ev_dict in self.events:
            key = list(ev_dict.keys())[0]
            hydrated.append({key: _EVENT_LOOKUP[key].from_dict(ev_dict[key])})
        self.events = hydrated
        self.transaction = TransactionData.from_dict(self.transaction["data"])

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
    events: list[dict]

    def __post_init__(self):
        """Post init processing.

        Post process events lookup
        """
        hydrated = []
        for ev_dict in self.events:
            key = list(ev_dict.keys())[0]
            hydrated.append({key: _EVENT_LOOKUP[key].from_dict(ev_dict[key])})
        self.events = hydrated


@dataclass
class TxInspectionResult(SuiTxReturnType, DataClassJsonMixin):
    """From sui_devInspectTransaction and sui_devInspectMoveCall."""

    effects: Effects
    results: dict
    events: list[dict]

    def __post_init__(self):
        """Post init processing.

        Post process events lookup
        """
        hydrated = []
        for ev_dict in self.events:
            key = list(ev_dict.keys())[0]
            hydrated.append({key: _EVENT_LOOKUP[key].from_dict(ev_dict[key])})
        self.events = hydrated

    @classmethod
    def factory(cls, in_data: dict) -> "TxInspectionResult":
        """."""
        return cls.from_dict(in_data)


# TODO: Trace for removal
@dataclass
class ExecutionDigests(DataClassJsonMixin):
    """From sui_getCheckpointContents sui_getCheckpointContentsBySequenceNumber."""

    effects: str
    transaction: str


# TODO: Trace for removal
@dataclass
class CheckpointContents(DataClassJsonMixin):
    """From sui_getCheckpointContents sui_getCheckpointContentsBySequenceNumber."""

    transactions: list[ExecutionDigests]
    user_signatures: list[Union[str, dict]]


@dataclass
class ECMHLiveObjectSetDigest(DataClassJsonMixin):
    """From sui_getCheckpoint."""

    digest: list[int]


@dataclass
class EndOfEpoch(DataClassJsonMixin):
    """From sui_getCheckpoint."""

    # "epoch_commitments",
    # "next_epoch_committee",
    # "next_epoch_protocol_version"

    epoch_commitments: list[ECMHLiveObjectSetDigest]
    next_epoch_protocol_version: int
    # root_state_digest: list[int]
    next_epoch_committee: Optional[list[int]] = field(default_factory=list)


# TODO: Trace for removal
@dataclass
class CheckpointSummary(DataClassJsonMixin):
    """From sui_getCheckpointSummary."""

    content_digest: str
    epoch: int
    epoch_rolling_gas_cost_summary: GasCostSummary
    network_total_transactions: int
    sequence_number: int

    timestamp_ms: int
    end_of_epoch_data: Optional[EndOfEpoch]
    version_specific_data: list[int] = field(default_factory=dict)
    previous_digest: str = field(default_factory=str)

    # next_epoch_committee: list[int] = field(default_factory=list)


@dataclass
class Checkpoint(DataClassJsonMixin):
    """From sui_getCheckpoint."""

    checkpoint_commitments: list[ECMHLiveObjectSetDigest] = field(metadata=config(letter_case=LetterCase.CAMEL))
    digest: str
    epoch: int
    epoch_rolling_gas_cost_summary: GasCostSummary = field(metadata=config(letter_case=LetterCase.CAMEL))
    network_total_transactions: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    sequence_number: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    timestamp_ms: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    previous_digest: str = field(default_factory=str, metadata=config(letter_case=LetterCase.CAMEL))
    end_of_epoch_data: Optional[dict] = field(default_factory=dict)
    transactions: list[int] = field(default_factory=list)

    def __post_init__(self):
        """Post init processing.

        Post process end_of_epoch_data
        """
        if self.end_of_epoch_data:
            self.end_of_epoch_data = EndOfEpoch.from_dict(self.end_of_epoch_data)


# Event query results


@dataclass
class EventEnvelopID(DataClassJsonMixin):
    """From sui_getEvents."""

    transaction_digest: str = field(metadata=config(field_name="txDigest"))
    event_sequence: int = field(metadata=config(field_name="eventSeq"))


@dataclass
class EventEnvelope(DataClassJsonMixin):
    """From sui_getEvents."""

    timestamp: int
    event: dict
    transaction_digest: str = field(metadata=config(field_name="txDigest"))
    event_id: EventEnvelopID = field(metadata=config(field_name="id"))

    def __post_init__(self):
        """Post init processing.

        Hydrate relevant Events and other types
        """
        ev_map = list(self.event.items())
        event_key = ev_map[0][0]
        event_value = ev_map[0][1]
        self.event[event_key] = _EVENT_LOOKUP[event_key].from_dict(event_value)


@dataclass
class SubscribedEventParms(SuiTxReturnType, DataClassJsonMixin):
    """From sui_subscribeEvents."""

    subscription: int
    result: EventEnvelope


@dataclass
class SubscribedEvent(SuiTxReturnType, DataClassJsonMixin):
    """From sui_subscribeEvents."""

    jsonrpc: str
    method: str
    params: SubscribedEventParms


# @dataclass
# class TransactionEnvelope(SuiTxReturnType, DataClassJsonMixin):
#     """Effects Certification."""

#     certificate: Optional[Certificate]
#     effects: Effects
#     timestamp_ms: int
#     parsed_data: Union[dict, None] = field(default_factory=dict)
#     checkpoint: int = None


@dataclass
class EventQueryEnvelope(DataClassJsonMixin):
    """From sui_getEvents."""

    data: list[EventEnvelope]
    next_cursor: Union[None, EventID] = field(metadata=config(field_name="nextCursor"))


@dataclass
class TransactionQueryEnvelope(DataClassJsonMixin):
    """From sui_getTransactions."""

    data: list[str]
    next_cursor: Union[None, dict] = field(metadata=config(field_name="nextCursor"))
