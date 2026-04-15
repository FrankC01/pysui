#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Unit tests for PysuiConfiguration and ProfileGroup.

All tests are offline — no Sui node, no Sui CLI binaries required.
Uses tmp_path for filesystem isolation; keys are generated in-process.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from pysui import PysuiConfiguration
from pysui.abstracts.client_keypair import SignatureScheme
from pysui.sui.sui_common.config.confgroup import (
    GroupProtocol,
    ProfileGroup,
    Profile,
    ProfileAlias,
    ProfileKey,
    SUI_GQL_RPC_GROUP,
    SUI_GRPC_GROUP,
    SUI_JSON_RPC_GROUP,
    SUI_USER_GROUP,
)
import pysui.sui.sui_crypto as crypto


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _gen_key_string() -> str:
    """Generate a fresh serialized private key string (no Sui CLI needed)."""
    _, keypair = crypto.create_new_keypair(scheme=SignatureScheme.ED25519)
    return keypair.serialize()


def _make_minimal_group(
    name: str, protocol: GroupProtocol = GroupProtocol.OTHER
) -> tuple[ProfileGroup, str, str]:
    """Return a ProfileGroup with one keypair and one profile, plus address and alias."""
    _mnem, address, prf_key, prf_alias = ProfileGroup.new_keypair_parts(
        of_keytype=SignatureScheme.ED25519,
        alias_list=[],
    )
    group = ProfileGroup(
        name,
        "testnet",
        address,
        [prf_alias],
        [prf_key],
        [address],
        [Profile("testnet", "https://example.com")],
        protocol,
    )
    return group, address, prf_alias.alias


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def cfg_dir(tmp_path):
    """Minimal PysuiConfiguration in a temp dir.

    Returns (tmp_path, cfg) with one keypair and one profile already added.
    """
    cfg = PysuiConfiguration.initialize_config(
        in_folder=tmp_path,
        init_groups=[{"name": SUI_GQL_RPC_GROUP, "make_active": True}],
    )
    cfg.new_keypair(
        of_keytype=SignatureScheme.ED25519,
        make_active=True,
        alias="pri-mary",
        persist=True,
    )
    cfg.new_profile(
        profile_name="testnet",
        url="https://graphql.testnet.sui.io/graphql",
        make_active=True,
        persist=True,
    )
    return tmp_path, cfg


# ---------------------------------------------------------------------------
# ProfileGroup — __post_init__ protocol assignment
# ---------------------------------------------------------------------------


class TestProfileGroupProtocol:
    def test_standard_gql_name_assigns_graphql(self):
        group = ProfileGroup(SUI_GQL_RPC_GROUP, "", "", [], [], [], [])
        assert group.protocol == GroupProtocol.GRAPHQL

    def test_standard_grpc_name_assigns_grpc(self):
        group = ProfileGroup(SUI_GRPC_GROUP, "", "", [], [], [], [])
        assert group.protocol == GroupProtocol.GRPC

    def test_custom_name_preserves_passed_protocol(self):
        group = ProfileGroup("my_provider", "", "", [], [], [], [], GroupProtocol.GRAPHQL)
        assert group.protocol == GroupProtocol.GRAPHQL

    def test_custom_name_defaults_to_other(self):
        group = ProfileGroup("my_provider", "", "", [], [], [], [])
        assert group.protocol == GroupProtocol.OTHER

    def test_group_protocol_setter_round_trip(self):
        group = ProfileGroup("my_provider", "", "", [], [], [], [], GroupProtocol.GRAPHQL)
        group.group_protocol = GroupProtocol.GRPC
        assert group.group_protocol == GroupProtocol.GRPC

    def test_json_rpc_name_defaults_to_other(self):
        """SUI_JSON_RPC_GROUP has no __post_init__ branch — it must stay OTHER."""
        group = ProfileGroup(SUI_JSON_RPC_GROUP, "", "", [], [], [], [])
        assert group.protocol == GroupProtocol.OTHER


