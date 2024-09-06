#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Schema management module."""

from typing import Any, Optional
from gql import Client, gql
from gql.client import ReconnectingAsyncClientSession
import httpx

from gql.transport.httpx import HTTPXTransport
from gql.transport.httpx import HTTPXAsyncTransport

from gql.transport import exceptions as texc
from gql.dsl import (
    DSLSchema,
)
from pysui.sui.sui_pgql.pgql_configs import pgql_config, SuiConfigGQL


class Schema:

    RPC_CFG = "rpc_config"
    DSCHEMA = "schema"
    GCLIENT = "client"
    ASYNCSESS = "async_client"
    GURL = "url"
    BUILD = "build_version"
    SCHEMA_HEADER_SCHEMA_KEY: str = "x-sui-rpc-version"

    def __init__(self, active_schemas: list, default: str):
        """__init__ Initialize schema

        :param active_schemas: Collection of active schemas
        :type active_schemas: list
        :param default: The schema to default to
        :type default: str
        :raises ValueError: If the default is not in the active schemas
        :raises ValueError: No default provided
        """
        active_schemas.sort(reverse=True)
        if default and default not in active_schemas:
            active_schemas.insert(0, default)
        elif not default:
            raise ValueError("Must set default schema in cache")

        self._default_version = default
        self._last_version = default
        self._schemas: dict[str, dict[str, Any]] = {}
        self._all_versions = active_schemas
        self._present_schemas = set(active_schemas)

    @property
    def default_version(self) -> str:
        """Fetch default version of schema."""
        return self._default_version

    @property
    def last_version(self) -> str:
        """Fetch the last version used."""
        return self._last_version

    @property
    def schema_set(self) -> dict[str, dict[str, Any]]:
        """Fetch the entire schema set"""
        return self._schemas

    def _cache_schema_set(
        self,
        graphql_url: str,
        graphql_client: Any,
        schema_key: str,
        schema_long: str,
        dschema: DSLSchema,
        rconfig: SuiConfigGQL,
    ):
        """Insert a unique schema in the collection."""
        if schema_key not in self._schemas:
            self._schemas[schema_key] = {
                self.GURL: graphql_url,  # Covered
                self.GCLIENT: graphql_client,  # Covered
                self.BUILD: schema_long,  # Covered
                self.DSCHEMA: dschema,  # Covered
                self.RPC_CFG: rconfig,  # Covered
                self.ASYNCSESS: None,
            }
            if schema_key in self._present_schemas:
                self._present_schemas.remove(schema_key)


class NewSchema:
    """."""

    SCHEMA_HEADER_SCHEMA_KEY: str = "x-sui-rpc-version"

    def __init__(self, *, gql_url: str, gql_env: str):
        """."""
        _init_client: Client = Client(
            transport=HTTPXTransport(
                url=gql_url,
                verify=True,
                http2=True,
                timeout=120.0,
            ),
            fetch_schema_from_transport=True,
        )
        with _init_client as session:
            _long_version = session.transport.response_headers[
                NewSchema.SCHEMA_HEADER_SCHEMA_KEY
            ]
            _base_version = ".".join(_long_version.split(".")[:2])
            _schema: DSLSchema = DSLSchema(_init_client.schema)
            qstr, fndeser = pgql_config(gql_env, _base_version)
            _rpc_config: SuiConfigGQL = fndeser(session.execute(gql(qstr)))
            _rpc_config.gqlEnvironment = gql_env
            self._base_version: str = _base_version
            self._build_version: str = _long_version
            self._rpc_config: SuiConfigGQL = _rpc_config
            self._dsl_schema: DSLSchema = _schema
            self._graph_url: str = gql_url
            self._sync_client: Client = _init_client
            self._async_client: Client = None
            self._async_session: ReconnectingAsyncClientSession = None

    @property
    def base_version(self) -> str:
        """."""
        return self._base_version

    @property
    def build_version(self) -> str:
        """."""
        return self._build_version

    @property
    def rpc_config(self) -> SuiConfigGQL:
        """."""
        return self._rpc_config

    @property
    def dsl_schema(self) -> DSLSchema:
        """."""
        return self._dsl_schema

    @property
    def client(self) -> Client:
        """."""
        return self._sync_client

    @property
    async def async_client(self) -> ReconnectingAsyncClientSession:
        """."""
        if not self._async_session and self._async_client:
            self._async_session = await self._async_client.connect_async(
                reconnecting=True
            )
        return self._async_session

    def set_async_client(self):
        """."""
        self._async_client = Client(
            transport=HTTPXAsyncTransport(
                url=self._graph_url,
                verify=True,
                http2=True,
                timeout=120.0,
            ),
        )


def load_schema_cache(gurl: str, genv: str) -> Schema:
    """."""
    schema_mgr: Schema = None
    # Initialize the base
    _init_client: Client = Client(
        transport=HTTPXTransport(
            url=gurl,
            verify=True,
            http2=True,
            timeout=120.0,
        ),
        fetch_schema_from_transport=True,
    )
    with _init_client as session:
        _long_version = session.transport.response_headers[
            Schema.SCHEMA_HEADER_SCHEMA_KEY
        ]
        _base_version = ".".join(_long_version.split(".")[:2])
        _schema: DSLSchema = DSLSchema(_init_client.schema)
        qstr, fndeser = pgql_config(genv, _base_version)
        _rpc_config: SuiConfigGQL = fndeser(session.execute(gql(qstr)))
        schema_mgr = Schema(_rpc_config.serviceConfig.availableVersions, _base_version)
        _rpc_config.gqlEnvironment = genv
        schema_mgr._cache_schema_set(
            gurl, _init_client, _base_version, _long_version, _schema, _rpc_config
        )
        return schema_mgr
