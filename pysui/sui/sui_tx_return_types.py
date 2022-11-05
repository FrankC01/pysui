#    Copyright 2022 Frank V. Castellucci
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

"""Transaction based return types."""
from abc import ABC
from dataclasses import dataclass, field
from typing import Any, Optional, Union
from dataclasses_json import DataClassJsonMixin, LetterCase, config


class SuiJsonReturnType(ABC):
    """Abstraction for all return objects."""


@dataclass
class GenericRef(SuiJsonReturnType, DataClassJsonMixin):
    """Generic object reference."""

    object_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    version: int
    digest: str

    def __post_init__(self):
        """Post init processing.

        Convert object_id string to ObjectID type
        """


@dataclass
class CoinRef(GenericRef):
    """Coin representation."""


@dataclass
class GenericOwnerRef(SuiJsonReturnType, DataClassJsonMixin):
    """Owned coin referenece."""

    owner: Union[dict, str]
    reference: GenericRef


@dataclass
class PackageRef(SuiJsonReturnType, DataClassJsonMixin):
    """Package representation."""

    object_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    version: int
    digest: str

    def __post_init__(self):
        """Post init processing.

        Convert object_id string to ObjectID type
        """


@dataclass
class MoveCallTx(SuiJsonReturnType, DataClassJsonMixin):
    """sui_moveCall transaction."""

    function: str
    module: str
    package: dict
    arguments: list[str]
    type_arguments: Optional[list[str]] = field(metadata=config(letter_case=LetterCase.CAMEL), default_factory=list)


@dataclass
class PayTx(SuiJsonReturnType, DataClassJsonMixin):
    """sui_pay transaction."""

    coins: list[CoinRef]
    amounts: list[int]
    recipient: list[str]


@dataclass
class PayAllSuiTx(SuiJsonReturnType, DataClassJsonMixin):
    """sui_payAllSui transaction."""

    coins: list[CoinRef]
    recipient: str


@dataclass
class PaySuiTx(SuiJsonReturnType, DataClassJsonMixin):
    """sui_paySui transaction."""

    coins: list[CoinRef]
    amounts: list[int]
    recipients: list[str]


@dataclass
class PublishTx(SuiJsonReturnType, DataClassJsonMixin):
    """sui_publish transaction."""

    disassembled: dict


@dataclass
class TransferObjectTx(SuiJsonReturnType, DataClassJsonMixin):
    """sui_transferObject transaction."""

    object_ref: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    recipient: str  # Replace with SuiAddress when validated


@dataclass
class TransferSuiTx(SuiJsonReturnType, DataClassJsonMixin):
    """sui_transferSui transaction."""

    recipient: str  # Replace with SuiAddress when validated
    amouont: str = None


@dataclass
class AuthSignerInfo(SuiJsonReturnType, DataClassJsonMixin):
    """Authorized signer info."""

    epoch: int
    signature: str  # Replace with SuiSignature when validated
    signers_map: list[int]


_TRANSACTION_LOOKUP = {
    "Call": MoveCallTx,
    "Pay": PayTx,
    "PaySui": PaySuiTx,
    "PayAllSui": PayAllSuiTx,
    "Publish": PublishTx,
    "TransferObject": TransferObjectTx,
    "TransferSui": TransferSuiTx,
}


@dataclass
class TransactionData(SuiJsonReturnType, DataClassJsonMixin):
    """Transaction Data."""

    sender: str
    gas_payment: CoinRef = field(metadata=config(letter_case=LetterCase.CAMEL))
    gas_budget: int = field(metadata=config(letter_case=LetterCase.CAMEL))
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
class CoinBalanceChangeEvent(SuiJsonReturnType, DataClassJsonMixin):
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


@dataclass
class NewObjectEvent(SuiJsonReturnType, DataClassJsonMixin):
    """Event Type."""

    package_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    transaction_module: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    sender: str
    recipient: Union[dict, str]
    version: int
    object_type: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    object_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))


@dataclass
class TransferObjectEvent(SuiJsonReturnType, DataClassJsonMixin):
    """Event Type."""

    package_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    transaction_module: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    sender: str
    recipient: dict
    version: int
    object_type: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    object_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))


@dataclass
class MutateObjectEvent(SuiJsonReturnType, DataClassJsonMixin):
    """Event Type."""

    package_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    transaction_module: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    sender: str
    object_type: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    object_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    version: int


@dataclass
class DeleteObjectEvent(SuiJsonReturnType, DataClassJsonMixin):
    """Event Type."""

    package_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    transaction_module: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    sender: str
    object_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    version: int


@dataclass
class EpochChangeEvent(SuiJsonReturnType, DataClassJsonMixin):
    """Event Type."""

    epoch_change: int = field(metadata=config(letter_case=LetterCase.CAMEL))


@dataclass
class NewCheckpointEvent(SuiJsonReturnType, DataClassJsonMixin):
    """Event Type."""

    checkpoint: int = field(metadata=config(letter_case=LetterCase.CAMEL))


@dataclass
class PublishEvent(SuiJsonReturnType, DataClassJsonMixin):
    """Event Type."""

    package_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    sender: str


_EVENT_LOOKUP = {
    "coinBalanceChange": CoinBalanceChangeEvent,
    "newObject": NewObjectEvent,
    "transferObject": TransferObjectEvent,
    "mutateObject": MutateObjectEvent,
    "deleteObject": DeleteObjectEvent,
    "epochChange": EpochChangeEvent,
    "newCheckPoint": NewCheckpointEvent,
    "publish": PublishEvent,
}


@dataclass
class GasCostSummary(SuiJsonReturnType, DataClassJsonMixin):
    """Gas used."""

    computation_cost: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    storage_cost: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    storage_rebate: int = field(metadata=config(letter_case=LetterCase.CAMEL))


@dataclass
class Status(SuiJsonReturnType, DataClassJsonMixin):
    """Status of transaction."""

    status: str
    error: str = None
    succeeded: bool = field(init=False)

    def __post_init__(self):
        """Post init processing."""
        self.succeeded = True if self.status == "success" else False


