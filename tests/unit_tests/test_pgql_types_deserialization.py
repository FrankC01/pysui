#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Unit tests for OpenMove*GQL dataclass deserialization."""

import json
import pathlib
import pytest
from pysui.sui.sui_pgql import pgql_types as gql


# ── Fixture loading ─────────────────────────────────────────────────────────

FIXTURE_DIR = pathlib.Path(__file__).parent / "fixtures"


@pytest.fixture
def parms_functions():
    """Load parms module function fixtures."""
    with open(FIXTURE_DIR / "parms_functions.json") as f:
        return json.load(f)


@pytest.fixture
def txn_base_commands():
    """Load transaction base command fixtures."""
    with open(FIXTURE_DIR / "txn_base_commands.json") as f:
        return json.load(f)


# ── _body_from_dict tests ───────────────────────────────────────────────────


class TestBodyFromDict:
    """Test OpenMoveTypeSignatureBody deserialization."""

    def test_scalar_body_string(self):
        """Scalar body as bare string."""
        body = gql._body_from_dict("u8")
        assert isinstance(body, gql.OpenMoveScalarBodyGQL)
        assert body.scalar_type == "u8"

    def test_scalar_body_all_types(self):
        """All scalar types."""
        for scalar in ["u8", "u16", "u32", "u64", "u128", "u256", "bool", "address"]:
            body = gql._body_from_dict(scalar)
            assert isinstance(body, gql.OpenMoveScalarBodyGQL)
            assert body.scalar_type == scalar

    def test_vector_body_scalar(self):
        """Vector of scalar."""
        body = gql._body_from_dict({"vector": "u8"})
        assert isinstance(body, gql.OpenMoveVectorBodyGQL)
        assert isinstance(body.inner, gql.OpenMoveScalarBodyGQL)
        assert body.inner.scalar_type == "u8"

    def test_vector_nested_depth_2(self):
        """vector<vector<u8>>."""
        body = gql._body_from_dict({"vector": {"vector": "u8"}})
        assert isinstance(body, gql.OpenMoveVectorBodyGQL)
        assert isinstance(body.inner, gql.OpenMoveVectorBodyGQL)
        assert isinstance(body.inner.inner, gql.OpenMoveScalarBodyGQL)
        assert body.inner.inner.scalar_type == "u8"

    def test_vector_nested_depth_3(self):
        """vector<vector<vector<u8>>> — original bug case."""
        body = gql._body_from_dict({"vector": {"vector": {"vector": "u8"}}})
        assert isinstance(body, gql.OpenMoveVectorBodyGQL)
        assert isinstance(body.inner, gql.OpenMoveVectorBodyGQL)
        assert isinstance(body.inner.inner, gql.OpenMoveVectorBodyGQL)
        assert isinstance(body.inner.inner.inner, gql.OpenMoveScalarBodyGQL)
        assert body.inner.inner.inner.scalar_type == "u8"

    def test_datatype_body_no_type_params(self):
        """Datatype with no type parameters."""
        body = gql._body_from_dict({
            "datatype": {
                "package": "0x2",
                "module": "sui",
                "type": "SUI",
                "typeParameters": []
            }
        })
        assert isinstance(body, gql.OpenMoveDatatypeBodyGQL)
        assert body.package == "0x2"
        assert body.module == "sui"
        assert body.type_name == "SUI"
        assert body.type_parameters == []

    def test_datatype_body_scalar_type_param(self):
        """Datatype with scalar string type parameter."""
        body = gql._body_from_dict({
            "datatype": {
                "package": "0x1",
                "module": "option",
                "type": "Option",
                "typeParameters": ["u8"]
            }
        })
        assert isinstance(body, gql.OpenMoveDatatypeBodyGQL)
        assert body.type_name == "Option"
        assert len(body.type_parameters) == 1
        assert isinstance(body.type_parameters[0], gql.OpenMoveScalarBodyGQL)
        assert body.type_parameters[0].scalar_type == "u8"

    def test_datatype_body_datatype_type_param(self):
        """Datatype with datatype type parameter."""
        body = gql._body_from_dict({
            "datatype": {
                "package": "0x1",
                "module": "option",
                "type": "Option",
                "typeParameters": [
                    {
                        "datatype": {
                            "package": "0x2",
                            "module": "sui",
                            "type": "SUI",
                            "typeParameters": []
                        }
                    }
                ]
            }
        })
        assert isinstance(body, gql.OpenMoveDatatypeBodyGQL)
        assert len(body.type_parameters) == 1
        assert isinstance(body.type_parameters[0], gql.OpenMoveDatatypeBodyGQL)
        assert body.type_parameters[0].type_name == "SUI"

    def test_datatype_body_vector_type_param(self):
        """Datatype with vector type parameter."""
        body = gql._body_from_dict({
            "datatype": {
                "package": "0x1",
                "module": "option",
                "type": "Option",
                "typeParameters": [{"vector": "u8"}]
            }
        })
        assert isinstance(body, gql.OpenMoveDatatypeBodyGQL)
        assert len(body.type_parameters) == 1
        assert isinstance(body.type_parameters[0], gql.OpenMoveVectorBodyGQL)

    def test_type_parameter_body(self):
        """Generic type parameter."""
        body = gql._body_from_dict({"typeParameter": 0})
        assert isinstance(body, gql.OpenMoveTypeParamBodyGQL)
        assert body.index == 0

    def test_type_parameter_indices(self):
        """Multiple type parameter indices."""
        for idx in [0, 1, 5, 15]:
            body = gql._body_from_dict({"typeParameter": idx})
            assert body.index == idx

    def test_vector_of_datatype(self):
        """vector<String>."""
        body = gql._body_from_dict({
            "vector": {
                "datatype": {
                    "package": "0x1",
                    "module": "string",
                    "type": "String",
                    "typeParameters": []
                }
            }
        })
        assert isinstance(body, gql.OpenMoveVectorBodyGQL)
        assert isinstance(body.inner, gql.OpenMoveDatatypeBodyGQL)
        assert body.inner.type_name == "String"


