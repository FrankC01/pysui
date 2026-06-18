#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Unit tests for pysui.zklogin_seal.config."""

import json
import pathlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pysui.zklogin_seal.config import (
    ZkSealConfig,
    ZkSealNetworkGroup,
    ZkLoginProvider,
    SealKeyServer,
    SealKeyServerSet,
    _ZkSealConfigModel,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_PROVER_DEV = "https://prover-dev.mystenlabs.com/v1"
_PROVER_MAIN = "https://prover.mystenlabs.com/v1"
_DEFAULT_GROUPS = ["devnet", "testnet", "mainnet"]
_TESTNET_SETS = ["mysten-testnet", "mysten-testnet-committee"]
_TESTNET_OID_1 = "0x73d05d62c18d9374e3ea529e8e0ed6161da1a141a94d3f76ae3fe4e99356db75"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _init_cfg(tmp_path: pathlib.Path) -> ZkSealConfig:
    ZkSealConfig._initialize_config(from_cfg_path=str(tmp_path))
    return ZkSealConfig(from_cfg_path=str(tmp_path))


def _make_ok_result(url: str) -> MagicMock:
    result = MagicMock()
    result.is_ok.return_value = True
    field = MagicMock()
    field.field_object.json.to_dict.return_value = {"value": {"url": url}}
    result.result_data.dynamic_fields = [field]
    return result


def _make_error_result(error_msg: str) -> MagicMock:
    result = MagicMock()
    result.is_ok.return_value = False
    result.result_string = error_msg
    return result


def _make_empty_fields_result() -> MagicMock:
    result = MagicMock()
    result.is_ok.return_value = True
    result.result_data.dynamic_fields = []
    return result


def _make_none_field_result() -> MagicMock:
    result = MagicMock()
    result.is_ok.return_value = True
    field = MagicMock()
    field.field_object = None
    result.result_data.dynamic_fields = [field]
    return result


def _make_none_json_result() -> MagicMock:
    result = MagicMock()
    result.is_ok.return_value = True
    field = MagicMock()
    field.field_object.json = None
    result.result_data.dynamic_fields = [field]
    return result


def _make_no_value_result() -> MagicMock:
    result = MagicMock()
    result.is_ok.return_value = True
    field = MagicMock()
    field.field_object.json.to_dict.return_value = {}
    result.result_data.dynamic_fields = [field]
    return result


def _make_no_url_result() -> MagicMock:
    result = MagicMock()
    result.is_ok.return_value = True
    field = MagicMock()
    field.field_object.json.to_dict.return_value = {"value": {}}
    result.result_data.dynamic_fields = [field]
    return result


def _make_empty_url_result() -> MagicMock:
    result = MagicMock()
    result.is_ok.return_value = True
    field = MagicMock()
    field.field_object.json.to_dict.return_value = {"value": {"url": ""}}
    result.result_data.dynamic_fields = [field]
    return result


# ---------------------------------------------------------------------------
# 1. Dataclass serialization — camelCase JSON round-trip
# ---------------------------------------------------------------------------


class TestDataclassSerialization:

    def test_zklogin_provider_to_json_camelcase(self):
        p = ZkLoginProvider(name="google", iss="https://accounts.google.com", prover_url=_PROVER_DEV)
        d = json.loads(p.to_json())
        assert "proverUrl" in d
        assert "prover_url" not in d
        assert d["proverUrl"] == _PROVER_DEV

    def test_zklogin_provider_roundtrip(self):
        p = ZkLoginProvider(name="google", iss="https://accounts.google.com", prover_url=_PROVER_DEV)
        p2 = ZkLoginProvider.from_json(p.to_json())
        assert p2.name == p.name
        assert p2.iss == p.iss
        assert p2.prover_url == p.prover_url

    def test_seal_key_server_to_json_camelcase(self):
        s = SealKeyServer(alias="srv-1", object_id="0xabc", url="https://srv.example.com")
        d = json.loads(s.to_json())
        assert "objectId" in d
        assert "object_id" not in d
        assert d["objectId"] == "0xabc"

    def test_seal_key_server_roundtrip(self):
        s = SealKeyServer(alias="srv-1", object_id="0xabc", url="https://srv.example.com")
        s2 = SealKeyServer.from_json(s.to_json())
        assert s2.alias == s.alias
        assert s2.object_id == s.object_id
        assert s2.url == s.url

    def test_seal_key_server_set_to_json_camelcase(self):
        ss = SealKeyServerSet(name="my-set", is_committee=True)
        d = json.loads(ss.to_json())
        assert "isCommittee" in d
        assert "is_committee" not in d
        assert d["isCommittee"] is True

    def test_seal_key_server_set_servers_default_empty(self):
        ss = SealKeyServerSet(name="my-set", is_committee=False)
        assert ss.servers == []

    def test_zkseal_network_group_to_json_camelcase(self):
        g = ZkSealNetworkGroup(group_name="testnet")
        d = json.loads(g.to_json())
        assert "groupName" in d
        assert "group_name" not in d
        assert d["groupName"] == "testnet"

    def test_zkseal_network_group_roundtrip(self):
        g = ZkSealNetworkGroup(
            group_name="testnet",
            zklogin_providers=[ZkLoginProvider("google", "https://accounts.google.com", _PROVER_DEV)],
        )
        g2 = ZkSealNetworkGroup.from_json(g.to_json())
        assert g2.group_name == "testnet"
        assert len(g2.zklogin_providers) == 1
        assert g2.zklogin_providers[0].name == "google"

    def test_model_version_field(self):
        m = _ZkSealConfigModel()
        d = json.loads(m.to_json())
        assert d["version"] == 1

    def test_model_roundtrip_with_groups(self):
        m = _ZkSealConfigModel(groups=[ZkSealNetworkGroup(group_name="devnet")])
        m2 = _ZkSealConfigModel.from_json(m.to_json())
        assert len(m2.groups) == 1
        assert m2.groups[0].group_name == "devnet"


# ---------------------------------------------------------------------------
# 2. _initialize_config
# ---------------------------------------------------------------------------


class TestInitializeConfig:

    def test_creates_file(self, tmp_path):
        ZkSealConfig._initialize_config(from_cfg_path=str(tmp_path))
        assert (tmp_path / "ZkSealConfig.json").exists()

    def test_creates_parent_dirs(self, tmp_path):
        nested = tmp_path / "a" / "b" / "c"
        ZkSealConfig._initialize_config(from_cfg_path=str(nested))
        assert (nested / "ZkSealConfig.json").exists()

    def test_creates_three_groups(self, tmp_path):
        ZkSealConfig._initialize_config(from_cfg_path=str(tmp_path))
        data = json.loads((tmp_path / "ZkSealConfig.json").read_text())
        assert [g["groupName"] for g in data["groups"]] == _DEFAULT_GROUPS

    def test_devnet_has_three_providers_no_sets(self, tmp_path):
        ZkSealConfig._initialize_config(from_cfg_path=str(tmp_path))
        data = json.loads((tmp_path / "ZkSealConfig.json").read_text())
        devnet = next(g for g in data["groups"] if g["groupName"] == "devnet")
        assert len(devnet["zkloginProviders"]) == 3
        assert devnet["keyServerSets"] == []

    def test_testnet_has_two_sets(self, tmp_path):
        ZkSealConfig._initialize_config(from_cfg_path=str(tmp_path))
        data = json.loads((tmp_path / "ZkSealConfig.json").read_text())
        testnet = next(g for g in data["groups"] if g["groupName"] == "testnet")
        assert [s["name"] for s in testnet["keyServerSets"]] == _TESTNET_SETS

    def test_testnet_mysten_testnet_has_two_servers_not_committee(self, tmp_path):
        ZkSealConfig._initialize_config(from_cfg_path=str(tmp_path))
        data = json.loads((tmp_path / "ZkSealConfig.json").read_text())
        testnet = next(g for g in data["groups"] if g["groupName"] == "testnet")
        s = next(s for s in testnet["keyServerSets"] if s["name"] == "mysten-testnet")
        assert len(s["servers"]) == 2
        assert s["isCommittee"] is False

    def test_testnet_committee_has_one_server_is_committee(self, tmp_path):
        ZkSealConfig._initialize_config(from_cfg_path=str(tmp_path))
        data = json.loads((tmp_path / "ZkSealConfig.json").read_text())
        testnet = next(g for g in data["groups"] if g["groupName"] == "testnet")
        s = next(s for s in testnet["keyServerSets"] if s["name"] == "mysten-testnet-committee")
        assert len(s["servers"]) == 1
        assert s["isCommittee"] is True

    def test_mainnet_prover_url_differs_from_devnet(self, tmp_path):
        ZkSealConfig._initialize_config(from_cfg_path=str(tmp_path))
        data = json.loads((tmp_path / "ZkSealConfig.json").read_text())
        mainnet = next(g for g in data["groups"] if g["groupName"] == "mainnet")
        for p in mainnet["zkloginProviders"]:
            assert p["proverUrl"] == _PROVER_MAIN

    def test_devnet_prover_url_is_dev(self, tmp_path):
        ZkSealConfig._initialize_config(from_cfg_path=str(tmp_path))
        data = json.loads((tmp_path / "ZkSealConfig.json").read_text())
        devnet = next(g for g in data["groups"] if g["groupName"] == "devnet")
        for p in devnet["zkloginProviders"]:
            assert p["proverUrl"] == _PROVER_DEV

    def test_raises_if_file_already_exists(self, tmp_path):
        ZkSealConfig._initialize_config(from_cfg_path=str(tmp_path))
        with pytest.raises(ValueError, match="already exists"):
            ZkSealConfig._initialize_config(from_cfg_path=str(tmp_path))

    def test_version_is_1(self, tmp_path):
        ZkSealConfig._initialize_config(from_cfg_path=str(tmp_path))
        data = json.loads((tmp_path / "ZkSealConfig.json").read_text())
        assert data["version"] == 1

    def test_json_uses_camelcase_keys(self, tmp_path):
        ZkSealConfig._initialize_config(from_cfg_path=str(tmp_path))
        data = json.loads((tmp_path / "ZkSealConfig.json").read_text())
        assert "groupName" in data["groups"][0]
        assert "group_name" not in data["groups"][0]


# ---------------------------------------------------------------------------
# 3. ZkSealConfig.__init__
# ---------------------------------------------------------------------------


class TestInit:

    def test_loads_existing_file(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        assert len(cfg._model.groups) == 3

    def test_raises_if_custom_path_and_no_file(self, tmp_path):
        with pytest.raises(ValueError):
            ZkSealConfig(from_cfg_path=str(tmp_path))

    def test_activates_named_group(self, tmp_path):
        ZkSealConfig._initialize_config(from_cfg_path=str(tmp_path))
        cfg = ZkSealConfig(from_cfg_path=str(tmp_path), group_name="testnet")
        assert cfg.active_group.group_name == "testnet"

    def test_activates_first_group_by_default(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        assert cfg.active_group.group_name == "testnet"

    def test_raises_on_unknown_group_name(self, tmp_path):
        ZkSealConfig._initialize_config(from_cfg_path=str(tmp_path))
        with pytest.raises(ValueError, match="not found"):
            ZkSealConfig(from_cfg_path=str(tmp_path), group_name="nonexistent")

    def test_persist_false_does_not_save(self, tmp_path):
        ZkSealConfig._initialize_config(from_cfg_path=str(tmp_path))
        with patch.object(ZkSealConfig, "save") as mock_save:
            ZkSealConfig(from_cfg_path=str(tmp_path), persist=False)
            mock_save.assert_not_called()

    def test_default_path_static_method(self):
        p = ZkSealConfig.default_path()
        assert p == pathlib.Path.home() / ".pysui" / "ZkSealConfig.json"


# ---------------------------------------------------------------------------
# 4. save
# ---------------------------------------------------------------------------


class TestSave:

    def test_save_writes_to_config_file(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        cfg.add_group(group_name="stagenet")
        cfg.save()
        data = json.loads((tmp_path / "ZkSealConfig.json").read_text())
        assert any(g["groupName"] == "stagenet" for g in data["groups"])

    def test_save_to_custom_path(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        alt = tmp_path / "alt" / "config.json"
        cfg.save(path=alt)
        assert alt.exists()

    def test_save_creates_parent_dirs(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        deep = tmp_path / "x" / "y" / "z" / "ZkSealConfig.json"
        cfg.save(path=deep)
        assert deep.exists()


# ---------------------------------------------------------------------------
# 5. active_group property
# ---------------------------------------------------------------------------


class TestActiveGroup:

    def test_returns_first_group_lazily(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        cfg._active_group = None
        assert cfg.active_group.group_name == "devnet"

    def test_returns_set_group(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        cfg.make_active(group_name="mainnet")
        assert cfg.active_group.group_name == "mainnet"

    def test_raises_runtime_error_when_no_groups(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        cfg._model.groups = []
        cfg._active_group = None
        with pytest.raises(RuntimeError, match="No groups configured"):
            _ = cfg.active_group


# ---------------------------------------------------------------------------
# 6. make_active
# ---------------------------------------------------------------------------


class TestMakeActive:

    def test_sets_group_by_name(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        cfg.make_active(group_name="testnet")
        assert cfg.active_group.group_name == "testnet"

    def test_returns_self_for_chaining(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        result = cfg.make_active(group_name="mainnet")
        assert result is cfg

    def test_raises_on_unknown_group(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        with pytest.raises(ValueError, match="not found"):
            cfg.make_active(group_name="doesnotexist")

    def test_none_group_name_keeps_existing_active(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        cfg.make_active(group_name="testnet")
        cfg.make_active(group_name=None)
        assert cfg.active_group.group_name == "testnet"

    def test_none_group_name_sets_first_when_none_active(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        cfg._active_group = None
        cfg.make_active(group_name=None)
        assert cfg.active_group.group_name == "testnet"

    def test_persist_true_saves(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        with patch.object(cfg, "save") as mock_save:
            cfg.make_active(group_name="testnet", persist=True)
            mock_save.assert_called_once()

    def test_persist_false_does_not_save(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        with patch.object(cfg, "save") as mock_save:
            cfg.make_active(group_name="testnet", persist=False)
            mock_save.assert_not_called()


# ---------------------------------------------------------------------------
# 7. Group CRUD
# ---------------------------------------------------------------------------


class TestGroupCrud:

    def test_add_group_returns_group(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        g = cfg.add_group(group_name="stagenet")
        assert isinstance(g, ZkSealNetworkGroup)
        assert g.group_name == "stagenet"

    def test_add_group_appends_to_model(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        cfg.add_group(group_name="stagenet")
        assert any(g.group_name == "stagenet" for g in cfg._model.groups)

    def test_add_group_starts_empty(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        g = cfg.add_group(group_name="stagenet")
        assert g.zklogin_providers == []
        assert g.key_server_sets == []

    def test_add_group_duplicate_raises(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        with pytest.raises(ValueError, match="already exists"):
            cfg.add_group(group_name="devnet")

    def test_add_group_persist_false_no_save(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        with patch.object(cfg, "save") as mock_save:
            cfg.add_group(group_name="stagenet", persist=False)
            mock_save.assert_not_called()

    def test_add_group_persist_true_saves(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        with patch.object(cfg, "save") as mock_save:
            cfg.add_group(group_name="stagenet", persist=True)
            mock_save.assert_called_once()

    def test_remove_group_removes_it(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        cfg.remove_group(group_name="devnet")
        assert not any(g.group_name == "devnet" for g in cfg._model.groups)

    def test_remove_group_clears_active_if_removed(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        cfg.make_active(group_name="devnet")
        cfg.remove_group(group_name="devnet")
        assert cfg._active_group is None

    def test_remove_group_does_not_clear_other_active(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        cfg.make_active(group_name="testnet")
        cfg.remove_group(group_name="devnet")
        assert cfg._active_group.group_name == "testnet"

    def test_remove_group_nonexistent_silently_passes(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        cfg.remove_group(group_name="nonexistent")
        assert len(cfg._model.groups) == 3

    def test_remove_group_persist_saves(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        with patch.object(cfg, "save") as mock_save:
            cfg.remove_group(group_name="devnet", persist=True)
            mock_save.assert_called_once()

    def test_get_group_returns_group(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        g = cfg._get_group("testnet")
        assert g.group_name == "testnet"

    def test_get_group_raises_on_miss(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        with pytest.raises(ValueError, match="not found"):
            cfg._get_group("nonexistent")


# ---------------------------------------------------------------------------
# 8. Provider CRUD
# ---------------------------------------------------------------------------


class TestProviderCrud:

    def test_add_provider(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        cfg.add_group(group_name="stagenet")
        cfg.add_provider(
            group_name="stagenet", name="apple",
            iss="https://appleid.apple.com", prover_url=_PROVER_DEV
        )
        group = cfg._get_group("stagenet")
        assert any(p.name == "apple" for p in group.zklogin_providers)

    def test_add_provider_stores_correct_fields(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        cfg.add_group(group_name="stagenet")
        cfg.add_provider(
            group_name="stagenet", name="apple",
            iss="https://appleid.apple.com", prover_url=_PROVER_DEV
        )
        p = next(p for p in cfg._get_group("stagenet").zklogin_providers if p.name == "apple")
        assert p.iss == "https://appleid.apple.com"
        assert p.prover_url == _PROVER_DEV

    def test_add_provider_duplicate_raises(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        with pytest.raises(ValueError, match="already exists"):
            cfg.add_provider(group_name="devnet", name="google", iss="x", prover_url="y")

    def test_add_provider_unknown_group_raises(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        with pytest.raises(ValueError, match="not found"):
            cfg.add_provider(group_name="nonexistent", name="google", iss="x", prover_url="y")

    def test_add_provider_persist_false_no_save(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        cfg.add_group(group_name="stagenet")
        with patch.object(cfg, "save") as mock_save:
            cfg.add_provider(
                group_name="stagenet", name="apple",
                iss="x", prover_url="y", persist=False
            )
            mock_save.assert_not_called()

    def test_remove_provider_removes_it(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        cfg.remove_provider(group_name="devnet", name="google")
        group = cfg._get_group("devnet")
        assert not any(p.name == "google" for p in group.zklogin_providers)

    def test_remove_provider_nonexistent_silently_passes(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        count_before = len(cfg._get_group("devnet").zklogin_providers)
        cfg.remove_provider(group_name="devnet", name="nonexistent")
        assert len(cfg._get_group("devnet").zklogin_providers) == count_before

    def test_update_provider_url(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        new_url = "https://custom-prover.example.com/v1"
        cfg.update_provider_url(group_name="devnet", name="google", prover_url=new_url)
        p = next(p for p in cfg._get_group("devnet").zklogin_providers if p.name == "google")
        assert p.prover_url == new_url

    def test_update_provider_url_unknown_name_raises(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        with pytest.raises(ValueError, match="not found"):
            cfg.update_provider_url(group_name="devnet", name="nonexistent", prover_url="x")

    def test_update_provider_url_does_not_change_iss(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        p = next(p for p in cfg._get_group("devnet").zklogin_providers if p.name == "google")
        iss_before = p.iss
        cfg.update_provider_url(group_name="devnet", name="google", prover_url="https://new.prover/v1")
        assert p.iss == iss_before

    def test_update_provider_url_persist_saves(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        with patch.object(cfg, "save") as mock_save:
            cfg.update_provider_url(
                group_name="devnet", name="google", prover_url="x", persist=True
            )
            mock_save.assert_called_once()


# ---------------------------------------------------------------------------
# 9. Key server set CRUD
# ---------------------------------------------------------------------------


class TestServerSetCrud:

    def test_add_key_server_set(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        cfg.add_key_server_set(group_name="devnet", set_name="my-set", is_committee=False)
        assert "my-set" in cfg.list_sets(group_name="devnet")

    def test_add_key_server_set_committee_flag(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        cfg.add_key_server_set(group_name="devnet", set_name="committee-set", is_committee=True)
        ss = cfg._get_server_set("devnet", "committee-set")
        assert ss.is_committee is True

    def test_add_key_server_set_starts_empty(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        cfg.add_key_server_set(group_name="devnet", set_name="my-set", is_committee=False)
        ss = cfg._get_server_set("devnet", "my-set")
        assert ss.servers == []

    def test_add_key_server_set_duplicate_raises(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        with pytest.raises(ValueError, match="already exists"):
            cfg.add_key_server_set(
                group_name="testnet", set_name="mysten-testnet", is_committee=False
            )

    def test_add_key_server_set_unknown_group_raises(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        with pytest.raises(ValueError, match="not found"):
            cfg.add_key_server_set(group_name="nonexistent", set_name="my-set", is_committee=False)

    def test_add_key_server_set_persist_false_no_save(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        with patch.object(cfg, "save") as mock_save:
            cfg.add_key_server_set(
                group_name="devnet", set_name="my-set", is_committee=False, persist=False
            )
            mock_save.assert_not_called()

    def test_remove_key_server_set(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        cfg.remove_key_server_set(group_name="testnet", set_name="mysten-testnet")
        assert "mysten-testnet" not in cfg.list_sets(group_name="testnet")

    def test_remove_key_server_set_nonexistent_silently_passes(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        sets_before = cfg.list_sets(group_name="testnet")
        cfg.remove_key_server_set(group_name="testnet", set_name="nonexistent")
        assert cfg.list_sets(group_name="testnet") == sets_before

    def test_list_sets_returns_names(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        assert cfg.list_sets(group_name="testnet") == _TESTNET_SETS

    def test_list_sets_empty_group(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        assert cfg.list_sets(group_name="devnet") == []

    def test_get_server_set_raises_on_unknown_set(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        with pytest.raises(ValueError, match="not found"):
            cfg._get_server_set("testnet", "nonexistent-set")


# ---------------------------------------------------------------------------
# 10. Key server CRUD
# ---------------------------------------------------------------------------


class TestServerCrud:

    def test_add_server(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        cfg.add_server(
            group_name="testnet", set_name="mysten-testnet",
            alias="new-srv", object_id="0xdeadbeef", url="https://new.srv.com"
        )
        s = cfg.get_server(group_name="testnet", set_name="mysten-testnet", alias="new-srv")
        assert s is not None
        assert s.object_id == "0xdeadbeef"
        assert s.url == "https://new.srv.com"

    def test_add_server_duplicate_alias_raises(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        with pytest.raises(ValueError, match="already exists"):
            cfg.add_server(
                group_name="testnet", set_name="mysten-testnet",
                alias="mysten-testnet-1", object_id="0x0", url="x"
            )

    def test_add_server_unknown_group_raises(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        with pytest.raises(ValueError, match="not found"):
            cfg.add_server(
                group_name="nonexistent", set_name="mysten-testnet",
                alias="srv", object_id="0x0", url="x"
            )

    def test_add_server_unknown_set_raises(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        with pytest.raises(ValueError, match="not found"):
            cfg.add_server(
                group_name="testnet", set_name="nonexistent-set",
                alias="srv", object_id="0x0", url="x"
            )

    def test_add_server_persist_false_no_save(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        with patch.object(cfg, "save") as mock_save:
            cfg.add_server(
                group_name="testnet", set_name="mysten-testnet",
                alias="new-srv", object_id="0x0", url="x", persist=False
            )
            mock_save.assert_not_called()

    def test_remove_server(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        cfg.remove_server(
            group_name="testnet", set_name="mysten-testnet", alias="mysten-testnet-1"
        )
        s = cfg.get_server(
            group_name="testnet", set_name="mysten-testnet", alias="mysten-testnet-1"
        )
        assert s is None

    def test_remove_server_nonexistent_silently_passes(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        ss = cfg._get_server_set("testnet", "mysten-testnet")
        count_before = len(ss.servers)
        cfg.remove_server(group_name="testnet", set_name="mysten-testnet", alias="nonexistent")
        assert len(ss.servers) == count_before

    def test_update_server_url(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        new_url = "https://updated.server.com"
        cfg.update_server_url(
            group_name="testnet", set_name="mysten-testnet",
            alias="mysten-testnet-1", url=new_url
        )
        s = cfg.get_server(
            group_name="testnet", set_name="mysten-testnet", alias="mysten-testnet-1"
        )
        assert s.url == new_url

    def test_update_server_url_unknown_alias_raises(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        with pytest.raises(ValueError, match="not found"):
            cfg.update_server_url(
                group_name="testnet", set_name="mysten-testnet",
                alias="nonexistent", url="x"
            )

    def test_update_server_url_persist_saves(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        with patch.object(cfg, "save") as mock_save:
            cfg.update_server_url(
                group_name="testnet", set_name="mysten-testnet",
                alias="mysten-testnet-1", url="x", persist=True
            )
            mock_save.assert_called_once()

    def test_get_server_returns_none_on_miss(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        s = cfg.get_server(
            group_name="testnet", set_name="mysten-testnet", alias="nonexistent"
        )
        assert s is None

    def test_get_server_returns_none_on_bad_group(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        s = cfg.get_server(group_name="nonexistent", set_name="mysten-testnet", alias="any")
        assert s is None

    def test_get_server_returns_none_on_bad_set(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        s = cfg.get_server(group_name="testnet", set_name="nonexistent-set", alias="any")
        assert s is None

    def test_resolve_server_by_alias(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        s = cfg.resolve_server(
            group_name="testnet", set_name="mysten-testnet",
            alias_or_object_id="mysten-testnet-1"
        )
        assert s is not None
        assert s.alias == "mysten-testnet-1"

    def test_resolve_server_by_object_id(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        s = cfg.resolve_server(
            group_name="testnet", set_name="mysten-testnet",
            alias_or_object_id=_TESTNET_OID_1
        )
        assert s is not None
        assert s.alias == "mysten-testnet-1"

    def test_resolve_server_returns_none_on_miss(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        s = cfg.resolve_server(
            group_name="testnet", set_name="mysten-testnet", alias_or_object_id="unknown"
        )
        assert s is None

    def test_resolve_server_returns_none_on_bad_group(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        s = cfg.resolve_server(
            group_name="nonexistent", set_name="mysten-testnet", alias_or_object_id="any"
        )
        assert s is None


# ---------------------------------------------------------------------------
# 11. _fetch_server_url
# ---------------------------------------------------------------------------


class TestFetchServerUrl:

    @pytest.mark.asyncio
    async def test_happy_path_returns_url(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        client = AsyncMock()
        client.execute.return_value = _make_ok_result("https://test.server.com")
        url = await cfg._fetch_server_url(object_id="0xabc", client=client)
        assert url == "https://test.server.com"

    @pytest.mark.asyncio
    async def test_calls_execute_once(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        client = AsyncMock()
        client.execute.return_value = _make_ok_result("https://test.server.com")
        await cfg._fetch_server_url(object_id="0xabc", client=client)
        client.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_raises_when_result_not_ok(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        client = AsyncMock()
        client.execute.return_value = _make_error_result("RPC error occurred")
        with pytest.raises(ValueError, match="RPC error occurred"):
            await cfg._fetch_server_url(object_id="0xabc", client=client)

    @pytest.mark.asyncio
    async def test_raises_on_empty_dynamic_fields(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        client = AsyncMock()
        client.execute.return_value = _make_empty_fields_result()
        with pytest.raises(ValueError, match="No dynamic fields"):
            await cfg._fetch_server_url(object_id="0xabc", client=client)

    @pytest.mark.asyncio
    async def test_raises_when_field_object_is_none(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        client = AsyncMock()
        client.execute.return_value = _make_none_field_result()
        with pytest.raises(ValueError, match="no JSON value"):
            await cfg._fetch_server_url(object_id="0xabc", client=client)

    @pytest.mark.asyncio
    async def test_raises_when_field_json_is_none(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        client = AsyncMock()
        client.execute.return_value = _make_none_json_result()
        with pytest.raises(ValueError, match="no JSON value"):
            await cfg._fetch_server_url(object_id="0xabc", client=client)

    @pytest.mark.asyncio
    async def test_raises_when_no_value_key(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        client = AsyncMock()
        client.execute.return_value = _make_no_value_result()
        with pytest.raises(ValueError, match="Could not extract URL"):
            await cfg._fetch_server_url(object_id="0xabc", client=client)

    @pytest.mark.asyncio
    async def test_raises_when_no_url_in_value(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        client = AsyncMock()
        client.execute.return_value = _make_no_url_result()
        with pytest.raises(ValueError, match="Could not extract URL"):
            await cfg._fetch_server_url(object_id="0xabc", client=client)

    @pytest.mark.asyncio
    async def test_raises_on_empty_url_string(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        client = AsyncMock()
        client.execute.return_value = _make_empty_url_result()
        with pytest.raises(ValueError, match="Could not extract URL"):
            await cfg._fetch_server_url(object_id="0xabc", client=client)

    @pytest.mark.asyncio
    async def test_object_id_in_error_message(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        client = AsyncMock()
        client.execute.return_value = _make_empty_fields_result()
        with pytest.raises(ValueError, match="0xspecific"):
            await cfg._fetch_server_url(object_id="0xspecific", client=client)


# ---------------------------------------------------------------------------
# 12. add_verified_server
# ---------------------------------------------------------------------------


class TestAddVerifiedServer:

    @pytest.mark.asyncio
    async def test_adds_server_with_url_from_chain(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        client = AsyncMock()
        client.execute.return_value = _make_ok_result("https://fetched.url.com")
        await cfg.add_verified_server(
            group_name="testnet", set_name="mysten-testnet",
            alias="new-verified", object_id="0xnew", client=client
        )
        s = cfg.get_server(group_name="testnet", set_name="mysten-testnet", alias="new-verified")
        assert s is not None
        assert s.url == "https://fetched.url.com"
        assert s.object_id == "0xnew"

    @pytest.mark.asyncio
    async def test_always_saves(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        client = AsyncMock()
        client.execute.return_value = _make_ok_result("https://fetched.url.com")
        with patch.object(cfg, "save") as mock_save:
            await cfg.add_verified_server(
                group_name="testnet", set_name="mysten-testnet",
                alias="new-verified", object_id="0xnew", client=client
            )
            mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_propagates_fetch_error(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        client = AsyncMock()
        client.execute.return_value = _make_error_result("chain error")
        with pytest.raises(ValueError, match="chain error"):
            await cfg.add_verified_server(
                group_name="testnet", set_name="mysten-testnet",
                alias="srv", object_id="0xabc", client=client
            )

    @pytest.mark.asyncio
    async def test_does_not_save_on_fetch_error(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        client = AsyncMock()
        client.execute.return_value = _make_error_result("chain error")
        with patch.object(cfg, "save") as mock_save:
            with pytest.raises(ValueError):
                await cfg.add_verified_server(
                    group_name="testnet", set_name="mysten-testnet",
                    alias="srv", object_id="0xabc", client=client
                )
            mock_save.assert_not_called()


# ---------------------------------------------------------------------------
# 13. refresh_server_url
# ---------------------------------------------------------------------------


class TestRefreshServerUrl:

    @pytest.mark.asyncio
    async def test_updates_server_url(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        client = AsyncMock()
        client.execute.return_value = _make_ok_result("https://refreshed.url.com")
        await cfg.refresh_server_url(
            group_name="testnet", set_name="mysten-testnet",
            alias="mysten-testnet-1", client=client
        )
        s = cfg.get_server(
            group_name="testnet", set_name="mysten-testnet", alias="mysten-testnet-1"
        )
        assert s.url == "https://refreshed.url.com"

    @pytest.mark.asyncio
    async def test_always_saves(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        client = AsyncMock()
        client.execute.return_value = _make_ok_result("https://refreshed.url.com")
        with patch.object(cfg, "save") as mock_save:
            await cfg.refresh_server_url(
                group_name="testnet", set_name="mysten-testnet",
                alias="mysten-testnet-1", client=client
            )
            mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_on_unknown_alias(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        client = AsyncMock()
        with pytest.raises(ValueError, match="not found"):
            await cfg.refresh_server_url(
                group_name="testnet", set_name="mysten-testnet",
                alias="nonexistent", client=client
            )

    @pytest.mark.asyncio
    async def test_only_updates_targeted_server(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        s2_url_before = cfg.get_server(
            group_name="testnet", set_name="mysten-testnet", alias="mysten-testnet-2"
        ).url
        client = AsyncMock()
        client.execute.return_value = _make_ok_result("https://refreshed.url.com")
        await cfg.refresh_server_url(
            group_name="testnet", set_name="mysten-testnet",
            alias="mysten-testnet-1", client=client
        )
        s2_url_after = cfg.get_server(
            group_name="testnet", set_name="mysten-testnet", alias="mysten-testnet-2"
        ).url
        assert s2_url_after == s2_url_before

    @pytest.mark.asyncio
    async def test_does_not_save_on_fetch_error(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        client = AsyncMock()
        client.execute.return_value = _make_error_result("network failure")
        with patch.object(cfg, "save") as mock_save:
            with pytest.raises(ValueError):
                await cfg.refresh_server_url(
                    group_name="testnet", set_name="mysten-testnet",
                    alias="mysten-testnet-1", client=client
                )
            mock_save.assert_not_called()


# ---------------------------------------------------------------------------
# 14. refresh_all_server_urls
# ---------------------------------------------------------------------------


class TestRefreshAllServerUrls:

    @pytest.mark.asyncio
    async def test_updates_all_servers_across_all_groups(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        client = AsyncMock()
        client.execute.return_value = _make_ok_result("https://new.url.com")
        await cfg.refresh_all_server_urls(client=client)
        for group in cfg._model.groups:
            for ss in group.key_server_sets:
                if ss.is_committee:
                    continue
                for srv in ss.servers:
                    assert srv.url == "https://new.url.com"

    @pytest.mark.asyncio
    async def test_saves_exactly_once(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        client = AsyncMock()
        client.execute.return_value = _make_ok_result("https://new.url.com")
        with patch.object(cfg, "save") as mock_save:
            await cfg.refresh_all_server_urls(client=client)
            mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_calls_execute_once_per_server(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        client = AsyncMock()
        client.execute.return_value = _make_ok_result("https://new.url.com")
        total_servers = sum(
            len(ss.servers)
            for g in cfg._model.groups
            for ss in g.key_server_sets
            if not ss.is_committee
        )
        await cfg.refresh_all_server_urls(client=client)
        assert client.execute.await_count == total_servers

    @pytest.mark.asyncio
    async def test_does_not_touch_prover_urls(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        prover_urls_before = {
            (g.group_name, p.name): p.prover_url
            for g in cfg._model.groups
            for p in g.zklogin_providers
        }
        client = AsyncMock()
        client.execute.return_value = _make_ok_result("https://new.url.com")
        await cfg.refresh_all_server_urls(client=client)
        for g in cfg._model.groups:
            for p in g.zklogin_providers:
                assert p.prover_url == prover_urls_before[(g.group_name, p.name)]

    @pytest.mark.asyncio
    async def test_saves_even_when_no_servers(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        cfg._model.groups = [ZkSealNetworkGroup(group_name="empty")]
        client = AsyncMock()
        with patch.object(cfg, "save") as mock_save:
            await cfg.refresh_all_server_urls(client=client)
            client.execute.assert_not_awaited()
            mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_on_transport_error(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        client = AsyncMock()
        client.execute.return_value = _make_error_result("transport failure")
        with patch.object(cfg, "save") as mock_save:
            with pytest.raises(ValueError, match="transport failure"):
                await cfg.refresh_all_server_urls(client=client)
            mock_save.assert_not_called()

    @pytest.mark.asyncio
    async def test_partial_update_aborts_on_first_error(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        client = AsyncMock()
        client.execute.side_effect = [
            _make_ok_result("https://updated.url.com"),
            _make_error_result("server down"),
        ]
        with patch.object(cfg, "save") as mock_save:
            with pytest.raises(ValueError, match="server down"):
                await cfg.refresh_all_server_urls(client=client)
        # First server updated in memory
        first_server = cfg._get_server_set("testnet", "mysten-testnet").servers[0]
        assert first_server.url == "https://updated.url.com"
        # Second server unchanged
        second_server = cfg._get_server_set("testnet", "mysten-testnet").servers[1]
        assert second_server.url != "https://updated.url.com"
        # Save never called
        mock_save.assert_not_called()


# ---------------------------------------------------------------------------
# 15. Round-trip persistence
# ---------------------------------------------------------------------------


class TestRoundTrip:

    def test_add_group_save_reload(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        cfg.add_group(group_name="stagenet")
        cfg.save()
        cfg2 = ZkSealConfig(from_cfg_path=str(tmp_path))
        assert any(g.group_name == "stagenet" for g in cfg2._model.groups)

    def test_add_server_save_reload(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        cfg.add_server(
            group_name="testnet", set_name="mysten-testnet",
            alias="persisted-srv", object_id="0xabc", url="https://persisted.srv.com"
        )
        cfg.save()
        cfg2 = ZkSealConfig(from_cfg_path=str(tmp_path))
        s = cfg2.get_server(
            group_name="testnet", set_name="mysten-testnet", alias="persisted-srv"
        )
        assert s is not None
        assert s.url == "https://persisted.srv.com"

    def test_camelcase_preserved_in_json_file(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        cfg.save()
        raw = json.loads((tmp_path / "ZkSealConfig.json").read_text())
        assert "groupName" in raw["groups"][0]
        assert "group_name" not in raw["groups"][0]

    def test_removed_group_absent_after_reload(self, tmp_path):
        cfg = _init_cfg(tmp_path)
        cfg.remove_group(group_name="devnet")
        cfg.save()
        cfg2 = ZkSealConfig(from_cfg_path=str(tmp_path))
        assert not any(g.group_name == "devnet" for g in cfg2._model.groups)