@dataclass
class Effects(SuiJsonReturnType, DataClassJsonMixin):
    """Effects Certification."""

    status: Status
    gas_used: GasCostSummary = field(metadata=config(letter_case=LetterCase.CAMEL))
    transaction_digest: str = field(metadata=config(letter_case=LetterCase.CAMEL))

    gas_object: GenericOwnerRef = field(metadata=config(letter_case=LetterCase.CAMEL))
    events: list[dict]
    dependencies: list[str] = field(default_factory=list)
    mutated: Optional[list[GenericOwnerRef]] = field(default_factory=list)
    created: Optional[list[GenericOwnerRef]] = field(default_factory=list)
    deleted: Optional[list[GenericOwnerRef]] = field(default_factory=list)
    wrapped: Optional[list[GenericOwnerRef]] = field(default_factory=list)
    unwrapped: Optional[list[GenericOwnerRef]] = field(default_factory=list)
    shared_objects: Optional[list[GenericOwnerRef]] = field(
        metadata=config(letter_case=LetterCase.CAMEL), default_factory=list
    )

    def __post_init__(self):
        """Post init processing.

        Hydrate relevant Events
        """
        hydrated = []
        for ev_dict in self.events:
            key = list(ev_dict.keys())[0]
            hydrated.append(_EVENT_LOOKUP[key].from_dict(ev_dict[key]))
        self.events = hydrated


@dataclass
class EffectsBlock(SuiJsonReturnType, DataClassJsonMixin):
    """Effects Block."""

    transaction_effects_digest: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    effects: Effects
    # dependencies: list[str]
    auth_sign_info: AuthSignerInfo = field(metadata=config(letter_case=LetterCase.CAMEL))


@dataclass
class Certificate(SuiJsonReturnType, DataClassJsonMixin):
    """Effects Certification."""

    transaction_digest: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    data: TransactionData
    tx_signature: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    auth_sign_info: AuthSignerInfo = field(metadata=config(letter_case=LetterCase.CAMEL))

    def __post_init__(self):
        """Post init processing."""


@dataclass
class EffectsCertTx(SuiJsonReturnType, DataClassJsonMixin):
    """Effects Certification."""

    certificate: Certificate
    effects: EffectsBlock
    confirmed_local_execution: bool

    def __post_init__(self):
        """Post init processing."""


@dataclass
class TxEffectResult(SuiJsonReturnType, DataClassJsonMixin):
    """Transaction Result."""

    effects_cert: EffectsCertTx = field(metadata=config(field_name="EffectsCert"))

    @property
    def succeeded(self) -> bool:
        """Check if transaction result is successful."""
        return self.effects_cert.effects.effects.status.succeeded

    @property
    def status(self) -> str:
        """Get underlying status string."""
        if self.succeeded:
            return "success"
        return f"{self.effects_cert.effects.effects.status.status} - {self.effects_cert.effects.effects.status.error}"


