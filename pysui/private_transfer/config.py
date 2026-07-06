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
from pysui.sui.sui_common.config.confgroup import GroupProtocol


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
    """

    name: str
    package_id: str
    token_registry: str
    account_registry: str


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
    no file exists), and the group matching the active :class:`PysuiConfiguration`
    profile is resolved and validated.  The matched group is available via
    :attr:`active_group`.

    :param pysui_config: The active pysui configuration whose group protocol and
        profile name drive group resolution
    :type pysui_config: PysuiConfiguration
    :param from_cfg_path: Directory containing ``PrivateFundsConfig.json``; defaults
        to ``~/.pysui``
    :type from_cfg_path: Optional[str], optional
    :raises ValueError: If ``from_cfg_path`` is given but the file does not exist
        there; if the active group protocol is not GraphQL or gRPC; if no group
        name matches the active profile; or if the matched group's ids are unset
    """

    _CONFIG_FILE_NAME: str = "PrivateFundsConfig.json"
    _DEFAULT_DIR: str = "~/.pysui"

    def __init__(
        self,
        *,
        pysui_config: PysuiConfiguration,
        from_cfg_path: Optional[str] = None,
    ) -> None:
        """Load the configuration and resolve the active group."""
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
        # NOTE (future): an optional override may be added here to force a specific
        # group regardless of the active PysuiConfiguration profile.  For now the
        # profile name and group name must align.
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

    def _initialize_config(self) -> None:
        """Create the default configuration file with placeholder network groups.

        The default file contains ``devnet``, ``testnet`` and ``mainnet`` groups
        whose ids are the placeholder ``"0x"`` and are expected to be replaced
        with real object ids before use.
        """
        placeholder: str = "0x"
        model: _PrivateFundsConfigModel = _PrivateFundsConfigModel(
            groups=[
                PrivateFundsGroup(
                    name=name,
                    package_id=placeholder,
                    token_registry=placeholder,
                    account_registry=placeholder,
                )
                for name in ("devnet", "testnet", "mainnet")
            ]
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
            no group name matches the active profile; or if the matched group's ids
            are still placeholders
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
        return matched
