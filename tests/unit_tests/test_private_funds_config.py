#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Unit tests for pysui.private_transfer.config.PrivateFundsConfig."""

import json
import pathlib
from unittest.mock import MagicMock, patch

import pytest

from pysui.private_transfer.config import (
    PrivateFundsConfig,
    PrivateFundsGroup,
    _PrivateFundsConfigModel,
    _CURRENT_PRIVATEFUNDS_CONFIG_VERSION,
)
from pysui.sui.sui_common.config.confgroup import GroupProtocol, NetworkType


def _make_pysui_config(
    *,
    protocol: GroupProtocol = GroupProtocol.GRPC,
    profile_name: str = "devnet",
    network_type: NetworkType = NetworkType.DEVELOP,
) -> MagicMock:
    """Build a minimal PysuiConfiguration mock exposing the attributes
    PrivateFundsConfig reads: active_group.group_protocol, active_profile,
    and active_group.active_profile.network_type.
    """
    cfg = MagicMock()
    cfg.active_group.group_protocol = protocol
    cfg.active_profile = profile_name
    cfg.active_group.active_profile.network_type = network_type
    return cfg


def _valid_group(
    name: str = "devnet", network_type: NetworkType = NetworkType.DEVELOP
) -> PrivateFundsGroup:
    """Return a PrivateFundsGroup with non-placeholder ids."""
    return PrivateFundsGroup(
        name=name,
        package_id="0xaaaa",
        token_registry="0xbbbb",
        account_registry="0xcccc",
        network_type=network_type,
    )


def _write_model(tmp_path, model: _PrivateFundsConfigModel) -> None:
    """Persist a model directly to PrivateFundsConfig.json under tmp_path."""
    (tmp_path / "PrivateFundsConfig.json").write_text(model.to_json(indent=2))


def _write_raw_v1_json(tmp_path) -> None:
    """Write a hand-authored pre-migration (version 1, no networkType key) config."""
    raw = {
        "version": 1,
        "groups": [
            {
                "name": "devnet",
                "packageId": "0xaaaa",
                "tokenRegistry": "0xbbbb",
                "accountRegistry": "0xcccc",
            },
            {
                "name": "testnet",
                "packageId": "0xaaaa",
                "tokenRegistry": "0xbbbb",
                "accountRegistry": "0xcccc",
            },
            {
                "name": "mainnet",
                "packageId": "0xaaaa",
                "tokenRegistry": "0xbbbb",
                "accountRegistry": "0xcccc",
            },
            {
                "name": "custom",
                "packageId": "0xaaaa",
                "tokenRegistry": "0xbbbb",
                "accountRegistry": "0xcccc",
            },
        ],
    }
    (tmp_path / "PrivateFundsConfig.json").write_text(json.dumps(raw, indent=2))


# 1. Dataclass serialization


class TestDataclassSerialization:
    def test_group_round_trip_with_network_type(self):
        group = _valid_group(network_type=NetworkType.TEST)
        restored = PrivateFundsGroup.from_json(group.to_json())
        assert restored == group
        assert restored.network_type == NetworkType.TEST

    def test_group_round_trip_network_type_none(self):
        group = PrivateFundsGroup(
            name="devnet",
            package_id="0xaaaa",
            token_registry="0xbbbb",
            account_registry="0xcccc",
        )
        assert group.network_type is None
        restored = PrivateFundsGroup.from_json(group.to_json())
        assert restored.network_type is None

    def test_model_round_trip(self):
        model = _PrivateFundsConfigModel(
            version=_CURRENT_PRIVATEFUNDS_CONFIG_VERSION,
            groups=[_valid_group("devnet"), _valid_group("testnet")],
        )
        restored = _PrivateFundsConfigModel.from_json(model.to_json())
        assert restored.version == _CURRENT_PRIVATEFUNDS_CONFIG_VERSION
        assert len(restored.groups) == 2

    def test_model_deserializes_missing_network_type_key(self):
        raw = {
            "version": 1,
            "groups": [
                {
                    "name": "devnet",
                    "packageId": "0xaaaa",
                    "tokenRegistry": "0xbbbb",
                    "accountRegistry": "0xcccc",
                }
            ],
        }
        model = _PrivateFundsConfigModel.from_json(json.dumps(raw))
        assert model.groups[0].network_type is None


# 2. _initialize_config