# ── OpenMoveTypeSignatureGQL.from_query tests ───────────────────────────────


class TestOpenMoveTypeSignatureGQL:
    """Test OpenMoveTypeSignature deserialization."""

    def test_scalar_no_ref(self):
        """Scalar with no reference."""
        sig = gql.OpenMoveTypeSignatureGQL.from_query({
            "body": "u8"
        })
        assert sig.ref is None
        assert isinstance(sig.body, gql.OpenMoveScalarBodyGQL)
        assert sig.body.scalar_type == "u8"

    def test_scalar_with_ref(self):
        """Scalar with immutable reference."""
        sig = gql.OpenMoveTypeSignatureGQL.from_query({
            "ref": "&",
            "body": "u8"
        })
        assert sig.ref == "&"
        assert isinstance(sig.body, gql.OpenMoveScalarBodyGQL)

    def test_scalar_with_mut_ref(self):
        """Scalar with mutable reference."""
        sig = gql.OpenMoveTypeSignatureGQL.from_query({
            "ref": "&mut",
            "body": "u8"
        })
        assert sig.ref == "&mut"

    def test_vector_no_ref(self):
        """Vector with no reference."""
        sig = gql.OpenMoveTypeSignatureGQL.from_query({
            "body": {"vector": "u8"}
        })
        assert sig.ref is None
        assert isinstance(sig.body, gql.OpenMoveVectorBodyGQL)

    def test_datatype_with_ref(self):
        """Datatype with reference."""
        sig = gql.OpenMoveTypeSignatureGQL.from_query({
            "ref": "&mut",
            "body": {
                "datatype": {
                    "package": "0x2",
                    "module": "sui",
                    "type": "SUI",
                    "typeParameters": []
                }
            }
        })
        assert sig.ref == "&mut"
        assert isinstance(sig.body, gql.OpenMoveDatatypeBodyGQL)


