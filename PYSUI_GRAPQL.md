# Sui GraphQL RPC ALPHA

MystenLabs announcement can be found [Here](https://github.com/mystenLabs/sui/issues/13700). This change transitions
from JSON RPC to GraphQL RPC.

Note: MystenLabs/Sui GraphQL RPC is available on devnet, testnet and mainnet. Note that devnet alpha is usable but
we recommend using testnet or mainnet beta for stability. We are tracking a few failures we are monitoring [Isssues](https://github.com/FrankC01/pysui/issues?q=is%3Aissue+is%3Aopen++Sui+GraphQL+RPC).

## Sui GraphQL IDEs

  [Mainnet](https://sui-mainnet.mystenlabs.com/graphql)

  [Testnet](https://sui-testnet.mystenlabs.com/graphql)

  [Devnet](https://sui-devnet.mystenlabs.com/graphql)

### pysui GraphQL support

**Note**: Functionality of pysui GraphQl should be considered alpha, use in production at your own risk.

With pysui 0.50.0 we released alpha `pysui`'s GraphQL aligning with MystenLabs strategy. The timeline of changes will keep up with the Timeline as noted in the Sui GraphQL annoucement. We are not yet stable however we have Clients and TransactionBuilder running against Sui GraphQL.

We continue to monitor and support changes from MystenLabs as they occur.

### Examples

  - **_pgql_s_example_** - Synchronous examples for all supported QueryNode queries and mutations
  - **_pgql_a_example_** - Asynchronous examples for all supported QueryNode queries and mutations
  - **_pgql_s_ptb_** - Example of new pysui Transaction Builder leveraging Sui GraphQL

You can read pysui documentation on graphql beta [here](https://pysui.readthedocs.io/en/latest/graphql.html)

### Known Issues

- No subscription support at this time
