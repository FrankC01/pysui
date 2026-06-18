#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""ZkSeal configuration: ZkSealConfig, ZkSealNetworkGroup, ZkLoginProvider, SealKeyServer, SealKeyServerSet."""

import dataclasses
import pathlib
from typing import Optional

import dataclasses_json

from pysui import AsyncClientBase, GetDynamicFields


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ZkLoginProvider:
    """Represents a zkLogin OAuth provider configuration.

    :param name: Identifier for the provider (e.g. "google", "facebook", "twitch")
    :type name: str
    :param iss: The JWT issuer URL for this provider
    :type iss: str
    :param prover_url: URL of the zkLogin proof generation service
    :type prover_url: str
    """

    name: str
    iss: str
    prover_url: str


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class SealKeyServer:
    """Represents a single SEAL key server endpoint.

    :param alias: Human-readable identifier for this server
    :type alias: str
    :param object_id: On-chain Sui object ID for the key server
    :type object_id: str
    :param url: Base URL of the key server
    :type url: str
    """

    alias: str
    object_id: str
    url: str


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class SealKeyServerSet:
    """A named collection of SEAL key servers forming a set or committee.

    :param name: Identifier for this server set
    :type name: str
    :param is_committee: True if this set acts as a committee (aggregator)
    :type is_committee: bool
    :param servers: Key servers belonging to this set, defaults to empty list
    :type servers: list[SealKeyServer], optional
    """

    name: str
    is_committee: bool
    servers: list[SealKeyServer] = dataclasses.field(default_factory=list)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ZkSealNetworkGroup:
    """Configuration group for a specific Sui network environment.

    :param group_name: The network identifier (e.g. "devnet", "testnet", "mainnet")
    :type group_name: str
    :param zklogin_providers: zkLogin OAuth providers for this network, defaults to empty list
    :type zklogin_providers: list[ZkLoginProvider], optional
    :param key_server_sets: SEAL key server sets for this network, defaults to empty list
    :type key_server_sets: list[SealKeyServerSet], optional
    """

    group_name: str
    zklogin_providers: list[ZkLoginProvider] = dataclasses.field(default_factory=list)
    key_server_sets: list[SealKeyServerSet] = dataclasses.field(default_factory=list)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class _ZkSealConfigModel:
    """Internal serialization model for ZkSealConfig JSON persistence.

    :param version: Configuration schema version, defaults to 1
    :type version: int, optional
    :param groups: Network groups defined in this configuration, defaults to empty list
    :type groups: list[ZkSealNetworkGroup], optional
    """

    version: int = 1
    active_group_name: Optional[str] = None
    groups: list[ZkSealNetworkGroup] = dataclasses.field(default_factory=list)


