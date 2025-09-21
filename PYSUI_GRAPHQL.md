# Sui GraphQL ALPHA

MystenLabs announcement can be [Found Here](https://github.com/mystenLabs/sui/issues/13700). This change transitions
from JSON RPC to GraphQL RPC.

Note: MystenLabs/Sui GraphQL Beta is available on devnet, testnet and mainnet. 

## PysuiConfiguration: GraphQL URL CHANGES

If you were previously setup PysuiConfiguration with GraphQL Alpha profiles you'll **need to update**
them. Here are approahes you can use:

1. Using an editor of your choice open up ~/.pysui/PysuiConfig.json (default) and replace any GraphQL profile URLs
  to those shown in the next section.
2. Use [tpysui](https://pypi.org/project/tpysui/) `tpysui` is the Pysui configuration editor. Open (Ctrl+f) the
  appropriate PysuiConfig.json and edit profile URLs.

## Sui GraphQL URL AND IDEs CHANGES

  [Mainnet](https://graphql.mainnet.sui.io/graphql) `https://graphql.mainnet.sui.io/graphql`

  [Testnet](https://graphql.testnet.sui.io/graphql) `https://graphql.testnet.sui.io/graphql`

  [Devnet](https://graphql.devnet.sui.io/graphql) `https://graphql.devnet.sui.io/graphql`

### pysui GraphQL support

**Note**: Functionality of pysui GraphQl should be considered BETA, use in production at your own risk.

With pysui 0.91.0 we released beta `pysui`'s GraphQL aligning with MystenLabs strategy. The timeline of changes will keep up with the Timeline as noted in the Sui GraphQL annoucement. We are not yet stable however we have Clients and TransactionBuilder running against Sui GraphQL.

We continue to monitor and support changes from MystenLabs as they occur.

### Examples

  - **_pgql_s_example_** - Synchronous examples for all supported QueryNode queries and mutations
  - **_pgql_a_example_** - Asynchronous examples for all supported QueryNode queries and mutations
  - **_pgql_s_ptb_** - Example of new pysui Transaction Builder leveraging Sui GraphQL

### Known Issues

- No subscription support at this time
