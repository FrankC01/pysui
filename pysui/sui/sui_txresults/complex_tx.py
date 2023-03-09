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


@dataclass
class ProgrammableTransaction(SuiTxReturnType, DataClassJsonMixin):
    """Programmable transaction type info."""

    commands: list[dict]
    inputs: list[dict]

    # def __post_init__(self):
    #     """."""
    #     print("Here")


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
    "ProgrammableTransaction": ProgrammableTransaction,
}


@dataclass
class TxGasData(SuiTxReturnType, DataClassJsonMixin):
    """Transaction Data."""

    budget: int
    owner: str
    price: int
    payment: list[GenericRef]


@dataclass
class TransactionData(SuiTxReturnType, DataClassJsonMixin):
    """Transaction Data."""

    sender: str
    message_version: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    gas_data: TxGasData = field(metadata=config(letter_case=LetterCase.CAMEL))
    transactions: list[dict] = field(default_factory=list)

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
    message_version: str = field(metadata=config(letter_case=LetterCase.CAMEL))
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
    executed_epoch: Optional[int] = field(metadata=config(letter_case=LetterCase.CAMEL), default_factory=int)
    events_digest: Optional[str] = field(metadata=config(letter_case=LetterCase.CAMEL), default_factory=int)

    def __post_init__(self):
        """Post init processing.

        Hydrate relevant Events and other types
        """