class TestInitializeConfig:
    def test_creates_file(self, tmp_path):
        cfg_root = tmp_path / "fresh"
        with patch.object(PrivateFundsConfig, "_DEFAULT_DIR", str(cfg_root)):
            pcfg = _make_pysui_config(profile_name="devnet", network_type=NetworkType.DEVELOP)
            PrivateFundsConfig(pysui_config=pcfg)
            assert (cfg_root / "PrivateFundsConfig.json").exists()

    def test_creates_parent_dirs_and_default_groups(self, tmp_path):
        cfg_root = tmp_path / "nested" / "dir"
        with patch.object(PrivateFundsConfig, "_DEFAULT_DIR", str(cfg_root)):
            pcfg = _make_pysui_config(profile_name="devnet", network_type=NetworkType.DEVELOP)
            PrivateFundsConfig(pysui_config=pcfg)
            cfg_file = cfg_root / "PrivateFundsConfig.json"
            assert cfg_file.exists()
            model = _PrivateFundsConfigModel.from_json(cfg_file.read_text())
            assert model.version == _CURRENT_PRIVATEFUNDS_CONFIG_VERSION
            names = {g.name for g in model.groups}
            assert names == {"devnet", "testnet", "mainnet"}

    def test_default_groups_have_correct_network_types(self, tmp_path):
        cfg_root = tmp_path / "root"
        with patch.object(PrivateFundsConfig, "_DEFAULT_DIR", str(cfg_root)):
            pcfg = _make_pysui_config(profile_name="devnet", network_type=NetworkType.DEVELOP)
            PrivateFundsConfig(pysui_config=pcfg)
            model = _PrivateFundsConfigModel.from_json(
                (cfg_root / "PrivateFundsConfig.json").read_text()
            )
            by_name = {g.name: g for g in model.groups}
            assert by_name["devnet"].network_type == NetworkType.DEVELOP
            assert by_name["testnet"].network_type == NetworkType.TEST
            assert by_name["mainnet"].network_type == NetworkType.PRODUCTION

    def test_devnet_has_real_ids_testnet_mainnet_placeholders(self, tmp_path):
        cfg_root = tmp_path / "root"
        with patch.object(PrivateFundsConfig, "_DEFAULT_DIR", str(cfg_root)):
            pcfg = _make_pysui_config(profile_name="devnet", network_type=NetworkType.DEVELOP)
            PrivateFundsConfig(pysui_config=pcfg)
            model = _PrivateFundsConfigModel.from_json(
                (cfg_root / "PrivateFundsConfig.json").read_text()
            )
            by_name = {g.name: g for g in model.groups}
            assert by_name["devnet"].package_id != "0x"
            assert by_name["testnet"].package_id == "0x"
            assert by_name["mainnet"].package_id == "0x"


# 3. __init__ / from_cfg_path handling


class TestInit:
    def test_from_cfg_path_missing_file_raises(self, tmp_path):
        pcfg = _make_pysui_config()
        with pytest.raises(ValueError, match="does not exist"):
            PrivateFundsConfig(pysui_config=pcfg, from_cfg_path=str(tmp_path))

    def test_loads_existing_file_from_cfg_path(self, tmp_path):
        model = _PrivateFundsConfigModel(
            version=_CURRENT_PRIVATEFUNDS_CONFIG_VERSION,
            groups=[_valid_group("devnet", NetworkType.DEVELOP)],
        )
        _write_model(tmp_path, model)
        pcfg = _make_pysui_config(profile_name="devnet", network_type=NetworkType.DEVELOP)
        cfg = PrivateFundsConfig(pysui_config=pcfg, from_cfg_path=str(tmp_path))
        assert cfg.active_group.name == "devnet"


# 4. _match_active_group gates


