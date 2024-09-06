#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Schema management module."""

from gql import Client, gql
from gql.client import ReconnectingAsyncClientSession
import httpx

from gql.transport.httpx import HTTPXTransport
from gql.transport.httpx import HTTPXAsyncTransport

from gql.dsl import (
    DSLSchema,
)
from pysui.sui.sui_pgql.pgql_configs import pgql_config, SuiConfigGQL


class Schema:
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
                Schema.SCHEMA_HEADER_SCHEMA_KEY
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
    async def async_session(self) -> ReconnectingAsyncClientSession:
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