dummy = {
    "jsonrpc": "2.0",
    "result": {
        "digest": "6DWchPLVr1B6sfd5UkbzgyXS4kW7gMGvyjW9zjqEkCnF",
        "transaction": {
            "data": {
                "messageVersion": "v1",
                "transactions": [
                    {
                        "ProgrammableTransaction": {
                            "inputs": [],
                            "commands": [
                                {
                                    "Publish": {
                                        "disassembled": {
                                            "base": "// Move bytecode v6\nmodule 0.base {\nuse 0000000000000000000000000000000000000000000000000000000000000001::vector;\nuse 0000000000000000000000000000000000000000000000000000000000000002::dynamic_field;\nuse 0000000000000000000000000000000000000000000000000000000000000002::dynamic_object_field;\nuse 0000000000000000000000000000000000000000000000000000000000000002::object;\nuse 0000000000000000000000000000000000000000000000000000000000000002::transfer;\nuse 0000000000000000000000000000000000000000000000000000000000000002::tx_context;\n\n\nstruct Service has key {\n\tid: UID,\n\tadmin: address\n}\nstruct TrackerField has store, key {\n\tid: UID\n}\nstruct TrackerObjectField has store, key {\n\tid: UID\n}\nstruct ServiceTracker has key {\n\tid: UID,\n\tinitialized: bool,\n\thas_child_field: bool,\n\thas_child_object_field: bool,\n\tcount_accounts: u64\n}\nstruct Tracker has store, key {\n\tid: UID,\n\tinitialized: bool,\n\taccumulator: vector<u8>\n}\n\nis_owner(Arg0: &Service, Arg1: address): bool {\nB0:\n\t0: MoveLoc[0](Arg0: &Service)\n\t1: ImmBorrowField[0](Service.admin: address)\n\t2: ReadRef\n\t3: MoveLoc[1](Arg1: address)\n\t4: Eq\n\t5: Ret\n}\nadd_dynamic_field(Arg0: &mut ServiceTracker, Arg1: &mut TxContext) {\nB0:\n\t0: MoveLoc[1](Arg1: &mut TxContext)\n\t1: Call object::new(&mut TxContext): UID\n\t2: Pack[1](TrackerField)\n\t3: StLoc[2](loc0: TrackerField)\n\t4: CopyLoc[0](Arg0: &mut ServiceTracker)\n\t5: MutBorrowField[1](ServiceTracker.id: UID)\n\t6: LdConst[4](Vector(U8): [9, 100, 121, 110, 95, 102, 105, 101, 108, 100])\n\t7: MoveLoc[2](loc0: TrackerField)\n\t8: Call dynamic_field::add<vector<u8>, TrackerField>(&mut UID, vector<u8>, TrackerField)\n\t9: LdTrue\n\t10: MoveLoc[0](Arg0: &mut ServiceTracker)\n\t11: MutBorrowField[2](ServiceTracker.has_child_field: bool)\n\t12: WriteRef\n\t13: Ret\n}\nadd_dynamic_object_field(Arg0: &mut ServiceTracker, Arg1: &mut TxContext) {\nB0:\n\t0: MoveLoc[1](Arg1: &mut TxContext)\n\t1: Call object::new(&mut TxContext): UID\n\t2: Pack[2](TrackerObjectField)\n\t3: StLoc[2](loc0: TrackerObjectField)\n\t4: CopyLoc[0](Arg0: &mut ServiceTracker)\n\t5: MutBorrowField[1](ServiceTracker.id: UID)\n\t6: LdConst[5](Vector(U8): [13, 100, 121, 110, 95, 111, 98, 106, 95, 102, 105, 101, 108, 100])\n\t7: MoveLoc[2](loc0: TrackerObjectField)\n\t8: Call dynamic_object_field::add<vector<u8>, TrackerObjectField>(&mut UID, vector<u8>, TrackerObjectField)\n\t9: LdTrue\n\t10: MoveLoc[0](Arg0: &mut ServiceTracker)\n\t11: MutBorrowField[3](ServiceTracker.has_child_object_field: bool)\n\t12: WriteRef\n\t13: Ret\n}\nincrease_account(Arg0: &mut ServiceTracker) {\nB0:\n\t0: CopyLoc[0](Arg0: &mut ServiceTracker)\n\t1: ImmBorrowField[4](ServiceTracker.count_accounts: u64)\n\t2: ReadRef\n\t3: LdU64(1)\n\t4: Add\n\t5: MoveLoc[0](Arg0: &mut ServiceTracker)\n\t6: MutBorrowField[4](ServiceTracker.count_accounts: u64)\n\t7: WriteRef\n\t8: Ret\n}\npublic accounts_created(Arg0: &ServiceTracker): u64 {\nB0:\n\t0: MoveLoc[0](Arg0: &ServiceTracker)\n\t1: ImmBorrowField[4](ServiceTracker.count_accounts: u64)\n\t2: ReadRef\n\t3: Ret\n}\npublic transfer(Arg0: Tracker, Arg1: address) {\nB0:\n\t0: MoveLoc[0](Arg0: Tracker)\n\t1: MoveLoc[1](Arg1: address)\n\t2: Call transfer::transfer<Tracker>(Tracker, address)\n\t3: Ret\n}\npublic stored_count(Arg0: &Tracker): u64 {\nB0:\n\t0: MoveLoc[0](Arg0: &Tracker)\n\t1: ImmBorrowField[5](Tracker.accumulator: vector<u8>)\n\t2: VecLen(12)\n\t3: Ret\n}\npublic add_to_store(Arg0: &mut Tracker, Arg1: u8): u64 {\nB0:\n\t0: CopyLoc[0](Arg0: &mut Tracker)\n\t1: MutBorrowField[5](Tracker.accumulator: vector<u8>)\n\t2: MoveLoc[1](Arg1: u8)\n\t3: VecPushBack(12)\n\t4: MoveLoc[0](Arg0: &mut Tracker)\n\t5: FreezeRef\n\t6: Call stored_count(&Tracker): u64\n\t7: Ret\n}\npublic add_from(Arg0: &mut Tracker, Arg1: vector<u8>) {\nB0:\n\t0: MoveLoc[0](Arg0: &mut Tracker)\n\t1: MutBorrowField[5](Tracker.accumulator: vector<u8>)\n\t2: MoveLoc[1](Arg1: vector<u8>)\n\t3: Call vector::append<u8>(&mut vector<u8>, vector<u8>)\n\t4: Ret\n}\npublic has_value(Arg0: &Tracker, Arg1: u8): bool {\nB0:\n\t0: MoveLoc[0](Arg0: &Tracker)\n\t1: ImmBorrowField[5](Tracker.accumulator: vector<u8>)\n\t2: ImmBorrowLoc[1](Arg1: u8)\n\t3: Call vector::contains<u8>(&vector<u8>, &u8): bool\n\t4: Ret\n}\npublic drop_from_store(Arg0: &mut Tracker, Arg1: u8): u8 {\nB0:\n\t0: CopyLoc[0](Arg0: &mut Tracker)\n\t1: ImmBorrowField[5](Tracker.accumulator: vector<u8>)\n\t2: ImmBorrowLoc[1](Arg1: u8)\n\t3: Call vector::index_of<u8>(&vector<u8>, &u8): bool * u64\n\t4: StLoc[2](loc0: u64)\n\t5: BrFalse(7)\nB1:\n\t6: Branch(11)\nB2:\n\t7: MoveLoc[0](Arg0: &mut Tracker)\n\t8: Pop\n\t9: LdConst[2](U64: [2, 0, 0, 0, 0, 0, 0, 0])\n\t10: Abort\nB3:\n\t11: MoveLoc[0](Arg0: &mut Tracker)\n\t12: MutBorrowField[5](Tracker.accumulator: vector<u8>)\n\t13: MoveLoc[2](loc0: u64)\n\t14: Call vector::remove<u8>(&mut vector<u8>, u64): u8\n\t15: Ret\n}\npublic create_service(Arg0: &mut TxContext) {\nB0:\n\t0: CopyLoc[0](Arg0: &mut TxContext)\n\t1: FreezeRef\n\t2: Call tx_context::sender(&TxContext): address\n\t3: StLoc[1](loc0: address)\n\t4: MoveLoc[0](Arg0: &mut TxContext)\n\t5: Call object::new(&mut TxContext): UID\n\t6: MoveLoc[1](loc0: address)\n\t7: Pack[0](Service)\n\t8: Call transfer::freeze_object<Service>(Service)\n\t9: Ret\n}\npublic create_service_tracker(Arg0: &mut TxContext) {\nB0:\n\t0: CopyLoc[0](Arg0: &mut TxContext)\n\t1: FreezeRef\n\t2: Call tx_context::sender(&TxContext): address\n\t3: StLoc[1](loc0: address)\n\t4: MoveLoc[0](Arg0: &mut TxContext)\n\t5: Call object::new(&mut TxContext): UID\n\t6: LdTrue\n\t7: LdFalse\n\t8: LdFalse\n\t9: LdU64(0)\n\t10: Pack[3](ServiceTracker)\n\t11: MoveLoc[1](loc0: address)\n\t12: Call transfer::transfer<ServiceTracker>(ServiceTracker, address)\n\t13: Ret\n}\ninit(Arg0: &mut TxContext) {\nB0:\n\t0: CopyLoc[0](Arg0: &mut TxContext)\n\t1: Call create_service(&mut TxContext)\n\t2: MoveLoc[0](Arg0: &mut TxContext)\n\t3: Call create_service_tracker(&mut TxContext)\n\t4: Ret\n}\nentry public set_dynamic_field(Arg0: &mut ServiceTracker, Arg1: &mut TxContext) {\nB0:\n\t0: MoveLoc[0](Arg0: &mut ServiceTracker)\n\t1: MoveLoc[1](Arg1: &mut TxContext)\n\t2: Call add_dynamic_field(&mut ServiceTracker, &mut TxContext)\n\t3: Ret\n}\nentry public set_dynamic_object_field(Arg0: &mut ServiceTracker, Arg1: &mut TxContext) {\nB0:\n\t0: MoveLoc[0](Arg0: &mut ServiceTracker)\n\t1: MoveLoc[1](Arg1: &mut TxContext)\n\t2: Call add_dynamic_object_field(&mut ServiceTracker, &mut TxContext)\n\t3: Ret\n}\nentry public create_account(Arg0: &Service, Arg1: &mut ServiceTracker, Arg2: address, Arg3: &mut TxContext) {\nB0:\n\t0: CopyLoc[3](Arg3: &mut TxContext)\n\t1: FreezeRef\n\t2: Call tx_context::sender(&TxContext): address\n\t3: StLoc[4](loc0: address)\n\t4: MoveLoc[0](Arg0: &Service)\n\t5: MoveLoc[4](loc0: address)\n\t6: Call is_owner(&Service, address): bool\n\t7: BrFalse(9)\nB1:\n\t8: Branch(15)\nB2:\n\t9: MoveLoc[1](Arg1: &mut ServiceTracker)\n\t10: Pop\n\t11: MoveLoc[3](Arg3: &mut TxContext)\n\t12: Pop\n\t13: LdConst[0](U64: [0, 0, 0, 0, 0, 0, 0, 0])\n\t14: Abort\nB3:\n\t15: MoveLoc[1](Arg1: &mut ServiceTracker)\n\t16: Call increase_account(&mut ServiceTracker)\n\t17: MoveLoc[3](Arg3: &mut TxContext)\n\t18: Call object::new(&mut TxContext): UID\n\t19: LdTrue\n\t20: LdConst[6](Vector(U8): [0])\n\t21: Pack[4](Tracker)\n\t22: MoveLoc[2](Arg2: address)\n\t23: Call transfer::transfer<Tracker>(Tracker, address)\n\t24: Ret\n}\nentry public add_value(Arg0: &mut Tracker, Arg1: u8, Arg2: &mut TxContext) {\nB0:\n\t0: MoveLoc[0](Arg0: &mut Tracker)\n\t1: MoveLoc[1](Arg1: u8)\n\t2: Call add_to_store(&mut Tracker, u8): u64\n\t3: Pop\n\t4: Ret\n}\nentry public remove_value(Arg0: &mut Tracker, Arg1: u8, Arg2: &mut TxContext) {\nB0:\n\t0: MoveLoc[0](Arg0: &mut Tracker)\n\t1: CopyLoc[1](Arg1: u8)\n\t2: Call drop_from_store(&mut Tracker, u8): u8\n\t3: MoveLoc[1](Arg1: u8)\n\t4: Eq\n\t5: BrFalse(7)\nB1:\n\t6: Branch(9)\nB2:\n\t7: LdConst[3](U64: [3, 0, 0, 0, 0, 0, 0, 0])\n\t8: Abort\nB3:\n\t9: Ret\n}\nentry public add_values(Arg0: &mut Tracker, Arg1: vector<u8>, Arg2: &mut TxContext) {\nB0:\n\t0: MoveLoc[0](Arg0: &mut Tracker)\n\t1: MoveLoc[1](Arg1: vector<u8>)\n\t2: Call add_from(&mut Tracker, vector<u8>)\n\t3: Ret\n}\n}"
                                        }
                                    }
                                }
                            ],
                        }
                    }
                ],
                "sender": "0xabfb3da1ccf95f2c0976b46c421fb89a765913089186d6ef9cc275258460e885",
                "gasData": {
                    "payment": [
                        {
                            "objectId": "0x21de82323c47d92d787a640592dceb8d898989c40335d1341d466bde6e930bd4",
                            "version": 1,
                            "digest": "EfEbK299x7mXsqkSNDVYB5VRw9GcawLSYeTzEBU6MCQX",
                        }
                    ],
                    "owner": "0xabfb3da1ccf95f2c0976b46c421fb89a765913089186d6ef9cc275258460e885",
                    "price": 1,
                    "budget": 3000,
                },
            },
            "txSignatures": [
                "AJGHQsxah45dBGnONFw8221MI3lSL5MdUmltigKlcE5i+N4eJJ5myjovgmySNpnQf9hgt1WJqtYOlIdXiKVqwQEtc4qqvxVrdF+oUUJnATaD25ZViWzx35HlqqsMMHgx3g=="
            ],
        },
        "effects": {
            "messageVersion": "v1",
            "status": {"status": "success"},
            "executedEpoch": 0,
            "gasUsed": {"computationCost": 390, "storageCost": 234, "storageRebate": 0},
            "transactionDigest": "6DWchPLVr1B6sfd5UkbzgyXS4kW7gMGvyjW9zjqEkCnF",
            "created": [
                {
                    "owner": "Immutable",
                    "reference": {
                        "objectId": "0x764ae5e43c4f9170436ef8c675b70f2b045428ff48757082ba186d5964cf3479",
                        "version": 1,
                        "digest": "95AeE8mTRkPYMHwqWvDKiKGLcu1ziWtMHa4RBntLEUPp",
                    },
                },
                {
                    "owner": "Immutable",
                    "reference": {
                        "objectId": "0x86257ab5c44d8646833c3c8f0cf77fcf92c031056858357d1d1ad68439298f1f",
                        "version": 2,
                        "digest": "BaUKa65jTwSwRBG6HoQeYB5RTFFKMRTMQhEkTNVea2kC",
                    },
                },
                {
                    "owner": {"AddressOwner": "0xabfb3da1ccf95f2c0976b46c421fb89a765913089186d6ef9cc275258460e885"},
                    "reference": {
                        "objectId": "0xddbacae8aad6192ad69b855dd066d719f6e6b82a9ef55682fe69c94cfc6a8197",
                        "version": 2,
                        "digest": "HYzPEJNwoPHbndzcYXVV8Tm7ewCmQiCKZxEeHgc8fWdP",
                    },
                },
            ],
            "mutated": [
                {
                    "owner": {"AddressOwner": "0xabfb3da1ccf95f2c0976b46c421fb89a765913089186d6ef9cc275258460e885"},
                    "reference": {
                        "objectId": "0x21de82323c47d92d787a640592dceb8d898989c40335d1341d466bde6e930bd4",
                        "version": 2,
                        "digest": "5TUq3qBuJrpLapGTAZeWmCi31SMbpXg6JUuEnEh3SQth",
                    },
                }
            ],
            "gasObject": {
                "owner": {"AddressOwner": "0xabfb3da1ccf95f2c0976b46c421fb89a765913089186d6ef9cc275258460e885"},
                "reference": {
                    "objectId": "0x21de82323c47d92d787a640592dceb8d898989c40335d1341d466bde6e930bd4",
                    "version": 2,
                    "digest": "5TUq3qBuJrpLapGTAZeWmCi31SMbpXg6JUuEnEh3SQth",
                },
            },
            "eventsDigest": "HiyNFQd83yKwcHQiNtUtF83Ai5njApAP7RCfM1EYmRj2",
            "dependencies": ["4oQmWVqp7o3Cqqr4nhvVskbSdRPfwquFDH3Eo8WZmihX"],
        },
        "timestampMs": 1678365852173,
        "checkpoint": 7926,
    },
    "id": 1,
}


@dataclass
class TxResponse(SuiTxReturnType, DataClassJsonMixin):
    """Transaction Result."""

    digest: Optional[str] = field(default_factory=str)
    transaction: Optional[dict] = field(default_factory=dict)
    errors: Optional[list[str]] = field(default_factory=list)
    effects: Optional[dict] = field(default_factory=dict)
    events: Optional[list[dict]] = field(default_factory=list)
    checkpoint: Optional[int] = field(default_factory=int)
    confirmed_local_execution: Optional[bool] = field(
        metadata=config(letter_case=LetterCase.CAMEL), default_factory=bool
    )
    timestamp_ms: Optional[int] = field(metadata=config(field_name="timestampMs"), default_factory=int)

    def __post_init__(self):
        """Post init processing.

        Post process events lookup and transaction data
        """
        hydrated = []
        for ev_dict in self.events:
            key = list(ev_dict.keys())[0]
            hydrated.append({key: _EVENT_LOOKUP[key].from_dict(ev_dict[key])})
        self.events = hydrated
        if self.effects:
            self.effects = Effects.from_dict(self.effects)
        if self.transaction:
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