# ── OpenMoveTypeGQL.from_query tests ────────────────────────────────────────


class TestOpenMoveTypeGQL:
    """Test OpenMoveType deserialization."""

    def test_with_signature_and_repr(self):
        """OpenMoveType with signature and repr."""
        opt = gql.OpenMoveTypeGQL.from_query({
            "signature": {
                "body": "u8"
            },
            "repr": "u8"
        })
        assert opt.repr == "u8"
        assert isinstance(opt.signature, gql.OpenMoveTypeSignatureGQL)
        assert isinstance(opt.signature.body, gql.OpenMoveScalarBodyGQL)

    def test_repr_defaults_to_empty_string(self):
        """Missing repr defaults to empty string."""
        opt = gql.OpenMoveTypeGQL.from_query({
            "signature": {
                "body": "u64"
            }
        })
        assert opt.repr == ""

    def test_complex_type_with_repr(self):
        """Complex nested type with repr."""
        opt = gql.OpenMoveTypeGQL.from_query({
            "signature": {
                "ref": "&mut",
                "body": {
                    "datatype": {
                        "package": "0x2",
                        "module": "coin",
                        "type": "Coin",
                        "typeParameters": [{"typeParameter": 0}]
                    }
                }
            },
            "repr": "Coin<T>"
        })
        assert opt.repr == "Coin<T>"
        assert opt.signature.ref == "&mut"
        assert isinstance(opt.signature.body, gql.OpenMoveDatatypeBodyGQL)
        assert len(opt.signature.body.type_parameters) == 1


# ── MoveFieldGQL.from_query tests ───────────────────────────────────────────


class TestMoveFieldGQL:
    """Test MoveField deserialization."""

    def test_field_with_name_and_type(self):
        """Field with both name and type."""
        field = gql.MoveFieldGQL.from_query({
            "name": "balance",
            "type": {
                "signature": {"body": "u64"},
                "repr": "u64"
            }
        })
        assert field.name == "balance"
        assert field.type_ is not None
        assert isinstance(field.type_, gql.OpenMoveTypeGQL)

    def test_field_with_only_name(self):
        """Field with only name (no type)."""
        field = gql.MoveFieldGQL.from_query({
            "name": "index"
        })
        assert field.name == "index"
        assert field.type_ is None

    def test_field_with_complex_type(self):
        """Field with complex nested type."""
        field = gql.MoveFieldGQL.from_query({
            "name": "items",
            "type": {
                "signature": {
                    "body": {
                        "vector": {
                            "datatype": {
                                "package": "0x1",
                                "module": "string",
                                "type": "String",
                                "typeParameters": []
                            }
                        }
                    }
                },
                "repr": "vector<String>"
            }
        })
        assert field.name == "items"
        assert field.type_.signature.ref is None
        assert isinstance(field.type_.signature.body, gql.OpenMoveVectorBodyGQL)


# ── MoveFunctionGQL.from_query tests ────────────────────────────────────────


