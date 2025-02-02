#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sui TransactionEffects BCS Type."""

import canoser as can
import pysui.sui.sui_types.bcs as bcs


class OptionalString(can.RustOptional):
    _type = can.StrT


class OptionalDigest(can.RustOptional):
    _type = bcs.Digest


class ModuleId(can.Struct):
    _fields = [
        ("address", bcs.Address),
        ("name", can.StrT),
    ]


class MoveLocation(can.Struct):
    _fields = [
        ("module", ModuleId),
        ("function", bcs.U16),
        ("instruction", bcs.U16),
        ("functionName", OptionalString),
    ]


class CommandArgumentError(can.RustEnum):
    _enums = [
        ("TypeMismatch", None),
        ("InvalidBCSBytes", None),
        ("InvalidUsageOfPureArg", None),
        ("InvalidArgumentToPrivateEntryFunction", None),
        ("IndexOutOfBounds", bcs.U16),
        ("SecondaryIndexOutOfBounds", (bcs.U16, bcs.U16)),
        ("InvalidResultArity", bcs.U16),
        ("InvalidGasCoinUsage", None),
        ("InvalidValueUsage", None),
        ("InvalidObjectByValue", None),
        ("InvalidObjectByMutRef", None),
        ("SharedObjectOperationNotAllowed", None),
    ]


class TypeArgumentError(can.RustEnum):
    _enums = [
        ("TypeNotFound", None),
        ("ConstraintNotSatisfied", None),
    ]


class PackageUpgradeError(can.RustEnum):
    _enums = [
        ("UnableToFetchPackage", bcs.Address),
        ("NotAPackage", bcs.Address),
        ("IncompatibleUpgrade", None),
        ("DigestDoesNotMatch", bcs.Digest),
        ("UnknownUpgradePolicy", bcs.U8),
        ("PackageIDDoesNotMatch", (bcs.Address, bcs.Address)),
    ]


class ExecutionFailureStatus(can.RustEnum):
    _enums = [
        ("InsufficientGas", None),
        ("InvalidGasObject", None),
        ("InvariantViolation", None),
        ("FeatureNotYetSupported", None),
        ("MoveObjectTooBig", (bcs.U64, bcs.U64)),
        ("MovePackageTooBig", (bcs.U64, bcs.U64)),
        ("CircularObjectOwnership", bcs.Address),
        ("InsufficientCoinBalance", None),
        ("CoinBalanceOverflow", None),
        ("PublishErrorNonZeroAddress", None),
        ("SuiMoveVerificationError", None),
        ("MovePrimitiveRuntimeError", MoveLocation),
        ("MoveAbort", (MoveLocation, bcs.U64)),
        ("VMVerificationOrDeserializationError", None),
        ("VMInvariantViolation", None),
        ("FunctionNotFound", None),
        ("ArityMismatch", None),
        ("TypeArityMismatch", None),
        ("NonEntryFunctionInvoked", None),
        ("CommandArgumentError", (bcs.U16, CommandArgumentError)),
        ("TypeArgumentError", (bcs.U16, TypeArgumentError)),
        ("UnusedValueWithoutDrop", (bcs.U16, bcs.U16)),
        ("InvalidPublicFunctionReturnType", bcs.U16),
        ("InvalidTransferObject", None),
        ("EffectsTooLarge", (bcs.U64, bcs.U64)),
        ("PublishUpgradeMissingDependency", None),
        ("PublishUpgradeDependencyDowngrade", None),
        ("PackageUpgradeError", PackageUpgradeError),
        ("WrittenObjectsTooLarge", (bcs.U64, bcs.U64)),
        ("CertificateDenied", None),
        ("SuiMoveVerificationTimedout", None),
        ("SharedObjectOperationNotAllowed", None),
        ("InputObjectDeleted", None),
        ("ExecutionCancelledDueToSharedObjectCongestion", bcs.Address),
        ("AddressDeniedForCoin", (bcs.Address, can.StrT)),
        ("CoinTypeGlobalPause", can.StrT),
        ("ExecutionCancelledDueToRandomnessUnavailable", None),
    ]


class ExecutionStatus(can.RustEnum):
    _enums = [
        ("Success", None),
        ("Failed", (ExecutionFailureStatus, bcs.OptionalU64)),
    ]


class GasCostSummary(can.Struct):
    _fields = [
        ("computationCost", bcs.U64),
        ("storageCost", bcs.U64),
        ("storageRebate", bcs.U64),
        ("nonRefundableStorageFee", bcs.U64),
    ]


class Owner(can.RustEnum):
    _enums = [
        ("AddressOwner", bcs.Address),
        ("ObjectOwner", bcs.Address),
        ("SharedInitialVersion", bcs.U64),
        ("Immutable", None),
    ]