# ---------------------------------------------------------------------------
# ProfileGroup — address / alias operations
# ---------------------------------------------------------------------------


class TestProfileGroupAddressAlias:
    @pytest.fixture
    def group(self):
        return _make_minimal_group("test_group")

    def test_active_address_get(self, group):
        g, address, _ = group
        assert g.active_address == address

    def test_active_address_set(self, group):
        g, _, _ = group
        _mnem, addr2, key2, alias2 = ProfileGroup.new_keypair_parts(
            of_keytype=SignatureScheme.ED25519, alias_list=g.alias_list
        )
        g.add_keypair_and_parts(new_address=addr2, new_alias=alias2, new_key=key2)
        g.active_address = addr2
        assert g.active_address == addr2

    def test_active_address_set_unknown_raises(self, group):
        g, _, _ = group
        with pytest.raises(ValueError, match="is not in list"):
            g.active_address = "0x" + "a" * 64

    def test_active_alias_get(self, group):
        g, _, alias = group
        assert g.active_alias == alias

    def test_active_alias_set(self, group):
        g, _, _ = group
        _mnem, addr2, key2, alias2 = ProfileGroup.new_keypair_parts(
            of_keytype=SignatureScheme.ED25519, alias_list=g.alias_list
        )
        g.add_keypair_and_parts(new_address=addr2, new_alias=alias2, new_key=key2)
        g.active_alias = alias2.alias
        assert g.active_alias == alias2.alias

    def test_active_alias_set_unknown_raises(self, group):
        g, _, _ = group
        with pytest.raises(ValueError, match="not found"):
            g.active_alias = "no-such-alias"

    def test_address_for_alias_happy_path(self, group):
        g, address, alias = group
        assert g.address_for_alias(alias=alias) == address

    def test_address_for_alias_unknown_raises(self, group):
        g, _, _ = group
        with pytest.raises(ValueError, match="not found"):
            g.address_for_alias(alias="ghost")

    def test_alias_for_address_happy_path(self, group):
        g, address, alias = group
        result = g.alias_for_address(address=address)
        assert result.alias == alias

    def test_alias_for_address_unknown_raises(self, group):
        g, _, _ = group
        with pytest.raises(ValueError, match="not found"):
            g.alias_for_address(address="0x" + "b" * 64)

    def test_replace_alias_name_success(self, group):
        g, address, alias = group
        returned_address = g.replace_alias_name(from_alias=alias, to_alias="new-alias")
        assert returned_address == address
        assert g.active_alias == "new-alias"

    def test_replace_alias_source_not_found_raises(self, group):
        g, _, _ = group
        with pytest.raises(ValueError, match="not found"):
            g.replace_alias_name(from_alias="ghost", to_alias="new-alias")

    def test_replace_alias_target_already_exists_raises(self, group):
        g, _, alias = group
        with pytest.raises(ValueError, match="already exists"):
            g.replace_alias_name(from_alias=alias, to_alias=alias)

    def test_alias_name_for_address_happy_path(self, group):
        g, address, alias = group
        assert g.alias_name_for_address(address=address) == alias

    def test_alias_name_for_address_unknown_raises(self, group):
        g, _, _ = group
        with pytest.raises(ValueError, match="not found"):
            g.alias_name_for_address(address="0x" + "e" * 64)

    def test_remove_alias_success(self, group):
        g, _, _ = group
        _mnem, addr2, key2, alias2 = ProfileGroup.new_keypair_parts(
            of_keytype=SignatureScheme.ED25519, alias_list=g.alias_list
        )
        g.add_keypair_and_parts(new_address=addr2, new_alias=alias2, new_key=key2)
        g.remove_alias(alias_name=alias2.alias)
        assert addr2 not in g.address_list
        assert alias2.alias not in [a.alias for a in g.alias_list]

    def test_remove_alias_active_falls_back_to_first(self, group):
        """Removing the active alias reassigns active address to the first remaining."""
        g, address, alias = group
        _mnem, addr2, key2, alias2 = ProfileGroup.new_keypair_parts(
            of_keytype=SignatureScheme.ED25519, alias_list=g.alias_list
        )
        g.add_keypair_and_parts(new_address=addr2, new_alias=alias2, new_key=key2)
        g.active_address = addr2
        g.remove_alias(alias_name=alias2.alias)
        # Should fall back to the first remaining address
        assert g.using_address == address

    def test_remove_alias_not_found_raises(self, group):
        g, _, _ = group
        with pytest.raises(ValueError, match="does not exist"):
            g.remove_alias(alias_name="ghost-alias")