class TestMoveFunctionGQL:
    """Test MoveFunction deserialization from fixtures."""

    def test_check_bool_function(self, parms_functions):
        """Deserialize check_bool function."""
        func_dict = next(f for f in parms_functions if f["functionName"] == "check_bool")
        func = gql.MoveFunctionGQL.from_query(func_dict)
        assert func.function_name == "check_bool"
        assert func.is_entry is False
        assert func.visibility == "PUBLIC"
        assert len(func.parameters) == 1  # TxContext is skipped
        assert isinstance(func.parameters[0].signature.body, gql.OpenMoveScalarBodyGQL)
        assert func.parameters[0].signature.body.scalar_type == "bool"

    def test_check_uints_function(self, parms_functions):
        """Deserialize check_uints function with multiple scalars."""
        func_dict = next(f for f in parms_functions if f["functionName"] == "check_uints")
        func = gql.MoveFunctionGQL.from_query(func_dict)
        assert len(func.parameters) == 5  # u16, u32, u64, u128, u256 (TxContext skipped)
        expected_types = ["u16", "u32", "u64", "u128", "u256"]
        for i, expected in enumerate(expected_types):
            assert func.parameters[i].signature.body.scalar_type == expected

    def test_check_vec_deep_u8_function(self, parms_functions):
        """Deserialize check_vec_deep_u8 (depth 3 vector)."""
        func_dict = next(f for f in parms_functions if f["functionName"] == "check_vec_deep_u8")
        func = gql.MoveFunctionGQL.from_query(func_dict)
        assert len(func.parameters) == 1  # TxContext skipped
        param = func.parameters[0]
        assert isinstance(param.signature.body, gql.OpenMoveVectorBodyGQL)
        assert isinstance(param.signature.body.inner, gql.OpenMoveVectorBodyGQL)
        assert isinstance(param.signature.body.inner.inner, gql.OpenMoveVectorBodyGQL)
        assert isinstance(param.signature.body.inner.inner.inner, gql.OpenMoveScalarBodyGQL)
        assert param.signature.body.inner.inner.inner.scalar_type == "u8"

    def test_check_vec_u8_function(self, parms_functions):
        """Deserialize check_vec_u8 (depth 1 vector)."""
        func_dict = next(f for f in parms_functions if f["functionName"] == "check_vec_u8")
        func = gql.MoveFunctionGQL.from_query(func_dict)
        assert len(func.parameters) == 1
        param = func.parameters[0]
        assert isinstance(param.signature.body, gql.OpenMoveVectorBodyGQL)
        assert isinstance(param.signature.body.inner, gql.OpenMoveScalarBodyGQL)
        assert param.signature.body.inner.scalar_type == "u8"

    def test_check_optional_uints_function(self, parms_functions):
        """Deserialize check_optional_uints with Option<scalar> types."""
        func_dict = next(f for f in parms_functions if f["functionName"] == "check_optional_uints")
        func = gql.MoveFunctionGQL.from_query(func_dict)
        assert len(func.parameters) == 5
        for i, param in enumerate(func.parameters):
            assert isinstance(param.signature.body, gql.OpenMoveDatatypeBodyGQL)
            assert param.signature.body.type_name == "Option"
            assert len(param.signature.body.type_parameters) == 1

    def test_check_string_function(self, parms_functions):
        """Deserialize check_string with String type and & reference."""
        func_dict = next(f for f in parms_functions if f["functionName"] == "check_string")
        func = gql.MoveFunctionGQL.from_query(func_dict)
        assert len(func.parameters) == 1  # TxContext skipped
        param = func.parameters[0]
        assert param.signature.ref == "&"
        assert isinstance(param.signature.body, gql.OpenMoveDatatypeBodyGQL)
        assert param.signature.body.type_name == "String"

    def test_check_vec_option_string_function(self, parms_functions):
        """Deserialize check_vec_option_string with vector<Option<String>>."""
        func_dict = next(f for f in parms_functions if f["functionName"] == "check_vec_option_string")
        func = gql.MoveFunctionGQL.from_query(func_dict)
        assert len(func.parameters) == 1
        param = func.parameters[0]
        assert isinstance(param.signature.body, gql.OpenMoveVectorBodyGQL)
        inner_dt = param.signature.body.inner
        assert isinstance(inner_dt, gql.OpenMoveDatatypeBodyGQL)
        assert inner_dt.type_name == "Option"

    def test_function_with_return_type(self, parms_functions):
        """Deserialize function with return type."""
        func_dict = next(f for f in parms_functions if f["functionName"] == "check_phoney")
        func = gql.MoveFunctionGQL.from_query(func_dict)
        assert len(func.returns) == 1
        ret = func.returns[0]
        assert isinstance(ret.signature.body, gql.OpenMoveScalarBodyGQL)
        assert ret.signature.body.scalar_type == "bool"

    def test_check_all_with_generic_type_param(self, parms_functions):
        """Deserialize check_all with generic type parameter."""
        func_dict = next(f for f in parms_functions if f["functionName"] == "check_all")
        func = gql.MoveFunctionGQL.from_query(func_dict)
        assert len(func.type_parameters) == 1
        # Find the vector<MayType<T>> parameter
        vec_maybe = next(
            (p for p in func.parameters
             if isinstance(p.signature.body, gql.OpenMoveVectorBodyGQL)
             and isinstance(p.signature.body.inner, gql.OpenMoveDatatypeBodyGQL)
             and p.signature.body.inner.type_name == "MayType"),
            None
        )
        assert vec_maybe is not None
        assert len(vec_maybe.signature.body.inner.type_parameters) == 1
        type_param = vec_maybe.signature.body.inner.type_parameters[0]
        assert isinstance(type_param, gql.OpenMoveTypeParamBodyGQL)
        assert type_param.index == 0

    def test_check_id_vec_function(self, parms_functions):
        """Deserialize check_id_vec with vector<ID>."""
        func_dict = next(f for f in parms_functions if f["functionName"] == "check_id_vec")
        func = gql.MoveFunctionGQL.from_query(func_dict)
        assert len(func.parameters) == 1
        param = func.parameters[0]
        assert isinstance(param.signature.body, gql.OpenMoveVectorBodyGQL)
        inner = param.signature.body.inner
        assert isinstance(inner, gql.OpenMoveDatatypeBodyGQL)
        assert inner.type_name == "ID"
        assert inner.module == "object"
        assert inner.package == "0x0000000000000000000000000000000000000000000000000000000000000002"