class TestMatchActiveGroupGates:
    def test_gate1_rejects_non_graphql_grpc_protocol(self, tmp_path):
        model = _PrivateFundsConfigModel(
            version=_CURRENT_PRIVATEFUNDS_CONFIG_VERSION,
            groups=[_valid_group("devnet", NetworkType.DEVELOP)],
        )
        _write_model(tmp_path, model)
        pcfg = _make_pysui_config(
            protocol=GroupProtocol.OTHER,
            profile_name="devnet",
            network_type=NetworkType.DEVELOP,
        )
        with pytest.raises(ValueError, match="GraphQL or gRPC"):
            PrivateFundsConfig(pysui_config=pcfg, from_cfg_path=str(tmp_path))

    def test_gate1_accepts_graphql(self, tmp_path):
        model = _PrivateFundsConfigModel(
            version=_CURRENT_PRIVATEFUNDS_CONFIG_VERSION,
            groups=[_valid_group("devnet", NetworkType.DEVELOP)],
        )
        _write_model(tmp_path, model)
        pcfg = _make_pysui_config(
            protocol=GroupProtocol.GRAPHQL,
            profile_name="devnet",
            network_type=NetworkType.DEVELOP,
        )
        cfg = PrivateFundsConfig(pysui_config=pcfg, from_cfg_path=str(tmp_path))
        assert cfg.active_group.name == "devnet"

    def test_gate2_no_matching_group_name_raises(self, tmp_path):
        model = _PrivateFundsConfigModel(
            version=_CURRENT_PRIVATEFUNDS_CONFIG_VERSION,
            groups=[_valid_group("devnet", NetworkType.DEVELOP)],
        )
        _write_model(tmp_path, model)
        pcfg = _make_pysui_config(profile_name="nowhere", network_type=NetworkType.DEVELOP)
        with pytest.raises(ValueError, match="No PrivateFundsConfig group named"):
            PrivateFundsConfig(pysui_config=pcfg, from_cfg_path=str(tmp_path))

    def test_gate3_placeholder_ids_raise(self, tmp_path):
        group = PrivateFundsGroup(
            name="testnet",
            package_id="0x",
            token_registry="0x",
            account_registry="0x",
            network_type=NetworkType.TEST,
        )
        model = _PrivateFundsConfigModel(
            version=_CURRENT_PRIVATEFUNDS_CONFIG_VERSION, groups=[group]
        )
        _write_model(tmp_path, model)
        pcfg = _make_pysui_config(profile_name="testnet", network_type=NetworkType.TEST)
        with pytest.raises(ValueError, match="unconfigured"):
            PrivateFundsConfig(pysui_config=pcfg, from_cfg_path=str(tmp_path))

    def test_gate4_network_type_mismatch_raises(self, tmp_path):
        model = _PrivateFundsConfigModel(
            version=_CURRENT_PRIVATEFUNDS_CONFIG_VERSION,
            groups=[_valid_group("devnet", NetworkType.DEVELOP)],
        )
        _write_model(tmp_path, model)
        pcfg = _make_pysui_config(profile_name="devnet", network_type=NetworkType.TEST)
        with pytest.raises(ValueError, match="network_type"):
            PrivateFundsConfig(pysui_config=pcfg, from_cfg_path=str(tmp_path))

    def test_gate4_network_type_match_succeeds(self, tmp_path):
        model = _PrivateFundsConfigModel(
            version=_CURRENT_PRIVATEFUNDS_CONFIG_VERSION,
            groups=[_valid_group("devnet", NetworkType.DEVELOP)],
        )
        _write_model(tmp_path, model)
        pcfg = _make_pysui_config(profile_name="devnet", network_type=NetworkType.DEVELOP)
        cfg = PrivateFundsConfig(pysui_config=pcfg, from_cfg_path=str(tmp_path))
        assert cfg.active_group.network_type == NetworkType.DEVELOP

    def test_gate4_unset_network_type_raises(self, tmp_path):
        group = PrivateFundsGroup(
            name="custom",
            package_id="0xaaaa",
            token_registry="0xbbbb",
            account_registry="0xcccc",
            network_type=None,
        )
        model = _PrivateFundsConfigModel(
            version=_CURRENT_PRIVATEFUNDS_CONFIG_VERSION, groups=[group]
        )
        _write_model(tmp_path, model)
        pcfg = _make_pysui_config(profile_name="custom", network_type=NetworkType.TEST)
        with pytest.raises(ValueError, match="network_type"):
            PrivateFundsConfig(pysui_config=pcfg, from_cfg_path=str(tmp_path))


# 5. active_group property and default_path


class TestActiveGroupAndDefaultPath:
    def test_active_group_returns_matched_group(self, tmp_path):
        model = _PrivateFundsConfigModel(
            version=_CURRENT_PRIVATEFUNDS_CONFIG_VERSION,
            groups=[_valid_group("devnet", NetworkType.DEVELOP)],
        )
        _write_model(tmp_path, model)
        pcfg = _make_pysui_config(profile_name="devnet", network_type=NetworkType.DEVELOP)
        cfg = PrivateFundsConfig(pysui_config=pcfg, from_cfg_path=str(tmp_path))
        assert isinstance(cfg.active_group, PrivateFundsGroup)
        assert cfg.active_group.name == "devnet"

    def test_default_path(self):
        assert PrivateFundsConfig.default_path() == pathlib.Path(
            PrivateFundsConfig._DEFAULT_DIR
        ).expanduser()