# ---------------------------------------------------------------------------
# ProfileGroup — profile operations
# ---------------------------------------------------------------------------


class TestProfileGroupProfiles:
    @pytest.fixture
    def group(self):
        return _make_minimal_group("test_group")

    def test_active_profile_get(self, group):
        g, _, _ = group
        assert g.active_profile.profile_name == "testnet"

    def test_active_profile_set(self, group):
        g, _, _ = group
        g.add_profile(new_prf=Profile("mainnet", "https://example.com/mainnet"))
        g.active_profile = "mainnet"
        assert g.active_profile.profile_name == "mainnet"

    def test_active_profile_set_unknown_raises(self, group):
        g, _, _ = group
        with pytest.raises(ValueError, match="does not exist"):
            g.active_profile = "no-such-profile"

    def test_add_profile_duplicate_raises(self, group):
        g, _, _ = group
        with pytest.raises(ValueError, match="already exists"):
            g.add_profile(new_prf=Profile("testnet", "https://example.com"))

    def test_remove_profile_success(self, group):
        g, _, _ = group
        g.add_profile(new_prf=Profile("devnet", "https://example.com/devnet"))
        g.remove_profile(profile_name="devnet")
        assert "devnet" not in g.profile_names

    def test_remove_profile_not_found_raises(self, group):
        g, _, _ = group
        with pytest.raises(ValueError):
            g.remove_profile(profile_name="no-such")

    def test_remove_active_profile_falls_back_to_first(self, group):
        g, _, _ = group
        g.add_profile(new_prf=Profile("devnet", "https://example.com/devnet"))
        g.active_profile = "devnet"
        g.remove_profile(profile_name="devnet")
        assert g.using_profile == "testnet"


# ---------------------------------------------------------------------------
# ProfileGroup — keypair operations
# ---------------------------------------------------------------------------


class TestProfileGroupKeypairs:
    @pytest.fixture
    def group(self):
        return _make_minimal_group("test_group")

    def test_keypair_for_address_happy_path(self, group):
        g, address, _ = group
        kp = g.keypair_for_address(address=address)
        # Verify the returned keypair round-trips to the stored private key string
        assert kp.serialize() == g.key_list[0].private_key_base64

    def test_keypair_for_address_unknown_raises(self, group):
        g, _, _ = group
        with pytest.raises(ValueError):
            g.keypair_for_address(address="0x" + "d" * 64)

    def test_add_keypair_duplicate_key_raises(self, group):
        g, _, _ = group
        existing_key = g.key_list[0]
        _mnem, _addr2, _key2, fresh_alias = ProfileGroup.new_keypair_parts(
            of_keytype=SignatureScheme.ED25519, alias_list=g.alias_list
        )
        with pytest.raises(ValueError):
            g.add_keypair_and_parts(
                new_address="0x" + "c" * 64,
                new_alias=fresh_alias,
                new_key=existing_key,
            )

    def test_add_keys_block_import(self, group):
        g, _, _ = group
        key_str = _gen_key_string()
        before = len(g.address_list)
        addies = g.add_keys(keys=[{"key_string": key_str}])
        assert len(addies) == 1
        assert len(g.address_list) == before + 1

    def test_add_keys_duplicate_raises(self, group):
        g, _, _ = group
        key_str = _gen_key_string()
        g.add_keys(keys=[{"key_string": key_str}])
        with pytest.raises(ValueError, match="already exists"):
            g.add_keys(keys=[{"key_string": key_str}])

    def test_add_keypair_duplicate_alias_raises(self, group):
        """Fresh key with an alias name already in the group must raise ValueError."""
        g, _, alias = group
        _mnem, addr2, key2, _any_alias = ProfileGroup.new_keypair_parts(
            of_keytype=SignatureScheme.ED25519, alias_list=[]
        )
        dup_alias = ProfileAlias(alias, _any_alias.public_key_base64)
        with pytest.raises(ValueError, match="already exist"):
            g.add_keypair_and_parts(
                new_address=addr2,
                new_alias=dup_alias,
                new_key=key2,
            )

    def test_add_keys_with_explicit_alias(self, group):
        """Providing an 'alias' key in the key dict uses that alias instead of generating one."""
        g, _, _ = group
        key_str = _gen_key_string()
        addies = g.add_keys(keys=[{"key_string": key_str, "alias": "custom-alias"}])
        assert g.alias_name_for_address(address=addies[0]) == "custom-alias"

    def test_add_keys_duplicate_explicit_alias_raises(self, group):
        """Providing an alias that already exists must raise ValueError."""
        g, _, alias = group
        with pytest.raises(ValueError):
            g.add_keys(keys=[{"key_string": _gen_key_string(), "alias": alias}])


