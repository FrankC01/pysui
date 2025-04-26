
gRPC
""""

MystenLab has exposed a lower level data protcol using Google Protobuffs. This change is part of the
transitions from JSON RPC node interactions which is planned to sunset in 2026.

``pysui`` has added support for interacting with the Sui gRPC node. This is currently in beta and only available
on testnet and mainnet.

At the time of this writing, there are limitations to Sui gRPC and only offers simple data fetch and transaction execution interfaces.

====================
Subject to Change
====================

pysui's gRPC implementation, class names, etc. subject to change. This implementation is not production ready and should be considered experiemental.

===================
pysui gRPC services
===================

There are currently 2 gRPC services clients available in pysui:

#. LedgerClient
    Provides basic data query methods
#. TxClient
    Provides methods to submit transactions

These clients are fetched from the main gRPC client, for example:

.. code-block:: python

    from pysui import PysuiConfiguration

    from pysui.sui.sui_grpc.pgrpc_clients import (
        SuiGrpcClient,
        LedgerClient,
        TxClient,
    )

    async def main(pcfg: PysuiConfiguration):
        """Access gRPC clients."""

        # Base client (factory) requires URL
        grpc_client: SuiGrpcClient = SuiGrpcClient(
            pysui_config=pcfg, grpc_node_url="fullnode.testnet.sui.io:443"
        )

        # Create specific service clients
        ledger_client: LedgerClient = grpc_client.ledger_client()
        txn_client: TxClient = grpc_client.transaction_client()

        # Always close the factory client
        grpc_client.close()


    if __name__ == "__main__":
        try:
            cfg = PysuiConfiguration(
                group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP, profile_name="testnet"
            )

            asyncio.run(main(cfg))
        except ValueError as ve:
            print(ve)


Notes:

#. All service clients are asynchronus
#. All gRPC calls return a ``SuiRpcResult``
#. All data results are of type ``dataclass``
#. A service client may be instantiated with a different URL than the factory client