# 6. save()


class TestSave:
    def test_save_persists_to_config_file(self, tmp_path):
        model = _PrivateFundsConfigModel(
            version=_CURRENT_PRIVATEFUNDS_CONFIG_VERSION,
            groups=[_valid_group("devnet", NetworkType.DEVELOP)],
        )
        _write_model(tmp_path, model)
        pcfg = _make_pysui_config(profile_name="devnet", network_type=NetworkType.DEVELOP)
        cfg = PrivateFundsConfig(pysui_config=pcfg, from_cfg_path=str(tmp_path))
        cfg._model.groups.append(_valid_group("testnet", NetworkType.TEST))
        cfg.save()
        reloaded = _PrivateFundsConfigModel.from_json(
            (tmp_path / "PrivateFundsConfig.json").read_text()
        )
        assert len(reloaded.groups) == 2

    def test_save_creates_parent_dirs_for_override_path(self, tmp_path):
        model = _PrivateFundsConfigModel(
            version=_CURRENT_PRIVATEFUNDS_CONFIG_VERSION,
            groups=[_valid_group("devnet", NetworkType.DEVELOP)],
        )
        _write_model(tmp_path, model)
        pcfg = _make_pysui_config(profile_name="devnet", network_type=NetworkType.DEVELOP)
        cfg = PrivateFundsConfig(pysui_config=pcfg, from_cfg_path=str(tmp_path))
        override = tmp_path / "sub" / "override.json"
        cfg.save(path=override)
        assert override.exists()


# 7. Migration


class TestMigration:
    def test_backfills_well_known_network_types_and_bumps_version(self, tmp_path):
        _write_raw_v1_json(tmp_path)
        pcfg = _make_pysui_config(profile_name="devnet", network_type=NetworkType.DEVELOP)
        cfg = PrivateFundsConfig(pysui_config=pcfg, from_cfg_path=str(tmp_path))
        assert cfg._model.version == _CURRENT_PRIVATEFUNDS_CONFIG_VERSION
        by_name = {g.name: g for g in cfg._model.groups}
        assert by_name["devnet"].network_type == NetworkType.DEVELOP
        assert by_name["testnet"].network_type == NetworkType.TEST
        assert by_name["mainnet"].network_type == NetworkType.PRODUCTION

    def test_does_not_backfill_unknown_group_names(self, tmp_path):
        _write_raw_v1_json(tmp_path)
        pcfg = _make_pysui_config(profile_name="devnet", network_type=NetworkType.DEVELOP)
        cfg = PrivateFundsConfig(pysui_config=pcfg, from_cfg_path=str(tmp_path))
        by_name = {g.name: g for g in cfg._model.groups}
        assert by_name["custom"].network_type is None

    def test_migration_persists_to_disk(self, tmp_path):
        _write_raw_v1_json(tmp_path)
        pcfg = _make_pysui_config(profile_name="devnet", network_type=NetworkType.DEVELOP)
        PrivateFundsConfig(pysui_config=pcfg, from_cfg_path=str(tmp_path))
        on_disk = _PrivateFundsConfigModel.from_json(
            (tmp_path / "PrivateFundsConfig.json").read_text()
        )
        assert on_disk.version == _CURRENT_PRIVATEFUNDS_CONFIG_VERSION
        by_name = {g.name: g for g in on_disk.groups}
        assert by_name["devnet"].network_type == NetworkType.DEVELOP

    def test_no_migration_when_already_current_version(self, tmp_path):
        model = _PrivateFundsConfigModel(
            version=_CURRENT_PRIVATEFUNDS_CONFIG_VERSION,
            groups=[_valid_group("devnet", NetworkType.DEVELOP)],
        )
        _write_model(tmp_path, model)
        pcfg = _make_pysui_config(profile_name="devnet", network_type=NetworkType.DEVELOP)
        with patch.object(PrivateFundsConfig, "save", autospec=True) as mock_save:
            PrivateFundsConfig(pysui_config=pcfg, from_cfg_path=str(tmp_path))
            mock_save.assert_not_called()

    def test_does_not_overwrite_existing_network_type(self, tmp_path):
        raw = {
            "version": 1,
            "groups": [
                {
                    "name": "devnet",
                    "packageId": "0xaaaa",
                    "tokenRegistry": "0xbbbb",
                    "accountRegistry": "0xcccc",
                    "networkType": int(NetworkType.PRODUCTION),
                }
            ],
        }
        (tmp_path / "PrivateFundsConfig.json").write_text(json.dumps(raw, indent=2))
        pcfg = _make_pysui_config(profile_name="devnet", network_type=NetworkType.PRODUCTION)
        cfg = PrivateFundsConfig(pysui_config=pcfg, from_cfg_path=str(tmp_path))
        assert cfg._model.groups[0].network_type == NetworkType.PRODUCTION