# ---------------------------------------------------------------------------
# PysuiConfiguration — initialization
# ---------------------------------------------------------------------------


class TestPysuiConfigurationInit:
    def test_init_missing_config_raises(self, tmp_path):
        with pytest.raises(ValueError, match="does not exist"):
            PysuiConfiguration(from_cfg_path=str(tmp_path))

    def test_initialize_config_creates_file(self, tmp_path):
        PysuiConfiguration.initialize_config(
            in_folder=tmp_path,
            init_groups=[{"name": SUI_GQL_RPC_GROUP, "make_active": True}],
        )
        assert (tmp_path / "PysuiConfig.json").exists()

    def test_initialize_config_empty_groups_raises(self, tmp_path):
        with pytest.raises(ValueError, match="At least 1 group"):
            PysuiConfiguration.initialize_config(in_folder=tmp_path, init_groups=[])

    def test_initialize_config_already_exists_raises(self, tmp_path):
        PysuiConfiguration.initialize_config(
            in_folder=tmp_path,
            init_groups=[{"name": SUI_GQL_RPC_GROUP, "make_active": True}],
        )
        with pytest.raises(ValueError, match="already exists"):
            PysuiConfiguration.initialize_config(
                in_folder=tmp_path,
                init_groups=[{"name": SUI_GQL_RPC_GROUP, "make_active": True}],
            )

    def test_class_constants_match_confgroup(self):
        assert PysuiConfiguration.SUI_GQL_RPC_GROUP == SUI_GQL_RPC_GROUP
        assert PysuiConfiguration.SUI_GRPC_GROUP == SUI_GRPC_GROUP
        assert PysuiConfiguration.SUI_JSON_RPC_GROUP == SUI_JSON_RPC_GROUP
        assert PysuiConfiguration.SUI_USER_GROUP == SUI_USER_GROUP

    def test_reload_from_file_preserves_state(self, cfg_dir):
        tmp_dir, cfg = cfg_dir
        original_address = cfg.active_address
        original_alias = cfg.active_address_alias
        original_profile = cfg.active_profile
        original_key_count = len(cfg.active_group.address_list)
        cfg2 = PysuiConfiguration(from_cfg_path=str(tmp_dir))
        assert cfg2.active_address == original_address
        assert cfg2.active_address_alias == original_alias
        assert cfg2.active_profile == original_profile
        assert len(cfg2.active_group.address_list) == original_key_count
        # Verify the keypair is still functional after reload
        kp = cfg2.keypair_for_address(address=original_address)
        assert kp is not None

    def test_config_actives_property(self, cfg_dir):
        _, cfg = cfg_dir
        expected = f"{SUI_GQL_RPC_GROUP}.testnet"
        assert cfg.config_actives == expected

    def test_version_migration_saves_updated_version(self, tmp_path):
        """Loading a v1.0.0 config file upgrades version to 1.1.0 and persists the change."""
        PysuiConfiguration.initialize_config(
            in_folder=tmp_path,
            init_groups=[{"name": SUI_GQL_RPC_GROUP, "make_active": True}],
        )
        config_file = tmp_path / "PysuiConfig.json"
        data = json.loads(config_file.read_text())
        data["version"] = "1.0.0"
        config_file.write_text(json.dumps(data, indent=2))

        cfg2 = PysuiConfiguration(from_cfg_path=str(tmp_path))

        assert cfg2.model.version == "1.1.0"
        saved = json.loads(config_file.read_text())
        assert saved["version"] == "1.1.0"