class TransactionEffectsV1(can.Struct):
    _fields = [
        ("status", ExecutionStatus),
        ("executedEpoch", bcs.U64),
        ("gasUsed", GasCostSummary),
        (
            "modifiedAtVersions",
            [("ObjectAddress", bcs.Address), ("ObjectVersion", bcs.U64)],
        ),
        ("sharedObjects", bcs.SharedObjectReference),
        ("transactionDigest", bcs.Digest),
        ("created", [(bcs.ObjectReference, Owner)]),
        ("mutated", [(bcs.ObjectReference, Owner)]),
        ("unwrapped", [(bcs.ObjectReference, Owner)]),
        ("deleted", [bcs.ObjectReference]),
        ("unwrappedDeleted", [bcs.ObjectReference]),
        ("wrapped", [bcs.ObjectReference]),
        ("gasObject", [(bcs.ObjectReference, Owner)]),
        ("eventsDigest", OptionalDigest),
        ("dependencies", [bcs.Digest]),
    ]


class VersionDigest(can.Struct):
    _fields = [
        ("version", bcs.U64),
        ("object", bcs.Digest),
    ]


class ObjectIn(can.RustEnum):
    _enums = [
        ("NotExist", None),
        ("Exists", (VersionDigest, Owner)),
    ]


class ObjectOut(can.RustEnum):
    _enums = [
        ("NotExist", None),
        ("ObjectWrite", (bcs.Digest, Owner)),
        ("PackageWrite", VersionDigest),
    ]


class IDOperation(can.RustEnum):
    _enums = [
        ("None", None),
        ("Created", None),
        ("Deleted", None),
    ]


class EffectsObjectChange(can.Struct):
    _fields = [
        ("inputState", ObjectIn),
        ("outputState", ObjectOut),
        ("idOperation", IDOperation),
    ]


class UnchangedShareKind(can.RustEnum):
    _enums = [
        ("ReadOnlyRoot", VersionDigest),
        ("MutableDeleted", bcs.U64),
        ("ReadDeleted", bcs.U64),
        ("Cancelled", bcs.U64),
        ("PerEpochConfig", None),
    ]


class TransactionEffectsV2(can.Struct):
    _fields = [
        ("status", ExecutionStatus),
        ("executedEpoch", bcs.U64),
        ("gasUsed", GasCostSummary),
        ("transactionDigest", bcs.Digest),
        ("gasObjectIndex", bcs.OptionalU32),
        ("eventDigest", OptionalDigest),
        ("dependencies", [bcs.Digest]),
        ("lamportVersion", bcs.U64),
        ("changedObjects", [(bcs.Address, EffectsObjectChange)]),
        ("unchangedSharedObjects", [(bcs.Address, UnchangedShareKind)]),
        ("auxDataDigest", OptionalDigest),
    ]


class TransactionEffects(can.RustEnum):
    _enums = [
        ("V1", TransactionEffectsV1),
        ("V2", TransactionEffectsV2),
    ]


if __name__ == "__main__":
    """."""
    import base64

    bcs = "AQByAAAAAAAAAEBCDwAAAAAAkJgXAQAAAADI7A4AAAAAAJgmAAAAAAAAIGumr1zYfIzEy6DwayTg2OOwsITm32cqH/BiCxNWy00/AQAAAAAAAiAhgX1CvwmrGbXuox6ZTSWMKN50XLEmHAoPWe8JRo2nMiDxlQRTv9yuritx6h9V3Lm/CdKbQXd9BU3Zryvs6HQT4XMAAAAAAAAABBQHztnMcSfWQquveJ8LgcWlGYMjZ/vWQb/i5PyNSLPDAXIAAAAAAAAAIOWd8XofHxGYSoN7FzAbEtTaaa9q6hlo/qmZaF24NaO4AKni2zhfBVzAIVo83iaLdicFNblEOAdRTxg76Gkmwhn0ASBvizHWJscsfpg8vXOTvgCvWmAbxFjXZid7lWY03PNfOQCp4ts4XwVcwCFaPN4mi3YnBTW5RDgHUU8YO+hpJsIZ9AAsYu63La/k1DLlOazaWqcYMESEWKwe+hsde2kApNTnRQACAQAAAAAAAAAgs7ZyN4Y+hZK0RMSQ7fPymerGY3VL9oPIxINKG9h+ZUwBNl1Z+JlMbRjGgqnO3kjP2TE7ctT53gKVKeOIiYETIxsAASCALuwi/OuVafChgxZ+gikNA3NQQH4bccPK39ELSEaQEgCp4ts4XwVcwCFaPN4mi3YnBTW5RDgHUU8YO+hpJsIZ9AFiK9Q4aJZnWh4x1Im3iaO4SEaMhfCBU3y6sHYJKwcn7QABILnbetajqVTghNWdP8EXoGBoMw7aiJUINM4qH0gSlKfOAKni2zhfBVzAIVo83iaLdicFNblEOAdRTxg76Gkmwhn0AQAA"
    te = TransactionEffects.deserialize(base64.b64decode(bcs))
    print(te)