# 8. add_group


class TestAddGroup:
    def test_add_group_requires_valid_network_type(self, tmp_path):
        model = _PrivateFundsConfigModel(
            version=_CURRENT_PRIVATEFUNDS_CONFIG_VERSION,
            groups=[_valid_group("devnet", NetworkType.DEVELOP)],
        )
        _write_model(tmp_path, model)
        pcfg = _make_pysui_config(profile_name="devnet", network_type=NetworkType.DEVELOP)
        cfg = PrivateFundsConfig(pysui_config=pcfg, from_cfg_path=str(tmp_path))
        with pytest.raises(ValueError, match="not a valid NetworkType"):
            cfg.add_group(
                name="testnet",
                network_type=None,
                package_id="0x1",
                token_registry="0x2",
                account_registry="0x3",
            )

    def test_add_group_creates_new_group(self, tmp_path):
        model = _PrivateFundsConfigModel(
            version=_CURRENT_PRIVATEFUNDS_CONFIG_VERSION,
            groups=[_valid_group("devnet", NetworkType.DEVELOP)],
        )
        _write_model(tmp_path, model)
        pcfg = _make_pysui_config(profile_name="devnet", network_type=NetworkType.DEVELOP)
        cfg = PrivateFundsConfig(pysui_config=pcfg, from_cfg_path=str(tmp_path))
        new_group = cfg.add_group(
            name="testnet",
            network_type=NetworkType.TEST,
            package_id="0x1",
            token_registry="0x2",
            account_registry="0x3",
        )
        assert new_group.name == "testnet"
        assert new_group.network_type == NetworkType.TEST
        assert any(g.name == "testnet" for g in cfg._model.groups)

    def test_add_group_rejects_duplicate_name(self, tmp_path):
        model = _PrivateFundsConfigModel(
            version=_CURRENT_PRIVATEFUNDS_CONFIG_VERSION,
            groups=[_valid_group("devnet", NetworkType.DEVELOP)],
        )
        _write_model(tmp_path, model)
        pcfg = _make_pysui_config(profile_name="devnet", network_type=NetworkType.DEVELOP)
        cfg = PrivateFundsConfig(pysui_config=pcfg, from_cfg_path=str(tmp_path))
        with pytest.raises(ValueError, match="already exists"):
            cfg.add_group(
                name="devnet",
                network_type=NetworkType.DEVELOP,
                package_id="0x1",
                token_registry="0x2",
                account_registry="0x3",
            )

    def test_add_group_persist_false_does_not_save(self, tmp_path):
        model = _PrivateFundsConfigModel(
            version=_CURRENT_PRIVATEFUNDS_CONFIG_VERSION,
            groups=[_valid_group("devnet", NetworkType.DEVELOP)],
        )
        _write_model(tmp_path, model)
        pcfg = _make_pysui_config(profile_name="devnet", network_type=NetworkType.DEVELOP)
        cfg = PrivateFundsConfig(pysui_config=pcfg, from_cfg_path=str(tmp_path))
        with patch.object(cfg, "save") as mock_save:
            cfg.add_group(
                name="testnet",
                network_type=NetworkType.TEST,
                package_id="0x1",
                token_registry="0x2",
                account_registry="0x3",
                persist=False,
            )
            mock_save.assert_not_called()

    def test_add_group_persist_true_saves(self, tmp_path):
        model = _PrivateFundsConfigModel(
            version=_CURRENT_PRIVATEFUNDS_CONFIG_VERSION,
            groups=[_valid_group("devnet", NetworkType.DEVELOP)],
        )
        _write_model(tmp_path, model)
        pcfg = _make_pysui_config(profile_name="devnet", network_type=NetworkType.DEVELOP)
        cfg = PrivateFundsConfig(pysui_config=pcfg, from_cfg_path=str(tmp_path))
        with patch.object(cfg, "save") as mock_save:
            cfg.add_group(
                name="testnet",
                network_type=NetworkType.TEST,
                package_id="0x1",
                token_registry="0x2",
                account_registry="0x3",
                persist=True,
            )
            mock_save.assert_called_once()


# 9. update_group


