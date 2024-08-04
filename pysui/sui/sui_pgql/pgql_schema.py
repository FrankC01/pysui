#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Schema management module."""

from typing import Any, Optional
from gql import Client, gql
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
        if default and default not in active_schemas:
            raise ValueError(
                f"{default} is invalid schema version. Available: {active_schemas}"
            )
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
                self.GURL: graphql_url,
                self.GCLIENT: graphql_client,
                self.BUILD: schema_long,
                self.DSCHEMA: dschema,
                self.RPC_CFG: rconfig,
                self.ASYNCSESS: None,
            }
            self._present_schemas.remove(schema_key)


def load_schema_cache(
    gurl: str, genv: str, default_version: Optional[str] = None
) -> Schema:
    """."""
    schema_mgr: Schema = None
    # TODO: Temporary Sui devnet bug workaround
    if not genv.startswith("devnet"):
        _furl = gurl + "/" + default_version if default_version else gurl
    else:
        _furl = gurl

    # Initialize the base
    _init_client: Client = Client(
        transport=HTTPXTransport(
            url=_furl,
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
        schema_mgr = Schema(
            _rpc_config.serviceConfig.availableVersions,
            default_version if default_version else _base_version,
        )
        _rpc_config.gqlEnvironment = genv
        if genv != "devnet":
            _url = gurl + "/" + _base_version
        else:
            _url = gurl
        schema_mgr._cache_schema_set(
            _url, _init_client, _base_version, _long_version, _schema, _rpc_config
        )

    if genv.startswith("devnet"):
        return schema_mgr

    while schema_mgr._present_schemas:
        _scm_ver = list(schema_mgr._present_schemas)[0]
        _url = gurl + "/" + _scm_ver
        _iclient: Client = Client(
            transport=HTTPXTransport(
                url=_url,
                verify=True,
                http2=True,
                timeout=120.0,
            ),
            fetch_schema_from_transport=True,
        )

        with _iclient as session:
            # session.fetch_schema()
            _long_version = session.transport.response_headers[
                Schema.SCHEMA_HEADER_SCHEMA_KEY
            ]
            _base_version = ".".join(_long_version.split(".")[:2])
            _schema: DSLSchema = DSLSchema(_iclient.schema)
            qstr, fndeser = pgql_config(genv, _base_version)
            try:
                _rpc_config = fndeser(session.execute(gql(qstr)))
                _rpc_config.gqlEnvironment = genv
                schema_mgr._cache_schema_set(
                    _url, _iclient, _base_version, _long_version, _schema, _rpc_config
                )
            except texc.TransportQueryError as gte:
                schema_mgr._present_schemas.remove(_base_version)
                schema_mgr._all_versions.remove(_base_version)

    return schema_mgr