class ZkSealConfig:
    """Configuration manager for zkLogin and SEAL key server settings across Sui networks.

    Persists to ``~/.pysui/ZkSealConfig.json`` by default and provides CRUD operations
    for network groups, zkLogin providers, SEAL key server sets, and individual servers.
    """

    def __init__(
        self,
        *,
        from_cfg_path: Optional[str] = None,
        group_name: Optional[str] = None,
        persist: bool = False,
    ) -> None:
        """Initialize ZkSealConfig, creating the default configuration if absent.

        :param from_cfg_path: Path to directory containing ZkSealConfig.json; defaults to ~/.pysui
        :type from_cfg_path: Optional[str], optional
        :param group_name: Network group to activate on load; defaults to the persisted active group name, then the first group
        :type group_name: Optional[str], optional
        :param persist: Save the configuration after activation, defaults to False
        :type persist: bool, optional
        :raises ValueError: If from_cfg_path is given but ZkSealConfig.json does not exist there
        """
        self._config_root = pathlib.Path(from_cfg_path or "~/.pysui").expanduser()
        self._config_file = self._config_root / "ZkSealConfig.json"
        if not self._config_file.exists():
            if from_cfg_path is not None:
                raise ValueError(f"{self._config_file} does not exist.")
            self._initialize_config()
        self._model: _ZkSealConfigModel = _ZkSealConfigModel.from_json(
            self._config_file.read_text()
        )
        self._active_group: Optional[ZkSealNetworkGroup] = None
        self.make_active(group_name=group_name, persist=persist)

    @staticmethod
    def default_path() -> pathlib.Path:
        """Return the default path for ZkSealConfig.json.

        :return: Absolute path to ~/.pysui/ZkSealConfig.json
        :rtype: pathlib.Path
        """
        return pathlib.Path.home() / ".pysui" / "ZkSealConfig.json"

    @classmethod
    def _initialize_config(cls, *, from_cfg_path: Optional[str] = None) -> None:
        """Write a default ZkSealConfig.json with built-in devnet/testnet/mainnet groups.

        :param from_cfg_path: Target directory for the config file; defaults to ~/.pysui
        :type from_cfg_path: Optional[str], optional
        :raises ValueError: If a ZkSealConfig.json already exists at the target path
        """
        config_root = pathlib.Path(from_cfg_path or "~/.pysui").expanduser()
        config_file = config_root / "ZkSealConfig.json"
        if config_file.exists():
            raise ValueError(f"ZkSealConfig already exists at {config_file}")
        model = _ZkSealConfigModel(
            active_group_name="testnet",
            groups=[
                ZkSealNetworkGroup(
                    group_name="devnet",
                    zklogin_providers=[
                        ZkLoginProvider(name="google", iss="https://accounts.google.com", prover_url="https://prover-dev.mystenlabs.com/v1"),
                        ZkLoginProvider(name="facebook", iss="https://www.facebook.com", prover_url="https://prover-dev.mystenlabs.com/v1"),
                        ZkLoginProvider(name="twitch", iss="https://id.twitch.tv/oauth2", prover_url="https://prover-dev.mystenlabs.com/v1"),
                    ],
                    key_server_sets=[],
                ),
                ZkSealNetworkGroup(
                    group_name="testnet",
                    zklogin_providers=[
                        ZkLoginProvider(name="google", iss="https://accounts.google.com", prover_url="https://prover-dev.mystenlabs.com/v1"),
                        ZkLoginProvider(name="facebook", iss="https://www.facebook.com", prover_url="https://prover-dev.mystenlabs.com/v1"),
                        ZkLoginProvider(name="twitch", iss="https://id.twitch.tv/oauth2", prover_url="https://prover-dev.mystenlabs.com/v1"),
                    ],
                    key_server_sets=[
                        SealKeyServerSet(
                            name="mysten-testnet",
                            is_committee=False,
                            servers=[
                                SealKeyServer(alias="mysten-testnet-1", object_id="0x73d05d62c18d9374e3ea529e8e0ed6161da1a141a94d3f76ae3fe4e99356db75", url="https://seal-key-server-testnet-1.mystenlabs.com"),
                                SealKeyServer(alias="mysten-testnet-2", object_id="0xf5d14a81a982144ae441cd7d64b09027f116a468bd36e7eca494f750591623c8", url="https://seal-key-server-testnet-2.mystenlabs.com"),
                            ],
                        ),
                        SealKeyServerSet(
                            name="mysten-testnet-committee",
                            is_committee=True,
                            servers=[
                                SealKeyServer(alias="mysten-committee", object_id="0xb012378c9f3799fb5b1a7083da74a4069e3c3f1c93de0b27212a5799ce1e1e98", url="https://seal-aggregator-testnet.mystenlabs.com"),
                            ],
                        ),
                    ],
                ),
                ZkSealNetworkGroup(
                    group_name="mainnet",
                    zklogin_providers=[
                        ZkLoginProvider(name="google", iss="https://accounts.google.com", prover_url="https://prover.mystenlabs.com/v1"),
                        ZkLoginProvider(name="facebook", iss="https://www.facebook.com", prover_url="https://prover.mystenlabs.com/v1"),
                        ZkLoginProvider(name="twitch", iss="https://id.twitch.tv/oauth2", prover_url="https://prover.mystenlabs.com/v1"),
                    ],
                    key_server_sets=[],
                ),
            ]
        )
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(model.to_json(indent=2))

    def save(self, path: Optional[pathlib.Path] = None) -> None:
        """Persist the current configuration to disk.

        :param path: Destination file path; defaults to the path used at construction
        :type path: Optional[pathlib.Path], optional
        """
        target = path or self._config_file
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self._model.to_json(indent=2))

    @property
    def active_group(self) -> ZkSealNetworkGroup:
        """Return the currently active network group, defaulting to the first group.

        :return: The active ZkSealNetworkGroup
        :rtype: ZkSealNetworkGroup
        :raises RuntimeError: If no groups are configured
        """
        if self._active_group is None:
            if not self._model.groups:
                raise RuntimeError("No groups configured in ZkSealConfig")
            self._active_group = self._model.groups[0]
        return self._active_group

    def make_active(
        self, *, group_name: Optional[str] = None, persist: bool = False
    ) -> "ZkSealConfig":
        """Set the active network group by name.

        :param group_name: Name of the group to activate; if None, keeps existing or defaults to first
        :type group_name: Optional[str], optional
        :param persist: Save the configuration after activation, defaults to False
        :type persist: bool, optional
        :return: Self, for chaining
        :rtype: ZkSealConfig
        :raises ValueError: If group_name is given but does not match any configured group
        """
        if group_name:
            group = next((g for g in self._model.groups if g.group_name == group_name), None)
            if group is None:
                raise ValueError(f"Network group '{group_name}' not found")
            self._active_group = group
            self._model.active_group_name = group_name
        elif self._active_group is None:
            resolved = self._model.active_group_name
            if resolved:
                group = next((g for g in self._model.groups if g.group_name == resolved), None)
                if group is None:
                    raise ValueError(
                        f"Persisted active group '{resolved}' no longer exists; "
                        "call make_active(group_name=...) to set a valid group"
                    )
                self._active_group = group
            elif self._model.groups:
                self._active_group = self._model.groups[0]
        if persist:
            self.save()
        return self

    # --- Group CRUD ---

    def add_group(self, *, group_name: str, persist: bool = False) -> ZkSealNetworkGroup:
        """Add a new empty network group.

        :param group_name: Identifier for the new group
        :type group_name: str
        :param persist: Save the configuration after adding, defaults to False
        :type persist: bool, optional
        :return: The newly created ZkSealNetworkGroup
        :rtype: ZkSealNetworkGroup
        :raises ValueError: If a group with this name already exists
        """
        if any(g.group_name == group_name for g in self._model.groups):
            raise ValueError(f"Group '{group_name}' already exists")
        group = ZkSealNetworkGroup(group_name=group_name)
        self._model.groups.append(group)
        if persist:
            self.save()
        return group

    def remove_group(self, *, group_name: str, persist: bool = False) -> None:
        """Remove a network group and clear the active group if it was the removed one.

        :param group_name: Identifier of the group to remove
        :type group_name: str
        :param persist: Save the configuration after removal, defaults to False
        :type persist: bool, optional
        """
        self._model.groups = [g for g in self._model.groups if g.group_name != group_name]
        if self._active_group and self._active_group.group_name == group_name:
            self._active_group = None
        if persist:
            self.save()

    def _get_group(self, group_name: str) -> ZkSealNetworkGroup:
        """Retrieve a network group by name.

        :param group_name: Identifier of the group to retrieve
        :type group_name: str
        :return: The matching ZkSealNetworkGroup
        :rtype: ZkSealNetworkGroup
        :raises ValueError: If no group with this name exists
        """
        group = next((g for g in self._model.groups if g.group_name == group_name), None)
        if group is None:
            raise ValueError(f"Network group '{group_name}' not found")
        return group

    # --- Provider CRUD ---

    def add_provider(
        self,
        *,
        group_name: str,
        name: str,
        iss: str,
        prover_url: str,
        persist: bool = False,
    ) -> None:
        """Add a zkLogin OAuth provider to a network group.

        :param group_name: Target network group identifier
        :type group_name: str
        :param name: Provider identifier (e.g. "google")
        :type name: str
        :param iss: JWT issuer URL for this provider
        :type iss: str
        :param prover_url: URL of the zkLogin proof generation service
        :type prover_url: str
        :param persist: Save the configuration after adding, defaults to False
        :type persist: bool, optional
        :raises ValueError: If the provider name already exists in the group
        """
        group = self._get_group(group_name)
        if any(p.name == name for p in group.zklogin_providers):
            raise ValueError(f"Provider '{name}' already exists in group '{group_name}'")
        group.zklogin_providers.append(ZkLoginProvider(name=name, iss=iss, prover_url=prover_url))
        if persist:
            self.save()

    def remove_provider(self, *, group_name: str, name: str, persist: bool = False) -> None:
        """Remove a zkLogin OAuth provider from a network group.

        :param group_name: Target network group identifier
        :type group_name: str
        :param name: Provider identifier to remove
        :type name: str
        :param persist: Save the configuration after removal, defaults to False
        :type persist: bool, optional
        """
        group = self._get_group(group_name)
        group.zklogin_providers = [p for p in group.zklogin_providers if p.name != name]
        if persist:
            self.save()

    def update_provider_url(
        self, *, group_name: str, name: str, prover_url: str, persist: bool = False
    ) -> None:
        """Update the prover URL for an existing zkLogin provider.

        :param group_name: Target network group identifier
        :type group_name: str
        :param name: Provider identifier to update
        :type name: str
        :param prover_url: New proof generation service URL
        :type prover_url: str
        :param persist: Save the configuration after updating, defaults to False
        :type persist: bool, optional
        :raises ValueError: If the provider name does not exist in the group
        """
        group = self._get_group(group_name)
        provider = next((p for p in group.zklogin_providers if p.name == name), None)
        if provider is None:
            raise ValueError(f"Provider '{name}' not found in group '{group_name}'")
        provider.prover_url = prover_url
        if persist:
            self.save()

    # --- Key server set CRUD ---

    def _get_server_set(self, group_name: str, set_name: str) -> SealKeyServerSet:
        """Retrieve a SEAL key server set by group and set name.

        :param group_name: Target network group identifier
        :type group_name: str
        :param set_name: Name of the key server set
        :type set_name: str
        :return: The matching SealKeyServerSet
        :rtype: SealKeyServerSet
        :raises ValueError: If the group or set does not exist
        """
        group = self._get_group(group_name)
        server_set = next((s for s in group.key_server_sets if s.name == set_name), None)
        if server_set is None:
            raise ValueError(f"Key server set '{set_name}' not found in group '{group_name}'")
        return server_set

    def add_key_server_set(
        self,
        *,
        group_name: str,
        set_name: str,
        is_committee: bool,
        persist: bool = False,
    ) -> None:
        """Add a new SEAL key server set to a network group.

        :param group_name: Target network group identifier
        :type group_name: str
        :param set_name: Name for the new server set
        :type set_name: str
        :param is_committee: True if this set acts as a committee (aggregator)
        :type is_committee: bool
        :param persist: Save the configuration after adding, defaults to False
        :type persist: bool, optional
        :raises ValueError: If a set with this name already exists in the group
        """
        group = self._get_group(group_name)
        if any(s.name == set_name for s in group.key_server_sets):
            raise ValueError(f"Key server set '{set_name}' already exists in group '{group_name}'")
        group.key_server_sets.append(SealKeyServerSet(name=set_name, is_committee=is_committee))
        if persist:
            self.save()

    def remove_key_server_set(
        self, *, group_name: str, set_name: str, persist: bool = False
    ) -> None:
        """Remove a SEAL key server set from a network group.

        :param group_name: Target network group identifier
        :type group_name: str
        :param set_name: Name of the server set to remove
        :type set_name: str
        :param persist: Save the configuration after removal, defaults to False
        :type persist: bool, optional
        """
        group = self._get_group(group_name)
        group.key_server_sets = [s for s in group.key_server_sets if s.name != set_name]
        if persist:
            self.save()

    def list_sets(self, *, group_name: str) -> list[str]:
        """Return the names of all SEAL key server sets in a network group.

        :param group_name: Target network group identifier
        :type group_name: str
        :return: List of server set names
        :rtype: list[str]
        """
        group = self._get_group(group_name)
        return [s.name for s in group.key_server_sets]

    # --- Key server CRUD (within a set) ---

    def add_server(
        self,
        *,
        group_name: str,
        set_name: str,
        alias: str,
        object_id: str,
        url: str,
        persist: bool = False,
    ) -> None:
        """Add a SEAL key server to a server set.

        :param group_name: Target network group identifier
        :type group_name: str
        :param set_name: Target server set name
        :type set_name: str
        :param alias: Human-readable identifier for the server
        :type alias: str
        :param object_id: On-chain Sui object ID for the key server
        :type object_id: str
        :param url: Base URL of the key server
        :type url: str
        :param persist: Save the configuration after adding, defaults to False
        :type persist: bool, optional
        :raises ValueError: If an entry with this alias already exists in the set
        """
        server_set = self._get_server_set(group_name, set_name)
        if any(s.alias == alias for s in server_set.servers):
            raise ValueError(f"Server alias '{alias}' already exists in set '{set_name}'")
        server_set.servers.append(SealKeyServer(alias=alias, object_id=object_id, url=url))
        if persist:
            self.save()

    def remove_server(
        self, *, group_name: str, set_name: str, alias: str, persist: bool = False
    ) -> None:
        """Remove a SEAL key server from a server set.

        :param group_name: Target network group identifier
        :type group_name: str
        :param set_name: Target server set name
        :type set_name: str
        :param alias: Alias of the server to remove
        :type alias: str
        :param persist: Save the configuration after removal, defaults to False
        :type persist: bool, optional
        """
        server_set = self._get_server_set(group_name, set_name)
        server_set.servers = [s for s in server_set.servers if s.alias != alias]
        if persist:
            self.save()

    def update_server_url(
        self,
        *,
        group_name: str,
        set_name: str,
        alias: str,
        url: str,
        persist: bool = False,
    ) -> None:
        """Update the URL for an existing SEAL key server.

        :param group_name: Target network group identifier
        :type group_name: str
        :param set_name: Target server set name
        :type set_name: str
        :param alias: Alias of the server to update
        :type alias: str
        :param url: New server URL
        :type url: str
        :param persist: Save the configuration after updating, defaults to False
        :type persist: bool, optional
        :raises ValueError: If the alias does not exist in the set
        """
        server_set = self._get_server_set(group_name, set_name)
        server = next((s for s in server_set.servers if s.alias == alias), None)
        if server is None:
            raise ValueError(f"Server alias '{alias}' not found in set '{set_name}'")
        server.url = url
        if persist:
            self.save()

    def get_server(
        self, *, group_name: str, set_name: str, alias: str
    ) -> Optional[SealKeyServer]:
        """Return a SEAL key server by alias, or None if not found.

        :param group_name: Target network group identifier
        :type group_name: str
        :param set_name: Target server set name
        :type set_name: str
        :param alias: Alias of the server to retrieve
        :type alias: str
        :return: The matching SealKeyServer, or None
        :rtype: Optional[SealKeyServer]
        """
        try:
            server_set = self._get_server_set(group_name, set_name)
            return next((s for s in server_set.servers if s.alias == alias), None)
        except ValueError:
            return None

    def resolve_server(
        self, *, group_name: str, set_name: str, alias_or_object_id: str
    ) -> Optional[SealKeyServer]:
        """Return a SEAL key server matching alias or object_id, or None if not found.

        :param group_name: Target network group identifier
        :type group_name: str
        :param set_name: Target server set name
        :type set_name: str
        :param alias_or_object_id: Server alias or on-chain object ID to match
        :type alias_or_object_id: str
        :return: The matching SealKeyServer, or None
        :rtype: Optional[SealKeyServer]
        """
        try:
            server_set = self._get_server_set(group_name, set_name)
        except ValueError:
            return None
        return next(
            (
                s
                for s in server_set.servers
                if s.alias == alias_or_object_id or s.object_id == alias_or_object_id
            ),
            None,
        )

    async def refresh_all_server_urls(self, *, client: AsyncClientBase) -> None:
        """Refresh all SEAL key server URLs across every group and set from on-chain dynamic fields.

        :param client: Async pysui client used to query the chain
        :type client: AsyncClientBase
        """
        for group in self._model.groups:
            for server_set in group.key_server_sets:
                if server_set.is_committee:
                    continue
                for server in server_set.servers:
                    server.url = await self._fetch_server_url(
                        object_id=server.object_id, client=client
                    )
        self.save()

    async def _fetch_server_url(self, *, object_id: str, client: AsyncClientBase) -> str:
        """Fetch the URL from a key server's on-chain dynamic fields.

        :param object_id: On-chain Sui object ID for the key server
        :type object_id: str
        :param client: Async pysui client used to query the chain
        :type client: AsyncClientBase
        :return: The URL string extracted from the dynamic field value
        :rtype: str
        :raises ValueError: If the execute fails, no dynamic fields exist, or the URL cannot be extracted
        """
        result = await client.execute(command=GetDynamicFields(object_id=object_id))
        if not result.is_ok():
            raise ValueError(f"Failed to fetch dynamic fields for '{object_id}': {result.result_string}")
        dfields = result.result_data.dynamic_fields
        if not dfields:
            raise ValueError(f"No dynamic fields found for object '{object_id}'")
        field = dfields[0].field_object
        if field is None or field.json is None:
            raise ValueError(f"Dynamic field for '{object_id}' has no JSON value")
        data = field.json.to_dict()
        url = data.get("value", {}).get("url")
        if not url:
            raise ValueError(f"Could not extract URL from dynamic field for '{object_id}'")
        return url

    async def add_verified_server(
        self,
        *,
        group_name: str,
        set_name: str,
        alias: str,
        object_id: str,
        client: AsyncClientBase,
    ) -> None:
        """Resolve the key server URL from on-chain dynamic fields and add it to a set.

        :param group_name: Target network group identifier
        :type group_name: str
        :param set_name: Target server set name
        :type set_name: str
        :param alias: Human-readable identifier for the server
        :type alias: str
        :param object_id: On-chain Sui object ID for the key server
        :type object_id: str
        :param client: Async pysui client used to query the chain
        :type client: AsyncClientBase
        """
        url = await self._fetch_server_url(object_id=object_id, client=client)
        self.add_server(group_name=group_name, set_name=set_name, alias=alias, object_id=object_id, url=url)
        self.save()

    async def refresh_server_url(
        self,
        *,
        group_name: str,
        set_name: str,
        alias: str,
        client: AsyncClientBase,
    ) -> None:
        """Refresh a key server's URL by fetching the current value from on-chain dynamic fields.

        :param group_name: Target network group identifier
        :type group_name: str
        :param set_name: Target server set name
        :type set_name: str
        :param alias: Alias of the server to refresh
        :type alias: str
        :param client: Async pysui client used to query the chain
        :type client: AsyncClientBase
        :raises ValueError: If the alias does not exist in the set
        """
        server_set = self._get_server_set(group_name, set_name)
        server = next((s for s in server_set.servers if s.alias == alias), None)
        if server is None:
            raise ValueError(f"Server alias '{alias}' not found in set '{set_name}'")
        server.url = await self._fetch_server_url(object_id=server.object_id, client=client)
        self.save()