class TestUpdateGroup:
    def test_update_group_raises_if_not_found(self, tmp_path):
        model = _PrivateFundsConfigModel(
            version=_CURRENT_PRIVATEFUNDS_CONFIG_VERSION,
            groups=[_valid_group("devnet", NetworkType.DEVELOP)],
        )
        _write_model(tmp_path, model)
        pcfg = _make_pysui_config(profile_name="devnet", network_type=NetworkType.DEVELOP)
        cfg = PrivateFundsConfig(pysui_config=pcfg, from_cfg_path=str(tmp_path))
        with pytest.raises(ValueError, match="does not exist"):
            cfg.update_group(name="nowhere", network_type=NetworkType.TEST)

    def test_update_group_network_type_optional_leaves_unchanged(self, tmp_path):
        model = _PrivateFundsConfigModel(
            version=_CURRENT_PRIVATEFUNDS_CONFIG_VERSION,
            groups=[_valid_group("devnet", NetworkType.DEVELOP)],
        )
        _write_model(tmp_path, model)
        pcfg = _make_pysui_config(profile_name="devnet", network_type=NetworkType.DEVELOP)
        cfg = PrivateFundsConfig(pysui_config=pcfg, from_cfg_path=str(tmp_path))
        updated = cfg.update_group(name="devnet", package_id="0xnew")
        assert updated.network_type == NetworkType.DEVELOP
        assert updated.package_id == "0xnew"

    def test_update_group_network_type_provided_updates(self, tmp_path):
        model = _PrivateFundsConfigModel(
            version=_CURRENT_PRIVATEFUNDS_CONFIG_VERSION,
            groups=[
                _valid_group("devnet", NetworkType.DEVELOP),
                _valid_group("staging", NetworkType.TEST),
            ],
        )
        _write_model(tmp_path, model)
        pcfg = _make_pysui_config(profile_name="devnet", network_type=NetworkType.DEVELOP)
        cfg = PrivateFundsConfig(pysui_config=pcfg, from_cfg_path=str(tmp_path))
        updated = cfg.update_group(name="staging", network_type=NetworkType.PRODUCTION)
        assert updated.network_type == NetworkType.PRODUCTION

    def test_update_group_updates_only_specified_fields(self, tmp_path):
        model = _PrivateFundsConfigModel(
            version=_CURRENT_PRIVATEFUNDS_CONFIG_VERSION,
            groups=[
                _valid_group("devnet", NetworkType.DEVELOP),
                _valid_group("staging", NetworkType.TEST),
            ],
        )
        _write_model(tmp_path, model)
        pcfg = _make_pysui_config(profile_name="devnet", network_type=NetworkType.DEVELOP)
        cfg = PrivateFundsConfig(pysui_config=pcfg, from_cfg_path=str(tmp_path))
        original = next(g for g in cfg._model.groups if g.name == "staging")
        updated = cfg.update_group(name="staging", token_registry="0xchanged")
        assert updated.token_registry == "0xchanged"
        assert updated.package_id == original.package_id
        assert updated.account_registry == original.account_registry

    def test_update_group_persist_default_true_saves(self, tmp_path):
        model = _PrivateFundsConfigModel(
            version=_CURRENT_PRIVATEFUNDS_CONFIG_VERSION,
            groups=[
                _valid_group("devnet", NetworkType.DEVELOP),
                _valid_group("staging", NetworkType.TEST),
            ],
        )
        _write_model(tmp_path, model)
        pcfg = _make_pysui_config(profile_name="devnet", network_type=NetworkType.DEVELOP)
        cfg = PrivateFundsConfig(pysui_config=pcfg, from_cfg_path=str(tmp_path))
        with patch.object(cfg, "save") as mock_save:
            cfg.update_group(name="staging", package_id="0xchanged")
            mock_save.assert_called_once()

    def test_update_group_persist_false_does_not_save(self, tmp_path):
        model = _PrivateFundsConfigModel(
            version=_CURRENT_PRIVATEFUNDS_CONFIG_VERSION,
            groups=[
                _valid_group("devnet", NetworkType.DEVELOP),
                _valid_group("staging", NetworkType.TEST),
            ],
        )
        _write_model(tmp_path, model)
        pcfg = _make_pysui_config(profile_name="devnet", network_type=NetworkType.DEVELOP)
        cfg = PrivateFundsConfig(pysui_config=pcfg, from_cfg_path=str(tmp_path))
        with patch.object(cfg, "save") as mock_save:
            cfg.update_group(name="staging", package_id="0xchanged", persist=False)
            mock_save.assert_not_called()
