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

"""Transaction result tests."""

from pysui.sui.sui_types import TxEffectResult, MovePackage


def test_payallsui_result_pass(payallsui_result):
    """Valid result."""
    result = TxEffectResult.from_dict(payallsui_result)
    assert result.succeeded is True
    assert result.status == "success"


def test_transferobject_result_pass(transfer_object_result):
    """Valid result."""
    result = TxEffectResult.from_dict(transfer_object_result)
    assert result.succeeded is True
    assert result.status == "success"


def test_publish_nest_result_pass(publish_nest_result):
    """Valid result."""
    result = TxEffectResult.from_dict(publish_nest_result)
    assert result.succeeded is True
    assert result.status == "success"


def test_publish_track_result_pass(publish_track_result):
    """Valid result."""
    result = TxEffectResult.from_dict(publish_track_result)
    assert result.succeeded is True
    assert result.status == "success"


def test_move_call_result_pass(move_call_result):
    """Valid result."""
    result = TxEffectResult.from_dict(move_call_result)
    assert result.succeeded is True
    assert result.status == "success"


def test_package_track_result_pass(package_track_result):
    """Valid result."""
    result = MovePackage(package_track_result)
    assert result is not None


def test_package_nest_result_pass(package_nest_result):
    """Valid result."""
    result = MovePackage(package_nest_result)
    assert result is not None


def test_bad_pay_result_pass(bad_pay_result):
    """Invalid result."""
    result = TxEffectResult.from_dict(bad_pay_result)
    assert result.succeeded is False
    assert result.status == "failure - InsufficientGas"
