#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Confidential Transfer (private funds) network configuration.

:class:`PrivateFundsConfig` loads the per-network Confidential Transfer package
and registry ids from ``PrivateFundsConfig.json`` (default directory ``~/.pysui``)
and resolves the group that matches the active :class:`PysuiConfiguration`
profile.  It mirrors :class:`pysui.zklogin_seal.config.ZkSealConfig` but holds no
active pointer of its own — the active network is resolved live from
``PysuiConfiguration`` at construction.
"""

import dataclasses
import pathlib
from typing import Optional

import dataclasses_json

from pysui import PysuiConfiguration
from pysui.sui.sui_common.config.confgroup import GroupProtocol, NetworkType

_CURRENT_PRIVATEFUNDS_CONFIG_VERSION: int = 2


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class PrivateFundsGroup:
    """A per-network Confidential Transfer configuration group.

    :param name: Group name; must match the active PysuiConfiguration profile name
    :type name: str
    :param package_id: Confidential Transfer package id for this network
    :type package_id: str
    :param token_registry: TokenRegistry shared-object id for this network
    :type token_registry: str
    :param account_registry: AccountRegistry shared-object id for this network
    :type account_registry: str
    :param network_type: The Sui network type for this group; backfilled by
        migration for well-known group names, otherwise must be set explicitly
    :type network_type: Optional[NetworkType], optional
    """

    name: str
    package_id: str
    token_registry: str
    account_registry: str
    network_type: Optional[NetworkType] = None


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class _PrivateFundsConfigModel:
    """Internal serialization model for PrivateFundsConfig JSON persistence.

    :param version: Configuration schema version, defaults to 1
    :type version: int, optional
    :param groups: Network groups defined in this configuration, defaults to empty list
    :type groups: list[PrivateFundsGroup], optional
    """

    version: int = 1
    groups: list[PrivateFundsGroup] = dataclasses.field(default_factory=list)


class PrivateFundsConfig:
    """Confidential Transfer per-network configuration manager.

    On construction the configuration is loaded from ``PrivateFundsConfig.json``
    (creating the default file when the default ``~/.pysui`` location is used and
    no file exists), backlevel configurations are migrated in place, and the group
    matching the active :class:`PysuiConfiguration` profile is resolved and
    validated.  The matched group is available via :attr:`active_group`.

    :param pysui_config: The active pysui configuration whose group protocol and
        profile name drive group resolution
    :type pysui_config: PysuiConfiguration
    :param from_cfg_path: Directory containing ``PrivateFundsConfig.json``; defaults
        to ``~/.pysui``
    :type from_cfg_path: Optional[str], optional
    :raises ValueError: If ``from_cfg_path`` is given but the file does not exist
        there; if the active group protocol is not GraphQL or gRPC; if no group
        name matches the active profile; if the matched group's ids are unset; or
        if the matched group's network_type does not match the active
        PysuiConfiguration profile's network_type
    """

    _CONFIG_FILE_NAME: str = "PrivateFundsConfig.json"
    _DEFAULT_DIR: str = "~/.pysui"

    def __init__(
        self,
        *,
        pysui_config: PysuiConfiguration,
        from_cfg_path: Optional[str] = None,
    ) -> None:
        """Load the configuration, migrate if needed, and resolve the active group."""
        self._config_root: pathlib.Path = pathlib.Path(
            from_cfg_path or self._DEFAULT_DIR
        ).expanduser()
        self._config_file: pathlib.Path = self._config_root / self._CONFIG_FILE_NAME
        if not self._config_file.exists():
            if from_cfg_path is not None:
                raise ValueError(f"{self._config_file} does not exist.")
            self._initialize_config()
        self._model: _PrivateFundsConfigModel = _PrivateFundsConfigModel.from_json(
            self._config_file.read_text()
        )
        self._migrate_if_needed()
        self._active_group: PrivateFundsGroup = self._match_active_group(
            pysui_config=pysui_config
        )

    @staticmethod
    def default_path() -> pathlib.Path:
        """Return the default configuration directory.

        :returns: The expanded default directory (``~/.pysui``)
        :rtype: pathlib.Path
        """
        return pathlib.Path(PrivateFundsConfig._DEFAULT_DIR).expanduser()

    @property
    def active_group(self) -> PrivateFundsGroup:
        """Return the group matched to the active PysuiConfiguration profile.

        :returns: The matched Confidential Transfer group
        :rtype: PrivateFundsGroup
        """
        return self._active_group

    def save(self, path: Optional[pathlib.Path] = None) -> None:
        """Persist the current configuration to disk.

        :param path: Destination file path; defaults to the path used at construction
        :type path: Optional[pathlib.Path], optional
        """
        target = path or self._config_file
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self._model.to_json(indent=2))

    def _migrate_if_needed(self) -> None:
        """Bump PrivateFundsConfig schema version and persist if a backlevel config was loaded."""
        if self._model.version < _CURRENT_PRIVATEFUNDS_CONFIG_VERSION:
            well_known_network_types = {
                "devnet": NetworkType.DEVELOP,
                "testnet": NetworkType.TEST,
                "mainnet": NetworkType.PRODUCTION,
            }
            for group in self._model.groups:
                if (
                    group.network_type is None
                    and group.name in well_known_network_types
                ):
                    group.network_type = well_known_network_types[group.name]
            self._model.version = _CURRENT_PRIVATEFUNDS_CONFIG_VERSION
            self.save()

    def _initialize_config(self) -> None:
        """Create the default configuration file with network groups.

        ``devnet`` is pre-populated with the live pysui-ct object ids for the
        ``contra`` module (published 2026-08-25). ``testnet`` and ``mainnet``
        remain the placeholder ``"0x"`` until CT is deployed there and are
        expected to be replaced with real object ids before use.
        """
        network_ids: dict[str, dict[str, str]] = {
            "devnet": {
                "package_id": (
                    "0xa516f301e83e90c2f335c5ce22802061faeacbf8a093bb9c5afd3165a9521add"
                ),
                "token_registry": (
                    "0x674fbada71b10a4561e174245cdf27a3e446fb406fd54e3abee4ba4f86635dfa"
                ),
                "account_registry": (
                    "0x8ff4a773339061ad8e1ecb961da58ddba9368c948fd180ca161990d03c0665f5"
                ),
            },
            "testnet": {
                "package_id": "0x",
                "token_registry": "0x",
                "account_registry": "0x",
            },
            "mainnet": {
                "package_id": "0x",
                "token_registry": "0x",
                "account_registry": "0x",
            },
        }
        well_known_network_types = {
            "devnet": NetworkType.DEVELOP,
            "testnet": NetworkType.TEST,
            "mainnet": NetworkType.PRODUCTION,
        }
        model: _PrivateFundsConfigModel = _PrivateFundsConfigModel(
            version=_CURRENT_PRIVATEFUNDS_CONFIG_VERSION,
            groups=[
                PrivateFundsGroup(
                    name=name,
                    network_type=well_known_network_types.get(name),
                    **ids,
                )
                for name, ids in network_ids.items()
            ],
        )
        self._config_root.mkdir(parents=True, exist_ok=True)
        self._config_file.write_text(model.to_json(indent=2))

    def _match_active_group(
        self, *, pysui_config: PysuiConfiguration
    ) -> PrivateFundsGroup:
        """Resolve and validate the group for the active PysuiConfiguration profile.

        :param pysui_config: The active pysui configuration
        :type pysui_config: PysuiConfiguration
        :raises ValueError: If the active group protocol is not GraphQL or gRPC; if
            no group name matches the active profile; if the matched group's ids
            are still placeholders; or if the matched group's network_type does not
            match the active PysuiConfiguration profile's network_type
        :returns: The matched and validated group
        :rtype: PrivateFundsGroup
        """
        # Gate 1 — transport must be GraphQL or gRPC.
        protocol: GroupProtocol = pysui_config.active_group.group_protocol
        if protocol not in (GroupProtocol.GRAPHQL, GroupProtocol.GRPC):
            raise ValueError(
                "PrivateFundsConfig requires the active PysuiConfiguration group to "
                "use GraphQL or gRPC transport; active protocol is "
                f"'{protocol.to_string()}'."
            )
        # Gate 2 — a group name must match the active profile name.
        profile_name: str = pysui_config.active_profile
        matched: Optional[PrivateFundsGroup] = next(
            (group for group in self._model.groups if group.name == profile_name),
            None,
        )
        if matched is None:
            raise ValueError(
                f"No PrivateFundsConfig group named '{profile_name}'.  Rename the "
                f"target group in PrivateFundsConfig to '{profile_name}' to match "
                "the active PysuiConfiguration profile."
            )
        # Gate 3 — the matched group's ids must be configured (not placeholders).
        for label, value in (
            ("packageId", matched.package_id),
            ("tokenRegistry", matched.token_registry),
            ("accountRegistry", matched.account_registry),
        ):
            if len(value) <= 2:
                raise ValueError(
                    f"PrivateFundsConfig group '{profile_name}' has an unconfigured "
                    f"{label} ('{value}').  Set a valid object id before use."
                )
        # Gate 4 — the matched group's network_type must equal the active
        # PysuiConfiguration profile's network_type.
        active_network_type: Optional[NetworkType] = (
            pysui_config.active_group.active_profile.network_type
        )
        if matched.network_type != active_network_type:
            matched_str = (
                matched.network_type.to_string() if matched.network_type else "unset"
            )
            active_str = (
                active_network_type.to_string() if active_network_type else "unset"
            )
            raise ValueError(
                f"PrivateFundsConfig group '{profile_name}' has network_type "
                f"'{matched_str}', which does not match the active "
                f"PysuiConfiguration profile's network_type '{active_str}'."
            )
        return matched

    def add_group(
        self,
        *,
        name: str,
        network_type: NetworkType,
        package_id: str,
        token_registry: str,
        account_registry: str,
        persist: bool = False,
    ) -> PrivateFundsGroup:
        """Add a new PrivateFundsConfig group.

        :param name: Identifier for the new group; should match a PysuiConfiguration profile name
        :type name: str
        :param network_type: The Sui network type for this group
        :type network_type: NetworkType
        :param package_id: Confidential Transfer package id for this network
        :type package_id: str
        :param token_registry: TokenRegistry shared-object id for this network
        :type token_registry: str
        :param account_registry: AccountRegistry shared-object id for this network
        :type account_registry: str
        :param persist: Save the configuration after adding, defaults to False
        :type persist: bool, optional
        :raises ValueError: If a group with this name already exists or network_type is invalid
        :return: The newly created PrivateFundsGroup
        :rtype: PrivateFundsGroup
        """
        if network_type is None or not isinstance(network_type, NetworkType):
            raise ValueError(f"'{network_type}' is not a valid NetworkType")
        if any(g.name == name for g in self._model.groups):
            raise ValueError(f"Group '{name}' already exists")
        group = PrivateFundsGroup(
            name=name,
            package_id=package_id,
            token_registry=token_registry,
            account_registry=account_registry,
            network_type=network_type,
        )
        self._model.groups.append(group)
        if persist:
            self.save()
        return group

    def update_group(
        self,
        *,
        name: str,
        network_type: Optional[NetworkType] = None,
        package_id: Optional[str] = None,
        token_registry: Optional[str] = None,
        account_registry: Optional[str] = None,
        persist: bool = True,
    ) -> PrivateFundsGroup:
        """Update an existing PrivateFundsConfig group.

        Unspecified parameters leave the corresponding field unchanged.

        :param name: Identifier of the group to update
        :type name: str
        :param network_type: The Sui network type for this group, defaults to None (unchanged)
        :type network_type: Optional[NetworkType], optional
        :param package_id: Confidential Transfer package id, defaults to None (unchanged)
        :type package_id: Optional[str], optional
        :param token_registry: TokenRegistry shared-object id, defaults to None (unchanged)
        :type token_registry: Optional[str], optional
        :param account_registry: AccountRegistry shared-object id, defaults to None (unchanged)
        :type account_registry: Optional[str], optional
        :param persist: Save the configuration after updating, defaults to True
        :type persist: bool, optional
        :raises ValueError: If no group with this name exists
        :return: The updated PrivateFundsGroup
        :rtype: PrivateFundsGroup
        """
        group = next((g for g in self._model.groups if g.name == name), None)
        if group is None:
            raise ValueError(f"Group '{name}' does not exist")
        group.network_type = network_type or group.network_type
        group.package_id = package_id or group.package_id
        group.token_registry = token_registry or group.token_registry
        group.account_registry = account_registry or group.account_registry
        if persist:
            self.save()
        return group
