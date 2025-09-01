#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Pysui Configuration."""


from copy import deepcopy
import platform
from pathlib import Path
from typing import Optional
from deprecated.sphinx import versionchanged, versionadded, deprecated

from pysui.abstracts.client_keypair import SignatureScheme
from pysui.sui.sui_common.config.conflegacy import load_client_yaml
from pysui.sui.sui_common.config.confmodel import (
    _CURRENT_CONFIG_VERSION,
    PysuiConfigModel,
)
import pysui.sui.sui_common.config.confgroup as cfg_group


class PysuiConfiguration:
    """pysui configuration class."""

    SUI_JSON_RPC_GROUP: str = "sui_json_config"
    SUI_GQL_RPC_GROUP: str = "sui_gql_config"
    SUI_GRPC_GROUP: str = "sui_grpc_config"
    SUI_USER_GROUP: str = "user"

    @versionchanged(
        version="0.86.0",
        reason="BREAKING: Moved initializing profiles to `PysuiCofiguration.initialize_config`",
    )
    def __init__(
        self,
        *,
        group_name: Optional[str] = None,
        from_cfg_path: str = None,
        profile_name: Optional[str] = None,
        address: Optional[str] = None,
        alias: Optional[str] = None,
        persist: Optional[bool] = False,
    ):
        """PysuiConfiguration initialization.

        :param from_cfg_path: Where to read/write PysuiConfig.json, defaults to '~/.pysui'
        :type from_cfg_path: str, optional
        :param group_name: Sets the active ProfileGroup, defaults to "sui_gql_config"
        :type group_name: Optional[str], optional
        :param profile_name: Sets the active Profile, defaults to None
        :type profile_name: Optional[str], optional
        :param address: Sets the active address, defaults to None
        :type address: Optional[str], optional
        :param alias: Sets the active address via alias name (precedence is address argument), defaults to None
        :type alias: Optional[str], optional
        :param persist: Indicates wheter to persist any changes made above, defaults to False
        :type persist: Optional[bool], optional
        """
        # Get the base configuration folder and profile file
        self._config_root = Path(from_cfg_path or "~/.pysui").expanduser()
        # _ecfgdir = Path(self._config_root).expanduser()
        self._config_file = self._config_root / "PysuiConfig.json"
        if not self._config_file.exists():
            raise ValueError(
                f"{self._config_file} does not exist, use PysuiConfiguration.initialize_config to setup."
            )
        self._model: PysuiConfigModel = PysuiConfigModel.from_json(
            self._config_file.read_text(encoding="utf8")
        )
        # Migrate if versions outdated.
        if self._model.version != _CURRENT_CONFIG_VERSION:
            self._model.update_model(self.SUI_GQL_RPC_GROUP, self.SUI_GRPC_GROUP)
            self._model.version = _CURRENT_CONFIG_VERSION
            self.save()

        # Make active as per arguments
        self.make_active(
            group_name=group_name,
            profile_name=profile_name,
            address=address,
            alias=alias,
            persist=persist,
        )

    @classmethod
    def _gen_graphql(
        cls, basis: cfg_group.ProfileGroup, name: str
    ) -> cfg_group.ProfileGroup:
        """Generate graphql group"""
        group_cfg = deepcopy(basis)
        group_cfg.group_name = name
        group_cfg.group_protocol = cfg_group.GroupProtocol.GRAPHQL
        for prf in group_cfg.profiles:
            if prf.profile_name == "devnet":
                prf.url = "https://sui-devnet.mystenlabs.com/graphql"
            elif prf.profile_name == "testnet":
                prf.url = "https://sui-testnet.mystenlabs.com/graphql"
            elif prf.profile_name == "mainnet":
                prf.url = "https://sui-mainnet.mystenlabs.com/graphql"
        return group_cfg

    @classmethod
    def _gen_grpc(
        cls, basis: cfg_group.ProfileGroup, name: str
    ) -> cfg_group.ProfileGroup:
        """Generate gRPC group"""
        group_cfg = deepcopy(basis)
        group_cfg.group_name = name
        group_cfg.group_protocol = cfg_group.GroupProtocol.GRPC
        for prf in group_cfg.profiles:
            prf.faucet_url = None
            prf.faucet_status_url = None
            if prf.profile_name == "devnet":
                prf.url = "fullnode.devnet.sui.io:443"
            elif prf.profile_name == "testnet":
                prf.url = "fullnode.testnet.sui.io:443"
            elif prf.profile_name == "mainnet":
                prf.url = "fullnode.mainnet.sui.io:443"
        # Append archive profiles
        group_cfg.add_profile(
            new_prf=cfg_group.Profile(
                profile_name="main-arch", url="archive.mainnet.sui.io:443"
            )
        )
        group_cfg.add_profile(
            new_prf=cfg_group.Profile(
                profile_name="test-arch", url="archive.testnet.sui.io:443"
            )
        )

        return group_cfg

    @versionadded(
        version="0.86.0",
        reason="New group and profile initializations",
    )
    @classmethod
    def initialize_config(
        cls,
        *,
        in_folder: Optional[Path] = None,
        init_groups: list[dict],
    ) -> "PysuiConfiguration":
        """Initialize a PysuiConfiguration (PysuiConfig.json)."""
        if len(init_groups) == 0:
            raise ValueError("At least 1 group needed in initialize_config")
        _config_root = in_folder if in_folder else Path("~/.pysui")
        _config_root = _config_root.expanduser()
        _config_file = _config_root / "PysuiConfig.json"
        if not _config_root.exists():
            _config_root.mkdir(parents=True, exist_ok=True)
        if _config_file.exists():
            raise ValueError(f"{_config_file} already exists.")

        instance = cls.__new__(cls)

        _suicfg = Path("~/.sui/sui_config").expanduser()
        if _suicfg.exists():
            _faux_group = load_client_yaml(_suicfg, "_faux")

        if platform.system() == "Windows":
            _bcfgp = Path("~/.cargo/bin/sui.exe").expanduser()
        else:
            _bcfgp = Path("~/.cargo/bin/sui").expanduser()

        _bcfg = str(_bcfgp) if _bcfgp.exists() else ""

        setattr(instance, "_model", PysuiConfigModel(_CURRENT_CONFIG_VERSION, _bcfg))
        setattr(instance, "_config_root", _config_root)
        setattr(instance, "_config_file", _config_file)
        for group in init_groups:
            group_cfg = cfg_group.ProfileGroup(
                group["name"], "", "", [], [], [], [], cfg_group.GroupProtocol.OTHER
            )
            if group.get("graphql_from_sui", None):
                if _suicfg.exists():
                    group_cfg = cls._gen_graphql(_faux_group, group["name"])
                else:
                    raise ValueError(
                        f"Initialize {group['name']} from sui config failure. Sui config does not exist."
                    )
            if group.get("grpc_from_sui", None):
                if _suicfg.exists():
                    group_cfg = cls._gen_grpc(_faux_group, group["name"])
                else:
                    raise ValueError(
                        f"Initialize {group['name']} from sui config failure. Sui config does not exist."
                    )

            instance.model.add_group(
                group=group_cfg, make_active=group.get("make_active", False)
            )
        # Save to file
        instance._write_model()
        # Return configuration
        return instance

    def _write_model(self):
        """Writes out the configuration model."""
        self._config_file.write_text(self.to_json(indent=2))

    def save(self):
        """External invoked write."""
        self._write_model()

    def save_to(self, new_folder: Path):
        """External invoked write."""
        _config_root = new_folder.expanduser()
        # _ecfgdir = Path(self._config_root).expanduser()
        _config_file = _config_root / "PysuiConfig.json"
        if not _config_root.exists():
            _config_root.mkdir(parents=True, exist_ok=True)
        self._config_root = _config_root
        self._config_file = _config_file
        self._write_model()

    def to_json(self, *_cmds, **kwargs) -> str:
        """Return JSON formatted representation of PysuiConfiguration."""
        return self._model.to_json(**kwargs)

    @property
    def config(self) -> str:
        """Return the configuration folder."""
        return str(self._config_root)

    @property
    def model(self) -> PysuiConfigModel:
        """Return underlying model."""
        return self._model

    @property
    def active_group_name(self) -> str:
        """Return name of active group."""
        return self._model.active_group.group_name

    @property
    def active_group(self) -> cfg_group.ProfileGroup:
        """Return the active group."""
        return self._model.active_group

    @property
    def active_address(self) -> str:
        """Returns the active groups active address."""
        return self.active_group.using_address

    @property
    def active_address_alias(self) -> str:
        """Returns the active groups active address."""
        return self.active_group.active_alias

    @property
    def active_profile(self) -> str:
        """Returns the active groups active profile name."""
        return self.active_group.active_profile.profile_name

    @property
    def url(self) -> str:
        """Returns the active groups active profile url."""
        return self.active_group.active_profile.url

    @property
    def faucet_url(self) -> str:
        """Returns the active groups active profile faucet url."""
        return self.active_group.active_profile.faucet_urls

    @property
    def faucet_status_url(self) -> str:
        """Returns the active groups active profile faucet status url."""
        return self.active_group.active_profile.faucet_status_url

    @versionchanged(version="0.86.0", reason="Name change to be semantically correct")
    @property
    def config_actives(self) -> str:
        """Return configuration breadcrumb path."""
        _group = self.active_group
        return f"{_group.group_name}.{_group.active_profile.profile_name}"

    def address_for_alias(self, *, alias_name: str) -> str:
        """Return the address for the alias name in current group."""
        return self.active_group.address_for_alias(alias=alias_name)

    def alias_for_address(self, *, address: str) -> str:
        """Return the alias for the address in current group."""
        return self.active_group.alias_for_address(address=address)

    def keypair_for_address(self, *, address: str, in_group: Optional[str] = None):
        """Returnn the SuiKeyPair for an address."""
        _group = (
            self._model.get_group(group_name=in_group)
            if in_group
            else self.active_group
        )
        return _group.keypair_for_address(address=address)

    def group_names(self) -> list[str]:
        """Return the groups in the configuration."""
        return [x.group_name for x in self._model.groups]

    def profile_names(self, *, in_group: Optional[str] = None) -> list[str]:
        """Return the profiles in a group. Default to active group."""
        # If group specified and it's not the active
        if in_group and self._model.group_active != in_group:
            # If  it exists and is not already the active group then set it
            if _group := self._model.has_group(group_name=in_group):
                self._model.active_group = in_group
                _changes = True
            else:
                raise ValueError(f"{in_group} does not exist")
        else:
            _group = self.active_group

        return _group.profile_names

    def make_active(
        self,
        *,
        group_name: Optional[str] = None,
        profile_name: Optional[str] = None,
        address: Optional[str] = None,
        alias: Optional[str] = None,
        persist: Optional[bool] = True,
    ) -> "PysuiConfiguration":
        """Activate specific aspects of configuration."""
        # Track changes for persist
        _changes: bool = False

        # If group specified and it's not the active
        if group_name and self._model.group_active != group_name:
            # If  it exists and is not already the active group then set it
            if _group := self._model.has_group(group_name=group_name):
                self._model.active_group = group_name
                _changes = True
            else:
                raise ValueError(f"{group_name} does not exist")
        else:
            _group = self.active_group

        # Change profile, checks if it exists
        if profile_name and _group.using_profile != profile_name:
            _group.active_profile = profile_name
            _changes = True

        # Change activte address, checks if exists
        if address and _group.active_address != address:
            _group.active_address = address
            _changes = True
        # Else try alias
        elif alias and _group.active_alias != alias:
            _group.active_alias = alias
            _changes = True

        if _changes and persist:
            self._write_model()
        return self

    def new_group(
        self,
        *,
        group_name: str,
        profile_block: list[dict[str, str]],
        key_block: list[dict[str, str]],
        active_address_index: int,
        group_protocol: cfg_group.GroupProtocol,
        make_group_active: Optional[bool] = False,
        persist: Optional[bool] = True,
    ) -> list[str]:
        """Create a unique new group.

        A profile is defined by a dict with the following k/v pairs
        {
            "profile_name": str,
            "url": str,
            "faucet_url": str | None,
            "faucet_status_url": str | None,
            "make_active": bool
        }

        A key is defined by a dict with following k/v pairs
        {
            "key_string": str # Either a base64 or bech32 private key
            "alias": str     # Optional alias, one will be generated otherwise
        }

        :param group_name: The name of the new group, fails if already exists
        :type group_name: str
        :param profile_block: A list of profile dicts
        :type profile_block: list[dict[str, str]]
        :param key_block: A list of key dicts
        :type key_block: list[dict[str, str]]
        :param active_address_index: The index of the address to make as active_address for group
        :type active_address_index: int
        :parm group_protocol: THe protocol hint from conf_group.py
        :type GroupProtocol
        :param make_group_active: Sets the group to the configurations active_group, defaults to False
        :type make_group_active: Optional[bool], optional
        :param persist: Persist updates to PysuiConfig.json, defaults to True
        :type persist: Optional[bool], optional
        :return: The list of addresses generated from the key_block
        :rtype: list[str]
        """

        if self._model.has_group(group_name=group_name):
            raise ValueError(f"{group_name} already exists")
        # Create and add an empty group
        self.model.add_group(
            group=cfg_group.ProfileGroup(
                group_name, "", "", [], [], [], [], group_protocol
            ),
            make_active=make_group_active,
        )
        if make_group_active and (self.active_group.group_name != group_name):
            self.model.remove_group(group_name=group_name)
            raise ValueError(f"Failed to make {group_name} active. Aborting new_group")

        # Get the group
        _group = self.model.get_group(group_name=group_name)

        # Add key block
        addies: list[str] = self.add_keys(
            key_block=key_block, in_group=group_name, persist=False
        )
        if len(addies) != len(key_block):
            self.model.remove_group(group_name=group_name)
            raise ValueError(
                f"Failed to added keyblock {key_block}. Aborting new_group"
            )

        # Add profile block
        if profile_block:
            for pblock in profile_block:
                self.new_profile(in_group=group_name, persist=False, **pblock)
            if len(self.model.get_group(group_name=group_name).profiles) != len(
                profile_block
            ):
                self.model.remove_group(group_name=group_name)
                raise ValueError(
                    f"Failed to add profile_block {profile_block}. Aborting new_group."
                )
        _group.active_address = addies[active_address_index]
        if persist:
            self._write_model()
        return addies

    def new_keypair(
        self,
        *,
        of_keytype: SignatureScheme,
        in_group: Optional[str] = None,
        word_counts: Optional[int] = 12,
        derivation_path: Optional[str] = None,
        make_active: Optional[bool] = False,
        alias: Optional[str] = None,
        persist: Optional[bool] = True,
    ) -> tuple[str, str]:
        """new_keypair _summary_

        :param of_keytype: Identifies whether new key is ed25519, secp256k1 or secp256r1
        :type of_keytype: SignatureScheme
        :param in_group: _description_, defaults to None
        :type in_group: Optional[str], optional
        :param word_counts: count of words to generate mnemonic phrase, defaults to 12
        :type word_counts: int, optional
        :param derivation_path: The derivation path for key, specific to Signature scheme,
            defaults to root path of scheme
        :type derivation_path: str, optional
        :param make_active: Make the result address the active_address, defaults to False
        :type make_active: Optional[bool], optional
        :param alias: Provide an alias for the new address, will be generated if None
        :type alias: Optional[str], optional
        :param persist: Persist updates to PysuiConfig.json, defaults to True
        :type persist: Optional[bool], optional
        :return: The mnemonic phrase generated for the key and the new address
        :rtype: tuple[str, str]
        """
        # Resolve group
        _group = (
            self._model.get_group(group_name=in_group)
            if in_group
            else self.active_group
        )

        if of_keytype in [
            SignatureScheme.ED25519,
            SignatureScheme.SECP256K1,
            SignatureScheme.SECP256R1,
        ]:
            mnem, new_addy, prf_key, prf_alias = (
                cfg_group.ProfileGroup.new_keypair_parts(
                    of_keytype=of_keytype,
                    word_counts=word_counts,
                    derivation_path=derivation_path,
                    alias=alias,
                    alias_list=_group.alias_list,
                )
            )
            new_addy = _group.add_keypair_and_parts(
                new_address=new_addy,
                new_alias=prf_alias,
                new_key=prf_key,
                make_active=make_active,
            )
            if make_active and _group.group_name != self.active_group.group_name:
                self._model.active_group = _group.group_name
            if persist:
                self._write_model()
            return mnem, new_addy
        raise ValueError(f"{of_keytype}: Not recognized as valid keypair scheme.")

    def add_keys(
        self,
        *,
        key_block: list[dict[str, str]],
        in_group: Optional[str] = None,
        persist: Optional[bool] = True,
    ) -> list[str]:
        """Add one or more keys to a group. Each dict has k/v:

        {
            "key_string": str # Either a base64 or bech32 private key
            "alias": str     # Optional alias, one will be generated otherwise
        }

        :param key_block: List of key construct dictionaries
        :type key_block: list[dict]
        :param in_group: Group to add new profile, defaults to active_group or excepts if not exists
        :type in_group: Optional[str]
        :param persist: Persist updates to PysuiConfig.json, defaults to True
        :type persist: Optional[bool], optional
        :return: List of addresses derived from keys
        :rtype: list[str]
        """
        _group = (
            self._model.get_group(group_name=in_group)
            if in_group
            else self.active_group
        )

        addies: list[str] = _group.add_keys(keys=key_block)

        if persist:
            self._write_model()

        return addies

    def new_profile(
        self,
        *,
        profile_name: str,
        url: str,
        faucet_url: Optional[str] = None,
        faucet_status_url: Optional[str] = None,
        make_active: Optional[bool] = False,
        in_group: Optional[str] = None,
        persist: Optional[bool] = True,
    ):
        """Adds a new profile to exiting or named group, equivelant of `sui client new-env`.

        :param profile_name: The name of the new profile, exception if exists
        :type porfile_name: str
        :param url: The url reference for the profile
        :type url: str
        :param faucet_url: The faucet url reference for the profile, defaults to None
        :type faucet_url: Optional[str], optional
        :param faucet_status_url: The faucet status url reference for the profile, defaults to None
        :type faucet_status_url: Optional[str], optional
        :param make_active: Sets this as the groups active_profile, defaults to False
        :type make_active: Optional[bool], optional
        :param in_group: Group to add new profile, defaults to active_group or excepts if not exists
        :type in_group: Optional[str], optional
        :param persist: Persist updates to PysuiConfig.json, defaults to True
        :type persist: Optional[bool], optional
        """
        _group = (
            self._model.get_group(group_name=in_group)
            if in_group
            else self.active_group
        )
        _group.add_profile(
            new_prf=cfg_group.Profile(profile_name, url, faucet_url, faucet_status_url),
            make_active=make_active,
        )
        if persist:
            self._write_model()

    def update_profile(
        self,
        *,
        profile_name: str,
        url: Optional[str] = None,
        faucet_url: Optional[str] = None,
        faucet_status_url: Optional[str] = None,
        in_group: Optional[str] = None,
        persist: Optional[bool] = True,
    ):
        """Updates and exiting profile.

        :param profile_name: The name of the existing profile, exception if not exists
        :type porfile_name: str
        :param url: The url reference for the profile, defaults to None
        :type url: Optional[str], optional
        :param faucet_url: The faucet url reference for the profile, defaults to None
        :type faucet_url: Optional[str], optional
        :param faucet_status_url: The faucet status url reference for the profile, defaults to None
        :type faucet_status_url: Optional[str], optional
        :param make_active: Sets this as the groups active_profile, defaults to False
        :type make_active: Optional[bool], optional
        :param in_group: Group to add new profile, defaults to active_group or excepts if not exists
        :type in_group: Optional[str], optional
        :param persist: Persist updates to PysuiConfig.json, defaults to True
        :type persist: Optional[bool], optional
        """
        _group = (
            self._model.get_group(group_name=in_group)
            if in_group
            else self.active_group
        )
        _prf = _group.get_profile(profile_name)
        _prf.url = url or _prf.url
        _prf.faucet_url = faucet_url or _prf.faucet_url
        _prf.faucet_status_url = faucet_status_url or _prf.faucet_status_url
        if persist:
            self._write_model()

    def rename_alias(
        self,
        *,
        existing_alias: str,
        new_alias: str,
        in_group: Optional[str] = None,
        persist: Optional[bool] = True,
    ) -> str:
        """Rename an alias.

        :param existing_alias: The name of the existing alias address association, fails if not found
        :type existing_alias: str
        :param new_alias: The new name to set to address association, fails if already exists
        :type new_alias: str
        :param in_group: Group if different than active_group, defaults to active_group or excepts if not exists
        :type in_group: Optional[str], optional
        :param persist: Persist updates to PysuiConfig.json, defaults to True
        :type persist: Optional[bool], optional
        :return: The address associated to the new alias
        :rtype: str
        """
        _group = (
            self._model.get_group(group_name=in_group)
            if in_group
            else self.active_group
        )

        _res = _group.replace_alias_name(from_alias=existing_alias, to_alias=new_alias)
        if _res and persist:
            self._write_model()
        return _res