# ── Transaction base command fixtures ───────────────────────────────────────


class TestTxnBaseCommands:
    """Test deserialization of _TransactionBase command parameter signatures."""

    def test_split_coin_parameters(self, txn_base_commands):
        """Verify split_coin parameter structure."""
        params = txn_base_commands["split_coin"]
        assert len(params) == 2
        # &mut Coin<SUI>
        assert params[0]["signature"]["ref"] == "&mut"
        assert params[0]["signature"]["body"]["datatype"]["type"] == "SUI"
        # vector<u64>
        assert params[1]["signature"]["body"]["vector"] == "u64"

    def test_transfer_objects_parameters(self, txn_base_commands):
        """Verify transfer_objects parameter structure."""
        params = txn_base_commands["transfer_objects"]
        assert len(params) == 2
        # address
        assert params[0]["signature"]["body"] == "address"
        # vector<Object>
        assert params[1]["signature"]["body"]["vector"]["datatype"]["type"] == "SUI"

    def test_make_move_vec_parameters(self, txn_base_commands):
        """Verify make_move_vec parameter structure."""
        params = txn_base_commands["make_move_vec"]
        assert len(params) == 1
        assert params[0]["signature"]["body"]["vector"]["datatype"]["type"] == "SUI"

    def test_transfer_sui_parameters(self, txn_base_commands):
        """Verify transfer_sui parameter structure."""
        params = txn_base_commands["transfer_sui"]
        assert len(params) == 3
        assert params[0]["signature"]["body"] == "address"
        assert params[1]["signature"]["ref"] == "&mut"
        assert params[2]["signature"]["body"] == "u64"

    def test_all_commands_present(self, txn_base_commands):
        """Verify all 7 commands are in fixture."""
        expected = {
            "split_coin",
            "merge_coins",
            "transfer_objects",
            "transfer_sui",
            "public_transfer_objects",
            "make_move_vec",
            "publish_upgrade"
        }
        assert set(txn_base_commands.keys()) == expected