if __name__ == "__main__":
    # payallsui = {
    #     "EffectsCert": {
    #         "certificate": {
    #             "transactionDigest": "KDPMKrugRySS9mmCG7hFOE+6aBn4x7ik1TFAXKLW63k=",
    #             "data": {
    #                 "transactions": [
    #                     {
    #                         "PayAllSui": {
    #                             "coins": [
    #                                 {
    #                                     "objectId": "0x0301c42860f3474c04725d4feb1ed2c76e07bec1",
    #                                     "version": 1,
    #                                     "digest": "FDXPSUpneKwOWJnjlHvwkpBR5q5am2pGz3hk/REYQgU=",
    #                                 }
    #                             ],
    #                             "recipient": "0xdf590397ea5607f06f9ed1681930c58089b2c75c",
    #                         }
    #                     }
    #                 ],
    #                 "sender": "0x51dd42b2b2a071e1db973ef4fc810cf9860984be",
    #                 "gasPayment": {
    #                     "objectId": "0x0301c42860f3474c04725d4feb1ed2c76e07bec1",
    #                     "version": 1,
    #                     "digest": "FDXPSUpneKwOWJnjlHvwkpBR5q5am2pGz3hk/REYQgU=",
    #                 },
    #                 "gasBudget": 1000,
    #             },
    #             "txSignature": "AXBDwVnwHepg71jxT1suYv05MU3qdTe4tGOHD6/Oqo9cTLhqhi5nXYEosBBVRITqooYxi3gvl8bZNzQCOeeWoGEBAk+cktZ7bXx/uqE02IQdLgD672lPmmGffD3MUxv74O9h",
    #             "authSignInfo": {
    #                 "epoch": 0,
    #                 "signature": "qMK69vr0rLiJbheaJUAOIVeRHL8ABZQBcDWt9bY/vI44E+2tfiClZ4G8b81g0izi",
    #                 "signers_map": [58, 48, 0, 0, 1, 0, 0, 0, 0, 0, 2, 0, 16, 0, 0, 0, 0, 0, 1, 0, 3, 0],
    #             },
    #         },
    #         "effects": {
    #             "transactionEffectsDigest": "119IBq6R0TIa5bWCJhcKQqdOvpFQXczRzZY90TOtq3g=",
    #             "effects": {
    #                 "status": {"status": "success"},
    #                 "gasUsed": {"computationCost": 39, "storageCost": 32, "storageRebate": 32},
    #                 "transactionDigest": "KDPMKrugRySS9mmCG7hFOE+6aBn4x7ik1TFAXKLW63k=",
    #                 "mutated": [
    #                     {
    #                         "owner": {"AddressOwner": "0xdf590397ea5607f06f9ed1681930c58089b2c75c"},
    #                         "reference": {
    #                             "objectId": "0x0301c42860f3474c04725d4feb1ed2c76e07bec1",
    #                             "version": 2,
    #                             "digest": "Yj/fAL9fAFmeyMZpm5Qry8adhtIhmy5CvcPrZ3Shk1U=",
    #                         },
    #                     }
    #                 ],
    #                 "gasObject": {
    #                     "owner": {"AddressOwner": "0xdf590397ea5607f06f9ed1681930c58089b2c75c"},
    #                     "reference": {
    #                         "objectId": "0x0301c42860f3474c04725d4feb1ed2c76e07bec1",
    #                         "version": 2,
    #                         "digest": "Yj/fAL9fAFmeyMZpm5Qry8adhtIhmy5CvcPrZ3Shk1U=",
    #                     },
    #                 },
    #                 "events": [
    #                     {
    #                         "coinBalanceChange": {
    #                             "packageId": "0x0000000000000000000000000000000000000002",
    #                             "transactionModule": "gas",
    #                             "sender": "0x51dd42b2b2a071e1db973ef4fc810cf9860984be",
    #                             "changeType": "Gas",
    #                             "owner": {"AddressOwner": "0x51dd42b2b2a071e1db973ef4fc810cf9860984be"},
    #                             "coinType": "0x2::sui::SUI",
    #                             "coinObjectId": "0x0301c42860f3474c04725d4feb1ed2c76e07bec1",
    #                             "version": 1,
    #                             "amount": -39,
    #                         }
    #                     },
    #                     {
    #                         "coinBalanceChange": {
    #                             "packageId": "0x0000000000000000000000000000000000000002",
    #                             "transactionModule": "pay_all_sui",
    #                             "sender": "0x51dd42b2b2a071e1db973ef4fc810cf9860984be",
    #                             "changeType": "Pay",
    #                             "owner": {"AddressOwner": "0x51dd42b2b2a071e1db973ef4fc810cf9860984be"},
    #                             "coinType": "0x2::sui::SUI",
    #                             "coinObjectId": "0x0301c42860f3474c04725d4feb1ed2c76e07bec1",
    #                             "version": 1,
    #                             "amount": -9999961,
    #                         }
    #                     },
    #                     {
    #                         "coinBalanceChange": {
    #                             "packageId": "0x0000000000000000000000000000000000000002",
    #                             "transactionModule": "pay_all_sui",
    #                             "sender": "0x51dd42b2b2a071e1db973ef4fc810cf9860984be",
    #                             "changeType": "Receive",
    #                             "owner": {"AddressOwner": "0xdf590397ea5607f06f9ed1681930c58089b2c75c"},
    #                             "coinType": "0x2::sui::SUI",
    #                             "coinObjectId": "0x0301c42860f3474c04725d4feb1ed2c76e07bec1",
    #                             "version": 2,
    #                             "amount": 9999961,
    #                         }
    #                     },
    #                 ],
    #                 "dependencies": ["pPZmXkUAhzd2ise73u98bNJUm2j3rVJU2Zn8Io0QDG8="],
    #             },
    #             "authSignInfo": {
    #                 "epoch": 0,
    #                 "signature": "iPyUDMSHfpcSmGgAux6l4zKDuo98hrCGtLye5LKPwhPfGi3mjH6fGfJ4YTWEfHfQ",
    #                 "signers_map": [58, 48, 0, 0, 1, 0, 0, 0, 0, 0, 2, 0, 16, 0, 0, 0, 0, 0, 1, 0, 3, 0],
    #             },
    #         },
    #         "confirmed_local_execution": True,
    #     }
    # }
    # res = TxEffectResult.from_dict(payallsui)
    # print(res.to_json(indent=2))
    # move_call = {
    #     "EffectsCert": {
    #         "certificate": {
    #             "transactionDigest": "96TRiJtau70sjd4Br6jqFhnJ523/yApa1dcV697xPqA=",
    #             "data": {
    #                 "transactions": [
    #                     {
    #                         "Call": {
    #                             "package": {
    #                                 "objectId": "0xf643d513d510fbc1180908fbc565cac9d6317f94",
    #                                 "version": 1,
    #                                 "digest": "BV8jBwVTrftHB62IRvdUCgv6hal3mu/2gnRTuNMDMBk=",
    #                             },
    #                             "module": "base",
    #                             "function": "create_account",
    #                             "arguments": [
    #                                 "0xce476ac5c1a41782ef854bb36d3f011351dbc1ac",
    #                                 "0xddc2a96eedef61abdd1b1d26f1ee9660632b1d98",
    #                                 "0x51dd42b2b2a071e1db973ef4fc810cf9860984be",
    #                             ],
    #                         }
    #                     }
    #                 ],
    #                 "sender": "0xdf590397ea5607f06f9ed1681930c58089b2c75c",
    #                 "gasPayment": {
    #                     "objectId": "0x0301c42860f3474c04725d4feb1ed2c76e07bec1",
    #                     "version": 2,
    #                     "digest": "Yj/fAL9fAFmeyMZpm5Qry8adhtIhmy5CvcPrZ3Shk1U=",
    #                 },
    #                 "gasBudget": 1000,
    #             },
    #             "txSignature": "ADhkiuy0Pcu1PIFb8bPPZ2oQQpwIVsK/3UeWQY2eof8bf+OVVcQBZDx3z2+giPpKSkR1h0xgUIAV+LkGxwFcuQ1tzfSoALPF6JJbe2y4hbgaY9kH7bOpgDyeDi23JflX3A==",
    #             "authSignInfo": {
    #                 "epoch": 0,
    #                 "signature": "mcKAFSIv4rS6wrRhhhfVxj3pjGE/CglBC7AOJWv5BQbwF9Ck06NJ5z8UIhQkZh/u",
    #                 "signers_map": [58, 48, 0, 0, 1, 0, 0, 0, 0, 0, 2, 0, 16, 0, 0, 0, 0, 0, 1, 0, 3, 0],
    #             },
    #         },
    #         "effects": {
    #             "transactionEffectsDigest": "KTGMuCl/38PJP+6WGyUW/THmbmwOoO4Z/KNJ43KUDgk=",
    #             "effects": {
    #                 "status": {"status": "success"},
    #                 "gasUsed": {"computationCost": 101, "storageCost": 44, "storageRebate": 30},
    #                 "transactionDigest": "96TRiJtau70sjd4Br6jqFhnJ523/yApa1dcV697xPqA=",
    #                 "created": [
    #                     {
    #                         "owner": {"AddressOwner": "0x51dd42b2b2a071e1db973ef4fc810cf9860984be"},
    #                         "reference": {
    #                             "objectId": "0xb99a8365033c89967e98740c6962e1d2c0d98c27",
    #                             "version": 1,
    #                             "digest": "+bx9EoLNTgBARFUuqg4Ofcko2wszk5rd4oZzXKn43L0=",
    #                         },
    #                     }
    #                 ],
    #                 "mutated": [
    #                     {
    #                         "owner": {"AddressOwner": "0xdf590397ea5607f06f9ed1681930c58089b2c75c"},
    #                         "reference": {
    #                             "objectId": "0x0301c42860f3474c04725d4feb1ed2c76e07bec1",
    #                             "version": 3,
    #                             "digest": "CZTM0G1or+FR9C63cwIy1m8gIt1IWhShKLjaZWU0Ni4=",
    #                         },
    #                     },
    #                     {
    #                         "owner": {"AddressOwner": "0xdf590397ea5607f06f9ed1681930c58089b2c75c"},
    #                         "reference": {
    #                             "objectId": "0xddc2a96eedef61abdd1b1d26f1ee9660632b1d98",
    #                             "version": 2,
    #                             "digest": "zqt1IJJDEe6rdOtLHPDGy0NfTHjTHDvDRcAK9NXCJOU=",
    #                         },
    #                     },
    #                 ],
    #                 "gasObject": {
    #                     "owner": {"AddressOwner": "0xdf590397ea5607f06f9ed1681930c58089b2c75c"},
    #                     "reference": {
    #                         "objectId": "0x0301c42860f3474c04725d4feb1ed2c76e07bec1",
    #                         "version": 3,
    #                         "digest": "CZTM0G1or+FR9C63cwIy1m8gIt1IWhShKLjaZWU0Ni4=",
    #                     },
    #                 },
    #                 "events": [
    #                     {
    #                         "coinBalanceChange": {
    #                             "packageId": "0x0000000000000000000000000000000000000002",
    #                             "transactionModule": "gas",
    #                             "sender": "0xdf590397ea5607f06f9ed1681930c58089b2c75c",
    #                             "changeType": "Gas",
    #                             "owner": {"AddressOwner": "0xdf590397ea5607f06f9ed1681930c58089b2c75c"},
    #                             "coinType": "0x2::sui::SUI",
    #                             "coinObjectId": "0x0301c42860f3474c04725d4feb1ed2c76e07bec1",
    #                             "version": 2,
    #                             "amount": -115,
    #                         }
    #                     },
    #                     {
    #                         "newObject": {
    #                             "packageId": "0xf643d513d510fbc1180908fbc565cac9d6317f94",
    #                             "transactionModule": "base",
    #                             "sender": "0xdf590397ea5607f06f9ed1681930c58089b2c75c",
    #                             "recipient": {"AddressOwner": "0x51dd42b2b2a071e1db973ef4fc810cf9860984be"},
    #                             "objectType": "0xf643d513d510fbc1180908fbc565cac9d6317f94::base::Tracker",
    #                             "objectId": "0xb99a8365033c89967e98740c6962e1d2c0d98c27",
    #                             "version": 1,
    #                         }
    #                     },
    #                     {
    #                         "mutateObject": {
    #                             "packageId": "0xf643d513d510fbc1180908fbc565cac9d6317f94",
    #                             "transactionModule": "base",
    #                             "sender": "0xdf590397ea5607f06f9ed1681930c58089b2c75c",
    #                             "objectType": "0xf643d513d510fbc1180908fbc565cac9d6317f94::base::ServiceTracker",
    #                             "objectId": "0xddc2a96eedef61abdd1b1d26f1ee9660632b1d98",
    #                             "version": 2,
    #                         }
    #                     },
    #                 ],
    #                 "dependencies": [
    #                     "KDPMKrugRySS9mmCG7hFOE+6aBn4x7ik1TFAXKLW63k=",
    #                     "YPCeujtaIjLSs0UOwOMebmEPZYD8Nm50jcz2kvYmKnY=",
    #                 ],
    #             },
    #             "authSignInfo": {
    #                 "epoch": 0,
    #                 "signature": "mR3tuFW4orsh2Qe086LuEn+chn7kqq/pj3HhW6rGFCTQzmXjAZT4mYKHiIyseWPD",
    #                 "signers_map": [58, 48, 0, 0, 1, 0, 0, 0, 0, 0, 2, 0, 16, 0, 0, 0, 0, 0, 1, 0, 3, 0],
    #             },
    #         },
    #         "confirmed_local_execution": True,
    #     }
    # }
    # res = TxEffectResult.from_dict(move_call)
    # print(res.to_json(indent=2))
    # publish = {
    #     "EffectsCert": {
    #         "certificate": {
    #             "transactionDigest": "27fzjNcwu+gb/9jTpl0UouPhypp8+7Am2wvVq3tijPU=",
    #             "data": {
    #                 "transactions": [
    #                     {
    #                         "Publish": {
    #                             "disassembled": {
    #                                 "lest": "// Move bytecode v6\nmodule 0.lest {\n\n\n\n}",
    #                                 "nest": "// Move bytecode v6\nmodule 0.nest {\nstruct Child0 has store, key {\n\tid: UID,\n\tval: u64\n}\nstruct Child1 has store, key {\n\tid: UID,\n\tval: u64\n}\nstruct Parent0 has key {\n\tid: UID,\n\tchild: Child0\n}\nstruct Parent1 has key {\n\tid: UID,\n\tchild: Option<Child1>\n}\n\nentry public create_data(Arg0: &mut TxContext) {\nL0:\tloc1: Child1\nL1:\tloc2: Parent0\nL2:\tloc3: Parent1\nB0:\n\t0: CopyLoc[0](Arg0: &mut TxContext)\n\t1: Call[1](new(&mut TxContext): UID)\n\t2: LdU64(20)\n\t3: Pack[0](Child0)\n\t4: StLoc[1](loc0: Child0)\n\t5: CopyLoc[0](Arg0: &mut TxContext)\n\t6: Call[1](new(&mut TxContext): UID)\n\t7: MoveLoc[1](loc0: Child0)\n\t8: Pack[2](Parent0)\n\t9: StLoc[3](loc2: Parent0)\n\t10: MoveLoc[3](loc2: Parent0)\n\t11: CopyLoc[0](Arg0: &mut TxContext)\n\t12: FreezeRef\n\t13: Call[2](sender(&TxContext): address)\n\t14: Call[0](transfer<Parent0>(Parent0, address))\n\t15: CopyLoc[0](Arg0: &mut TxContext)\n\t16: Call[1](new(&mut TxContext): UID)\n\t17: LdU64(20)\n\t18: Pack[1](Child1)\n\t19: StLoc[2](loc1: Child1)\n\t20: CopyLoc[0](Arg0: &mut TxContext)\n\t21: Call[1](new(&mut TxContext): UID)\n\t22: Call[1](none<Child1>(): Option<Child1>)\n\t23: Pack[3](Parent1)\n\t24: StLoc[4](loc3: Parent1)\n\t25: MutBorrowLoc[4](loc3: Parent1)\n\t26: MutBorrowField[0](Parent1.child: Option<Child1>)\n\t27: MoveLoc[2](loc1: Child1)\n\t28: Call[2](fill<Child1>(&mut Option<Child1>, Child1))\n\t29: MoveLoc[4](loc3: Parent1)\n\t30: MoveLoc[0](Arg0: &mut TxContext)\n\t31: FreezeRef\n\t32: Call[2](sender(&TxContext): address)\n\t33: Call[3](transfer<Parent1>(Parent1, address))\n\t34: Ret\n}\n}",
    #                             }
    #                         }
    #                     }
    #                 ],
    #                 "sender": "0xdf590397ea5607f06f9ed1681930c58089b2c75c",
    #                 "gasPayment": {
    #                     "objectId": "0x7ad543034bae37fb3a9f7355fd6813e85d2abfb4",
    #                     "version": 1,
    #                     "digest": "BdmN4SNowcGxdsoglt1QtBOI5v6cZkZL9BrWZtHkjvY=",
    #                 },
    #                 "gasBudget": 3000,
    #             },
    #             "txSignature": "AJlX+9pMqVIVK6Kfinyt/VBovgJ6F2+XGLxRmeKccDJdfKBxVJiz6QNGpX/pFl+8kHjg0R0xo3BnTPZvT/FZAg1tzfSoALPF6JJbe2y4hbgaY9kH7bOpgDyeDi23JflX3A==",
    #             "authSignInfo": {
    #                 "epoch": 0,
    #                 "signature": "lOraH4NOSafXbscWUnUKt6gPGO4Dyw4BLhpmEWg5I5hd5lMYrmImpYlQQIvAjkZK",
    #                 "signers_map": [58, 48, 0, 0, 1, 0, 0, 0, 0, 0, 2, 0, 16, 0, 0, 0, 0, 0, 1, 0, 3, 0],
    #             },
    #         },
    #         "effects": {
    #             "transactionEffectsDigest": "juw9YhdTWjj+o7F9XJLpkD/GBvogzR+g5GrdsKuQvA8=",
    #             "effects": {
    #                 "status": {"status": "success"},
    #                 "gasUsed": {"computationCost": 786, "storageCost": 81, "storageRebate": 16},
    #                 "transactionDigest": "27fzjNcwu+gb/9jTpl0UouPhypp8+7Am2wvVq3tijPU=",
    #                 "created": [
    #                     {
    #                         "owner": "Immutable",
    #                         "reference": {
    #                             "objectId": "0x5a3a05a071b2186b1964e25d9e2b1e089dc3e467",
    #                             "version": 1,
    #                             "digest": "I0SLOOVeY8Nrw1jYBk9IvS2Thp+8hzuVF6hbj1sbsmY=",
    #                         },
    #                     }
    #                 ],
    #                 "mutated": [
    #                     {
    #                         "owner": {"AddressOwner": "0xdf590397ea5607f06f9ed1681930c58089b2c75c"},
    #                         "reference": {
    #                             "objectId": "0x7ad543034bae37fb3a9f7355fd6813e85d2abfb4",
    #                             "version": 2,
    #                             "digest": "O0ZW8JpmHhQ+3d24hQI+w/GIAsXzzrPki3GXY7PyLfA=",
    #                         },
    #                     }
    #                 ],
    #                 "gasObject": {
    #                     "owner": {"AddressOwner": "0xdf590397ea5607f06f9ed1681930c58089b2c75c"},
    #                     "reference": {
    #                         "objectId": "0x7ad543034bae37fb3a9f7355fd6813e85d2abfb4",
    #                         "version": 2,
    #                         "digest": "O0ZW8JpmHhQ+3d24hQI+w/GIAsXzzrPki3GXY7PyLfA=",
    #                     },
    #                 },
    #                 "events": [
    #                     {
    #                         "coinBalanceChange": {
    #                             "packageId": "0x0000000000000000000000000000000000000002",
    #                             "transactionModule": "gas",
    #                             "sender": "0xdf590397ea5607f06f9ed1681930c58089b2c75c",
    #                             "changeType": "Gas",
    #                             "owner": {"AddressOwner": "0xdf590397ea5607f06f9ed1681930c58089b2c75c"},
    #                             "coinType": "0x2::sui::SUI",
    #                             "coinObjectId": "0x7ad543034bae37fb3a9f7355fd6813e85d2abfb4",
    #                             "version": 1,
    #                             "amount": -851,
    #                         }
    #                     },
    #                     {
    #                         "publish": {
    #                             "sender": "0xdf590397ea5607f06f9ed1681930c58089b2c75c",
    #                             "packageId": "0x5a3a05a071b2186b1964e25d9e2b1e089dc3e467",
    #                         }
    #                     },
    #                 ],
    #                 "dependencies": ["HWt/c03S4ETqdHr+ogws33FzVD3I7GyffGtBUZ644Lw="],
    #             },
    #             "authSignInfo": {
    #                 "epoch": 0,
    #                 "signature": "l8AwwOwBOjj3TWIiHtKavGSVn37tugrWBoIwQFyWbGVQTY3oATANRa5AUd862c+E",
    #                 "signers_map": [58, 48, 0, 0, 1, 0, 0, 0, 0, 0, 2, 0, 16, 0, 0, 0, 0, 0, 1, 0, 3, 0],
    #             },
    #         },
    #         "confirmed_local_execution": True,
    #     }
    # }
    # res = TxEffectResult.from_dict(publish)
    # print(f"Transactionn succeeded: {res.succeeded}")
    publish2 = {
        "EffectsCert": {
            "certificate": {
                "transactionDigest": "O7pVowmS279mJ0MotRwmU3JQA0ZE80raxOH9RcGb6Z0=",
                "data": {
                    "transactions": [
                        {
                            "Publish": {
                                "disassembled": {
                                    "base": "// Move bytecode v6\nmodule 0.base {\nstruct Service has key {\n\tid: UID,\n\tadmin: address\n}\nstruct ServiceTracker has key {\n\tid: UID,\n\tinitialized: bool,\n\tcount_accounts: u64\n}\nstruct Tracker has store, key {\n\tid: UID,\n\tinitialized: bool,\n\towner: address,\n\taccumulator: vector<u8>\n}\n\npublic accounts_created(Arg0: &ServiceTracker): u64 {\nB0:\n\t0: MoveLoc[0](Arg0: &ServiceTracker)\n\t1: ImmBorrowField[0](ServiceTracker.count_accounts: u64)\n\t2: ReadRef\n\t3: Ret\n}\npublic add_from(Arg0: &mut Tracker, Arg1: vector<u8>) {\nB0:\n\t0: MoveLoc[0](Arg0: &mut Tracker)\n\t1: MutBorrowField[1](Tracker.accumulator: vector<u8>)\n\t2: MoveLoc[1](Arg1: vector<u8>)\n\t3: Call[0](append<u8>(&mut vector<u8>, vector<u8>))\n\t4: Ret\n}\npublic add_to_store(Arg0: &mut Tracker, Arg1: u8): u64 {\nB0:\n\t0: CopyLoc[0](Arg0: &mut Tracker)\n\t1: MutBorrowField[1](Tracker.accumulator: vector<u8>)\n\t2: MoveLoc[1](Arg1: u8)\n\t3: VecPushBack(8)\n\t4: MoveLoc[0](Arg0: &mut Tracker)\n\t5: FreezeRef\n\t6: Call[14](stored_count(&Tracker): u64)\n\t7: Ret\n}\nentry public add_value(Arg0: &mut Tracker, Arg1: u8, Arg2: &mut TxContext) {\nB0:\n\t0: MoveLoc[2](Arg2: &mut TxContext)\n\t1: FreezeRef\n\t2: Call[17](sender(&TxContext): address)\n\t3: StLoc[5](loc2: address)\n\t4: CopyLoc[0](Arg0: &mut Tracker)\n\t5: MoveLoc[5](loc2: address)\n\t6: StLoc[4](loc1: address)\n\t7: StLoc[3](loc0: &mut Tracker)\n\t8: MoveLoc[3](loc0: &mut Tracker)\n\t9: FreezeRef\n\t10: MoveLoc[4](loc1: address)\n\t11: Call[10](is_owned_by(&Tracker, address): bool)\n\t12: BrTrue(17)\nB1:\n\t13: MoveLoc[0](Arg0: &mut Tracker)\n\t14: Pop\n\t15: LdConst[2](U64: [1, 0, 0, 0, 0, 0, 0, 0])\n\t16: Abort\nB2:\n\t17: MoveLoc[0](Arg0: &mut Tracker)\n\t18: MoveLoc[1](Arg1: u8)\n\t19: Call[2](add_to_store(&mut Tracker, u8): u64)\n\t20: Pop\n\t21: Ret\n}\nentry public add_values(Arg0: &mut Tracker, Arg1: vector<u8>, Arg2: &mut TxContext) {\nB0:\n\t0: MoveLoc[2](Arg2: &mut TxContext)\n\t1: FreezeRef\n\t2: Call[17](sender(&TxContext): address)\n\t3: StLoc[5](loc2: address)\n\t4: CopyLoc[0](Arg0: &mut Tracker)\n\t5: MoveLoc[5](loc2: address)\n\t6: StLoc[4](loc1: address)\n\t7: StLoc[3](loc0: &mut Tracker)\n\t8: MoveLoc[3](loc0: &mut Tracker)\n\t9: FreezeRef\n\t10: MoveLoc[4](loc1: address)\n\t11: Call[10](is_owned_by(&Tracker, address): bool)\n\t12: BrTrue(17)\nB1:\n\t13: MoveLoc[0](Arg0: &mut Tracker)\n\t14: Pop\n\t15: LdConst[2](U64: [1, 0, 0, 0, 0, 0, 0, 0])\n\t16: Abort\nB2:\n\t17: MoveLoc[0](Arg0: &mut Tracker)\n\t18: MoveLoc[1](Arg1: vector<u8>)\n\t19: Call[1](add_from(&mut Tracker, vector<u8>))\n\t20: Ret\n}\nentry public create_account(Arg0: &Service, Arg1: &mut ServiceTracker, Arg2: address, Arg3: &mut TxContext) {\nB0:\n\t0: CopyLoc[3](Arg3: &mut TxContext)\n\t1: FreezeRef\n\t2: Call[17](sender(&TxContext): address)\n\t3: StLoc[4](loc0: address)\n\t4: MoveLoc[0](Arg0: &Service)\n\t5: MoveLoc[4](loc0: address)\n\t6: Call[11](is_owner(&Service, address): bool)\n\t7: BrTrue(14)\nB1:\n\t8: MoveLoc[1](Arg1: &mut ServiceTracker)\n\t9: Pop\n\t10: MoveLoc[3](Arg3: &mut TxContext)\n\t11: Pop\n\t12: LdConst[1](U64: [0, 0, 0, 0, 0, 0, 0, 0])\n\t13: Abort\nB2:\n\t14: MoveLoc[1](Arg1: &mut ServiceTracker)\n\t15: Call[8](increase_account(&mut ServiceTracker))\n\t16: MoveLoc[3](Arg3: &mut TxContext)\n\t17: Call[18](new(&mut TxContext): UID)\n\t18: LdTrue\n\t19: CopyLoc[2](Arg2: address)\n\t20: LdConst[4](Vector(U8): [0])\n\t21: Pack[2](Tracker)\n\t22: MoveLoc[2](Arg2: address)\n\t23: Call[1](transfer<Tracker>(Tracker, address))\n\t24: Ret\n}\npublic drop_from_store(Arg0: &mut Tracker, Arg1: u8): u8 {\nB0:\n\t0: CopyLoc[0](Arg0: &mut Tracker)\n\t1: ImmBorrowField[1](Tracker.accumulator: vector<u8>)\n\t2: ImmBorrowLoc[1](Arg1: u8)\n\t3: Call[2](index_of<u8>(&vector<u8>, &u8): bool * u64)\n\t4: StLoc[3](loc1: u64)\n\t5: StLoc[2](loc0: bool)\n\t6: MoveLoc[2](loc0: bool)\n\t7: BrTrue(12)\nB1:\n\t8: MoveLoc[0](Arg0: &mut Tracker)\n\t9: Pop\n\t10: LdConst[0](U64: [2, 0, 0, 0, 0, 0, 0, 0])\n\t11: Abort\nB2:\n\t12: MoveLoc[0](Arg0: &mut Tracker)\n\t13: MutBorrowField[1](Tracker.accumulator: vector<u8>)\n\t14: MoveLoc[3](loc1: u64)\n\t15: Call[3](remove<u8>(&mut vector<u8>, u64): u8)\n\t16: Ret\n}\npublic has_value(Arg0: &Tracker, Arg1: u8): bool {\nB0:\n\t0: MoveLoc[0](Arg0: &Tracker)\n\t1: ImmBorrowField[1](Tracker.accumulator: vector<u8>)\n\t2: ImmBorrowLoc[1](Arg1: u8)\n\t3: Call[4](contains<u8>(&vector<u8>, &u8): bool)\n\t4: Ret\n}\nincrease_account(Arg0: &mut ServiceTracker) {\nB0:\n\t0: CopyLoc[0](Arg0: &mut ServiceTracker)\n\t1: ImmBorrowField[0](ServiceTracker.count_accounts: u64)\n\t2: ReadRef\n\t3: LdU64(1)\n\t4: Add\n\t5: MoveLoc[0](Arg0: &mut ServiceTracker)\n\t6: MutBorrowField[0](ServiceTracker.count_accounts: u64)\n\t7: WriteRef\n\t8: Ret\n}\ninit(Arg0: &mut TxContext) {\nL0:\tloc1: address\nB0:\n\t0: CopyLoc[0](Arg0: &mut TxContext)\n\t1: FreezeRef\n\t2: Call[17](sender(&TxContext): address)\n\t3: StLoc[2](loc1: address)\n\t4: CopyLoc[0](Arg0: &mut TxContext)\n\t5: Call[18](new(&mut TxContext): UID)\n\t6: StLoc[1](loc0: UID)\n\t7: MoveLoc[1](loc0: UID)\n\t8: MoveLoc[2](loc1: address)\n\t9: Pack[0](Service)\n\t10: Call[5](freeze_object<Service>(Service))\n\t11: CopyLoc[0](Arg0: &mut TxContext)\n\t12: Call[18](new(&mut TxContext): UID)\n\t13: LdTrue\n\t14: LdU64(0)\n\t15: Pack[1](ServiceTracker)\n\t16: MoveLoc[0](Arg0: &mut TxContext)\n\t17: FreezeRef\n\t18: Call[17](sender(&TxContext): address)\n\t19: Call[6](transfer<ServiceTracker>(ServiceTracker, address))\n\t20: Ret\n}\nis_owned_by(Arg0: &Tracker, Arg1: address): bool {\nB0:\n\t0: MoveLoc[0](Arg0: &Tracker)\n\t1: ImmBorrowField[2](Tracker.owner: address)\n\t2: ReadRef\n\t3: MoveLoc[1](Arg1: address)\n\t4: Eq\n\t5: Ret\n}\nis_owner(Arg0: &Service, Arg1: address): bool {\nB0:\n\t0: MoveLoc[0](Arg0: &Service)\n\t1: ImmBorrowField[3](Service.admin: address)\n\t2: ReadRef\n\t3: MoveLoc[1](Arg1: address)\n\t4: Eq\n\t5: Ret\n}\nentry public remove_value(Arg0: &mut Tracker, Arg1: u8, Arg2: &mut TxContext) {\nB0:\n\t0: MoveLoc[2](Arg2: &mut TxContext)\n\t1: FreezeRef\n\t2: Call[17](sender(&TxContext): address)\n\t3: StLoc[5](loc2: address)\n\t4: CopyLoc[0](Arg0: &mut Tracker)\n\t5: MoveLoc[5](loc2: address)\n\t6: StLoc[4](loc1: address)\n\t7: StLoc[3](loc0: &mut Tracker)\n\t8: MoveLoc[3](loc0: &mut Tracker)\n\t9: FreezeRef\n\t10: MoveLoc[4](loc1: address)\n\t11: Call[10](is_owned_by(&Tracker, address): bool)\n\t12: BrTrue(17)\nB1:\n\t13: MoveLoc[0](Arg0: &mut Tracker)\n\t14: Pop\n\t15: LdConst[2](U64: [1, 0, 0, 0, 0, 0, 0, 0])\n\t16: Abort\nB2:\n\t17: MoveLoc[0](Arg0: &mut Tracker)\n\t18: CopyLoc[1](Arg1: u8)\n\t19: Call[6](drop_from_store(&mut Tracker, u8): u8)\n\t20: MoveLoc[1](Arg1: u8)\n\t21: Eq\n\t22: BrTrue(25)\nB3:\n\t23: LdConst[3](U64: [3, 0, 0, 0, 0, 0, 0, 0])\n\t24: Abort\nB4:\n\t25: Ret\n}\nset_tracker_owner(Arg0: &mut Tracker, Arg1: address) {\nB0:\n\t0: MoveLoc[1](Arg1: address)\n\t1: MoveLoc[0](Arg0: &mut Tracker)\n\t2: MutBorrowField[2](Tracker.owner: address)\n\t3: WriteRef\n\t4: Ret\n}\npublic stored_count(Arg0: &Tracker): u64 {\nB0:\n\t0: MoveLoc[0](Arg0: &Tracker)\n\t1: ImmBorrowField[1](Tracker.accumulator: vector<u8>)\n\t2: VecLen(8)\n\t3: Ret\n}\npublic transfer(Arg0: Tracker, Arg1: address) {\nB0:\n\t0: MoveLoc[0](Arg0: Tracker)\n\t1: MoveLoc[1](Arg1: address)\n\t2: Call[1](transfer<Tracker>(Tracker, address))\n\t3: Ret\n}\n}"
                                }
                            }
                        }
                    ],
                    "sender": "0xed028a162354c4ec1e4557f84721ee57b890de88",
                    "gasPayment": {
                        "objectId": "0x3b5cd4647536750b4fe994b051b2401bc0a9c83b",
                        "version": 3,
                        "digest": "mxPTk0j3vUuGvu2OQ8Y4/XKG9S1wsl7yWScPyI7T+m8=",
                    },
                    "gasBudget": 3000,
                },
                "txSignature": "AB/uUb3aHfyPGPu1IJuFcd3o6RAwgz5N6ynNLaP/YCicywUIm/2Gd2j7DJ5b/xr2NgnZWrbCCg0y4cPep0ax4AkXtXnZ0PADMCi5gTAGuPQpWJpKoF89md3x8ze4c8Er0Q==",
                "authSignInfo": {
                    "epoch": 0,
                    "signature": "uKLm+uevBym6qixlbcHnNv5Zb3X6cihXg9XsfHy38I/ZTvl/GuABuGEFNqkWVzI+",
                    "signers_map": [58, 48, 0, 0, 1, 0, 0, 0, 0, 0, 2, 0, 16, 0, 0, 0, 0, 0, 1, 0, 2, 0],
                },
            },
            "effects": {
                "transactionEffectsDigest": "69u+dMkwLqT4H2TPc5oWiuWODNKCs3HstA9kfVmzqQA=",
                "effects": {
                    "status": {"status": "success"},
                    "gasUsed": {"computationCost": 936, "storageCost": 185, "storageRebate": 16},
                    "transactionDigest": "O7pVowmS279mJ0MotRwmU3JQA0ZE80raxOH9RcGb6Z0=",
                    "created": [
                        {
                            "owner": "Immutable",
                            "reference": {
                                "objectId": "0x00831d53483ab5509db70802c3a463bfb8d6a122",
                                "version": 1,
                                "digest": "GOcCaX6ENLTbJa1B7d38w1kCoiry5NZStuzg9u3IZGM=",
                            },
                        },
                        {
                            "owner": "Immutable",
                            "reference": {
                                "objectId": "0x2939f95970411adc160ca4f4ddd57414cc34caf0",
                                "version": 1,
                                "digest": "O1GD6MQRe+H+xONa7PGEpdSgj6IIt5W5puj8kJCOM30=",
                            },
                        },
                        {
                            "owner": {"AddressOwner": "0xed028a162354c4ec1e4557f84721ee57b890de88"},
                            "reference": {
                                "objectId": "0x503515d35d5c8a8e851f6236c78eccefb3828286",
                                "version": 1,
                                "digest": "BGhPyWiYhtaWgyrl6OEat28QvbXKqUp0vdSQBOb5wpg=",
                            },
                        },
                    ],
                    "mutated": [
                        {
                            "owner": {"AddressOwner": "0xed028a162354c4ec1e4557f84721ee57b890de88"},
                            "reference": {
                                "objectId": "0x3b5cd4647536750b4fe994b051b2401bc0a9c83b",
                                "version": 4,
                                "digest": "FNP36j5qo5TnAx6OLGKGis27aBJ/1Nui1NKm0Sega9w=",
                            },
                        }
                    ],
                    "gasObject": {
                        "owner": {"AddressOwner": "0xed028a162354c4ec1e4557f84721ee57b890de88"},
                        "reference": {
                            "objectId": "0x3b5cd4647536750b4fe994b051b2401bc0a9c83b",
                            "version": 4,
                            "digest": "FNP36j5qo5TnAx6OLGKGis27aBJ/1Nui1NKm0Sega9w=",
                        },
                    },
                    "events": [
                        {
                            "coinBalanceChange": {
                                "packageId": "0x0000000000000000000000000000000000000002",
                                "transactionModule": "gas",
                                "sender": "0xed028a162354c4ec1e4557f84721ee57b890de88",
                                "changeType": "Gas",
                                "owner": {"AddressOwner": "0xed028a162354c4ec1e4557f84721ee57b890de88"},
                                "coinType": "0x2::sui::SUI",
                                "coinObjectId": "0x3b5cd4647536750b4fe994b051b2401bc0a9c83b",
                                "version": 3,
                                "amount": -1105,
                            }
                        },
                        {
                            "newObject": {
                                "packageId": "0x2939f95970411adc160ca4f4ddd57414cc34caf0",
                                "transactionModule": "base",
                                "sender": "0xed028a162354c4ec1e4557f84721ee57b890de88",
                                "recipient": "Immutable",
                                "objectType": "0x2939f95970411adc160ca4f4ddd57414cc34caf0::base::Service",
                                "objectId": "0x00831d53483ab5509db70802c3a463bfb8d6a122",
                                "version": 1,
                            }
                        },
                        {
                            "publish": {
                                "sender": "0xed028a162354c4ec1e4557f84721ee57b890de88",
                                "packageId": "0x2939f95970411adc160ca4f4ddd57414cc34caf0",
                            }
                        },
                        {
                            "newObject": {
                                "packageId": "0x2939f95970411adc160ca4f4ddd57414cc34caf0",
                                "transactionModule": "base",
                                "sender": "0xed028a162354c4ec1e4557f84721ee57b890de88",
                                "recipient": {"AddressOwner": "0xed028a162354c4ec1e4557f84721ee57b890de88"},
                                "objectType": "0x2939f95970411adc160ca4f4ddd57414cc34caf0::base::ServiceTracker",
                                "objectId": "0x503515d35d5c8a8e851f6236c78eccefb3828286",
                                "version": 1,
                            }
                        },
                    ],
                    "dependencies": ["Lm1JtRCWUO+4BtpzqwlL0SG5o6w+s2B4MtYvd5RmFPY="],
                },
                "authSignInfo": {
                    "epoch": 0,
                    "signature": "swlNpgO1bvAYPimCEssUfQqDa5l+EPt3dYoFXByI9YHF6KN+2984mjTY1bhM+ptd",
                    "signers_map": [58, 48, 0, 0, 1, 0, 0, 0, 0, 0, 2, 0, 16, 0, 0, 0, 0, 0, 1, 0, 2, 0],
                },
            },
            "confirmed_local_execution": True,
        }
    }
    res = TxEffectResult.from_dict(publish2)
    print(f"Transactionn succeeded: {res.succeeded}")