# ---------------------------------------------------------------------------
# PysuiConfiguration — make_active and navigation
# ---------------------------------------------------------------------------


class TestMakeActive:
    def test_make_active_profile(self, cfg_dir):
        _, cfg = cfg_dir
        cfg.new_profile(
            profile_name="mainnet",
            url="https://graphql.mainnet.sui.io/graphql",
            persist=False,
        )
        cfg.make_active(profile_name="mainnet", persist=False)
        assert cfg.active_profile == "mainnet"

    def test_make_active_unknown_group_raises(self, cfg_dir):
        _, cfg = cfg_dir
        with pytest.raises(ValueError):
            cfg.make_active(group_name="no_such_group", persist=False)

    def test_make_active_by_alias(self, cfg_dir):
        _, cfg = cfg_dir
        cfg.new_keypair(
            of_keytype=SignatureScheme.ED25519, alias="sec-alias", persist=False
        )
        cfg.make_active(alias="sec-alias", persist=False)
        assert cfg.active_address_alias == "sec-alias"

    def test_make_active_by_address(self, cfg_dir):
        _, cfg = cfg_dir
        _, addr2 = cfg.new_keypair(
            of_keytype=SignatureScheme.ED25519, alias="thr-alias", persist=False
        )
        cfg.make_active(address=addr2, persist=False)
        assert cfg.active_address == addr2


# ---------------------------------------------------------------------------
# PysuiConfiguration — group and profile management
# ---------------------------------------------------------------------------


