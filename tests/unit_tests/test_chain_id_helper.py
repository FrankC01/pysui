#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Unit tests for update_move_toml_chain_id — offline, no network required."""

from pathlib import Path

import pytest

from tests.integration_tests.conftest import update_move_toml_chain_id


_TOML_TEMPLATE = """\
[package]
name = "sui-test"
edition = "2024.beta"

[dependencies]
Sui = {{ git = "https://github.com/MystenLabs/sui.git", subdir = "crates/sui-framework/packages/sui-framework", rev = "framework/testnet" }}

[addresses]
sui_test = "0x0"

[dev-addresses]
sui_test = "0x0"

[dev-dependencies.Sui]
devnet = "{old_id}"
"""


def _make_toml(tmp_path: Path, old_id: str) -> Path:
    p = tmp_path / "Move.toml"
    p.write_text(_TOML_TEMPLATE.format(old_id=old_id))
    return p


def test_chain_id_replaced(tmp_path: Path) -> None:
    """update_move_toml_chain_id replaces the old chain ID with the new one."""
    p = _make_toml(tmp_path, "a63d14dc")
    update_move_toml_chain_id(p, "deadbeef")
    assert 'devnet = "deadbeef"' in p.read_text()
    assert "a63d14dc" not in p.read_text()


def test_chain_id_idempotent(tmp_path: Path) -> None:
    """Calling update_move_toml_chain_id twice with the same ID is stable."""
    p = _make_toml(tmp_path, "a63d14dc")
    update_move_toml_chain_id(p, "cafecafe")
    update_move_toml_chain_id(p, "cafecafe")
    assert p.read_text().count('devnet = "cafecafe"') == 1


def test_chain_id_only_devnet_entry_changed(tmp_path: Path) -> None:
    """Only the devnet entry is modified; other file content is preserved."""
    p = _make_toml(tmp_path, "a63d14dc")
    original = p.read_text()
    update_move_toml_chain_id(p, "newchain1")
    updated = p.read_text()
    assert "sui-test" in updated
    assert "MystenLabs" in updated
    assert original.replace("a63d14dc", "newchain1") == updated
