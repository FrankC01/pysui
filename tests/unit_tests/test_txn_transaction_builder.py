#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Tests for ProgrammableTransactionBuilder.restore_unresolved_inputs (Task #102)."""

from pysui.sui.sui_bcs import bcs
from pysui.sui.sui_common.txn_transaction_builder import ProgrammableTransactionBuilder


def _unresolved(object_str: str) -> bcs.UnresolvedObjectArg:
    return bcs.UnresolvedObjectArg(object_str, False, False, 0, "")


def _resolved_pair(object_str: str) -> tuple:
    """Build a resolved (BuilderArg, CallArg) pair the same way _resolve_deferred_inputs would."""
    address = bcs.Address.from_str(object_str)
    barg = bcs.BuilderArg("Object", address)
    carg = bcs.CallArg(
        "Object",
        bcs.ObjectArg(
            "ImmOrOwnedObject",
            bcs.ObjectReference(address, 1, bcs.Digest.from_bytes(b"d" * 32)),
        ),
    )
    return barg, carg


def _resolve(builder: ProgrammableTransactionBuilder, idx: int, object_str: str) -> None:
    """Resolve the single input at idx (builder must have no other unresolved inputs)."""
    builder.resolved_object_inputs({idx: _resolved_pair(object_str)})


_SHARED_ID = "0x" + "aa" * 32
_OTHER_ID = "0x" + "bb" * 32


class TestRestoreUnresolvedInputs:
    """Test reverting a resolved input back to its unresolved form."""

    def test_reverts_single_resolved_entry(self):
        """A resolved entry is put back into Unresolved form with the original arg."""
        builder = ProgrammableTransactionBuilder()
        original = _unresolved(_SHARED_ID)
        builder.input_obj_from_unresolved_object(original)
        _resolve(builder, 0, _SHARED_ID)
        assert builder.get_unresolved_inputs() == {}

        builder.restore_unresolved_inputs({0: original})

        unresolved = builder.get_unresolved_inputs()
        assert unresolved == {0: original}
        assert builder.objects_registry[_SHARED_ID] is original

    def test_leaves_other_inputs_untouched(self):
        """Restoring one index does not disturb a different resolved input."""
        builder = ProgrammableTransactionBuilder()
        target = _unresolved(_SHARED_ID)
        other = _unresolved(_OTHER_ID)
        builder.input_obj_from_unresolved_object(target)
        builder.input_obj_from_unresolved_object(other)
        builder.resolved_object_inputs(
            {0: _resolved_pair(_SHARED_ID), 1: _resolved_pair(_OTHER_ID)}
        )
        assert builder.get_unresolved_inputs() == {}

        builder.restore_unresolved_inputs({0: target})

        unresolved = builder.get_unresolved_inputs()
        assert unresolved == {0: target}
        assert 1 not in unresolved

    def test_empty_entries_is_noop(self):
        """Calling with no entries leaves fully-resolved inputs untouched."""
        builder = ProgrammableTransactionBuilder()
        original = _unresolved(_SHARED_ID)
        builder.input_obj_from_unresolved_object(original)
        _resolve(builder, 0, _SHARED_ID)
        before = dict(builder.inputs)

        builder.restore_unresolved_inputs({})

        assert builder.inputs == before