class TestGroupAndProfileManagement:
    def test_group_names_contains_initialized(self, cfg_dir):
        _, cfg = cfg_dir
        assert SUI_GQL_RPC_GROUP in cfg.group_names()

    def test_profile_names_active_group(self, cfg_dir):
        _, cfg = cfg_dir
        assert "testnet" in cfg.profile_names()

    def test_profile_names_in_group(self, cfg_dir):
        _, cfg = cfg_dir
        names = cfg.profile_names(in_group=SUI_GQL_RPC_GROUP)
        assert "testnet" in names

    def test_profile_names_does_not_mutate_active_group(self, cfg_dir):
        """profile_names(in_group=...) must not change the active group — verifies our fix."""
        _, cfg = cfg_dir
        cfg.new_group(
            group_name="second_group",
            profile_block=[{"profile_name": "devnet", "url": "https://example.com"}],
            key_block=[{"key_string": _gen_key_string()}],
            active_address_index=0,
            group_protocol=GroupProtocol.GRPC,
            persist=False,
        )
        original_active = cfg.active_group_name
        cfg.profile_names(in_group="second_group")
        assert cfg.active_group_name == original_active

    def test_profile_names_unknown_group_raises(self, cfg_dir):
        _, cfg = cfg_dir
        with pytest.raises(ValueError):
            cfg.profile_names(in_group="ghost_group")

    def test_new_group_creates_group(self, cfg_dir):
        _, cfg = cfg_dir
        addies = cfg.new_group(
            group_name="extra_group",
            profile_block=[{"profile_name": "testnet", "url": "https://example.com"}],
            key_block=[{"key_string": _gen_key_string()}],
            active_address_index=0,
            group_protocol=GroupProtocol.GRPC,
            persist=False,
        )
        assert len(addies) == 1
        assert "extra_group" in cfg.group_names()

    def test_new_group_duplicate_raises(self, cfg_dir):
        _, cfg = cfg_dir
        with pytest.raises(ValueError, match="already exists"):
            cfg.new_group(
                group_name=SUI_GQL_RPC_GROUP,
                profile_block=[],
                key_block=[{"key_string": _gen_key_string()}],
                active_address_index=0,
                group_protocol=GroupProtocol.GRAPHQL,
                persist=False,
            )

    def test_new_profile_adds_profile(self, cfg_dir):
        _, cfg = cfg_dir
        cfg.new_profile(
            profile_name="devnet", url="https://example.com/dev", persist=False
        )
        assert "devnet" in cfg.profile_names()

    def test_new_profile_duplicate_raises(self, cfg_dir):
        _, cfg = cfg_dir
        with pytest.raises(ValueError, match="already exists"):
            cfg.new_profile(
                profile_name="testnet", url="https://example.com", persist=False
            )

    def test_update_profile_url(self, cfg_dir):
        _, cfg = cfg_dir
        new_url = "https://updated.example.com/graphql"
        cfg.update_profile(profile_name="testnet", url=new_url, persist=False)
        assert cfg.url == new_url

    def test_update_profile_preserves_faucet_when_not_passed(self, cfg_dir):
        """Calling update_profile without faucet_url leaves the existing value intact."""
        _, cfg = cfg_dir
        cfg.new_profile(
            profile_name="devnet",
            url="https://example.com/devnet",
            faucet_url="https://faucet.example.com",
            persist=False,
        )
        cfg.update_profile(
            profile_name="devnet",
            url="https://new-example.com/devnet",
            persist=False,
        )
        prf = cfg.active_group.get_profile("devnet")
        assert prf.faucet_url == "https://faucet.example.com"

    def test_update_profile_updates_faucet_url(self, cfg_dir):
        _, cfg = cfg_dir
        cfg.new_profile(
            profile_name="devnet",
            url="https://example.com/devnet",
            faucet_url="https://old-faucet.com",
            persist=False,
        )
        cfg.update_profile(
            profile_name="devnet",
            faucet_url="https://new-faucet.com",
            persist=False,
        )
        prf = cfg.active_group.get_profile("devnet")
        assert prf.faucet_url == "https://new-faucet.com"

    def test_new_group_make_active(self, cfg_dir):
        _, cfg = cfg_dir
        cfg.new_group(
            group_name="active_group",
            profile_block=[{"profile_name": "testnet", "url": "https://example.com"}],
            key_block=[{"key_string": _gen_key_string()}],
            active_address_index=0,
            group_protocol=GroupProtocol.GRPC,
            make_group_active=True,
            persist=False,
        )
        assert cfg.active_group_name == "active_group"


# ---------------------------------------------------------------------------
# PysuiConfiguration — keypair and address management
# ---------------------------------------------------------------------------


class TestKeypairManagement:
    def test_new_keypair_adds_address(self, cfg_dir):
        _, cfg = cfg_dir
        before = len(cfg.active_group.address_list)
        cfg.new_keypair(
            of_keytype=SignatureScheme.ED25519, alias="new-one", persist=False
        )
        assert len(cfg.active_group.address_list) == before + 1

    def test_new_keypair_make_active(self, cfg_dir):
        _, cfg = cfg_dir
        _, new_addr = cfg.new_keypair(
            of_keytype=SignatureScheme.ED25519,
            alias="act-alias",
            make_active=True,
            persist=False,
        )
        assert cfg.active_address == new_addr

    def test_add_keys_batch(self, cfg_dir):
        _, cfg = cfg_dir
        key_str = _gen_key_string()
        before = len(cfg.active_group.address_list)
        addies = cfg.add_keys(key_block=[{"key_string": key_str}], persist=False)
        assert len(addies) == 1
        assert len(cfg.active_group.address_list) == before + 1

    def test_address_for_alias(self, cfg_dir):
        _, cfg = cfg_dir
        alias = cfg.active_address_alias
        address = cfg.address_for_alias(alias_name=alias)
        assert address == cfg.active_address

    def test_alias_for_address(self, cfg_dir):
        _, cfg = cfg_dir
        result = cfg.alias_for_address(address=cfg.active_address)
        assert result.alias == cfg.active_address_alias

    def test_keypair_for_address(self, cfg_dir):
        _, cfg = cfg_dir
        kp = cfg.keypair_for_address(address=cfg.active_address)
        assert kp is not None

    def test_new_keypair_invalid_scheme_raises(self, cfg_dir):
        _, cfg = cfg_dir
        with pytest.raises(ValueError):
            cfg.new_keypair(of_keytype=MagicMock(), persist=False)

    def test_keypair_for_address_in_group(self, cfg_dir):
        """keypair_for_address with in_group fetches from a non-active group."""
        _, cfg = cfg_dir
        key_str = _gen_key_string()
        addies = cfg.new_group(
            group_name="second_group",
            profile_block=[{"profile_name": "testnet", "url": "https://example.com"}],
            key_block=[{"key_string": key_str}],
            active_address_index=0,
            group_protocol=GroupProtocol.GRPC,
            persist=False,
        )
        # Active group is still GQL — look up from second_group explicitly
        kp = cfg.keypair_for_address(address=addies[0], in_group="second_group")
        second_grp = cfg.model.get_group(group_name="second_group")
        assert kp.serialize() == second_grp.key_list[0].private_key_base64

    def test_rename_alias_success(self, cfg_dir):
        _, cfg = cfg_dir
        old_alias = cfg.active_address_alias
        cfg.rename_alias(
            existing_alias=old_alias, new_alias="renamed-ali", persist=False
        )
        assert cfg.active_address_alias == "renamed-ali"

    def test_rename_alias_source_not_found_raises(self, cfg_dir):
        _, cfg = cfg_dir
        with pytest.raises(ValueError):
            cfg.rename_alias(
                existing_alias="ghost-alias", new_alias="other", persist=False
            )

    def test_rename_alias_target_exists_raises(self, cfg_dir):
        _, cfg = cfg_dir
        alias = cfg.active_address_alias
        cfg.new_keypair(
            of_keytype=SignatureScheme.ED25519, alias="dup-target", persist=False
        )
        with pytest.raises(ValueError):
            cfg.rename_alias(
                existing_alias=alias, new_alias="dup-target", persist=False
            )


# ---------------------------------------------------------------------------
# PysuiConfiguration — persistence
# ---------------------------------------------------------------------------


class TestPersistence:
    def test_save_to_new_path(self, cfg_dir, tmp_path):
        _, cfg = cfg_dir
        new_dir = tmp_path / "new_location"
        cfg.save_to(new_dir)
        assert (new_dir / "PysuiConfig.json").exists()

    def test_save_to_updates_config_path(self, cfg_dir, tmp_path):
        """save_to must update cfg.config to reflect the new directory."""
        _, cfg = cfg_dir
        new_dir = tmp_path / "relocated"
        cfg.save_to(new_dir)
        assert cfg.config == str(new_dir)

    def test_save_and_reload_preserves_addresses_and_aliases(self, cfg_dir):
        tmp_dir, cfg = cfg_dir
        cfg.new_keypair(
            of_keytype=SignatureScheme.ED25519, alias="extra-key", persist=True
        )
        original_addresses = list(cfg.active_group.address_list)
        original_aliases = [a.alias for a in cfg.active_group.alias_list]
        cfg2 = PysuiConfiguration(from_cfg_path=str(tmp_dir))
        assert cfg2.active_group.address_list == original_addresses
        assert [a.alias for a in cfg2.active_group.alias_list] == original_aliases
        # Verify keypairs are still functional
        for addr in original_addresses:
            assert cfg2.keypair_for_address(address=addr) is not None
