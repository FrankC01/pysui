# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.63.0] - Unpublished

### Added

### Fixed

### Changed

### Removed

## [0.62.1] - 2024-06-08

### Added

- `availableVersions` list and `mutationTimeoutMs` to ServiceConfigGQL

### Fixed

- [bug](https://github.com/FrankC01/pysui/issues/212) GraphQL GetPackage and GetFunction fail converting to dataclass
- [bug](https://github.com/FrankC01/pysui/issues/210) Passing str doesn't convert to vector<u8> (GraphQL SuiTransaction)
- Fixed handling case of unresolvable UpgradeCap fetch in GraphQL SuiTransaction `publish_upgrade``
- Regression in arg processor for GraphQL Transaction building


### Changed

- [PR](https://github.com/FrankC01/pysui/pull/211) Return address instead of failing when address already exists

### Removed

## [0.61.0] - 2024-05-28

### Added

- `GetTxKind` query node for fetching transaction type details
  - Only ProgrammableTransactionBlock, ConsensusCommitPrologueTransaction, and GenesisTransaction kinds supported
  - Added `do_tx_kind` function to synch and asynch graphql samples
- `GetFilteredTx`` query node that fetches all transactions with TransactionBlockFilter set
  - Added `do_filter_txs` function to synch and asynch graphql samples
- Passing optional global HTTP client headers in SuiGQLClient constructor.
  - Accepts a dict (e.g. `{"headers":{"...":...}}` )
  - If not provided, defaults to `{"headers":None}` (see next)
- `client_headers` property to GraphQL clients (read only, produces copy)
- `with_headers` argument to client `execute...` methods.
  - During execution, merges provided with global headers:
  ```python
    hdr = self.client_headers
    hdr = hdr if not with_headers else hdr.update(with_headers)
  ```
- Single permanent reconnecting async session for `AsyncSuiGQLClient`


### Fixed

### Changed

- Document updates (added graphql transaction builder samples)
- Bumped dataclasses-json to 0.6.6
- Sui binary support range 1.20.x -> 1.27.x

### Removed

## [0.60.0] - 2024-05-15

### Added

- `query_node_to_string` to pysui GraphQL clients
- Package object_type discriminator in ObjectReadGQL
- `do_stake` and `do_unstake` in GraphQL samples
- Support for `0x1::string::String` move call parms:
  - `&String` (e.g. `args=["foo"]`)
  - `Option<String>` (e.g. `args=["foo"]` or `args=[None]`)
  - `vector<String>` (e.g. `args=[["foo","bar"]]`)

### Fixed

### Changed

- Cursor on MovePackageGQL for modules enabled in query node GetPackage
- Cursor through all modules for `do_package` in sample
- Cursor on MoveFunctionsGQL enabled in query node GetFunctions
- Cursor on MoveStructuresGQL enabled in query node GetStructures
- Enabled cursor in query node GetValidatorsApy

### Removed

## [0.59.0] - 2024-05-02

### Added

### Fixed

- [bug](https://github.com/FrankC01/pysui/issues/201) - Parameter passing fix for JSON RPC
- [bug](https://github.com/FrankC01/pysui/issues/200) - Typo in cursor reference in sample code

### Changed

- GetTx querynode includes richer effects for object changes content.

### Removed

- `split_coin_and_return` from GraphQL SuiTransaction. Less costly to just split and transfer

## [0.58.0] - - 2024-04-22

### Added

- build_and_sign() to GraphQL SuiTransaction
- `merge_some` and `split_1_half` examples transactions in pgql_s_example.py

### Fixed

- [PR](https://github.com/FrankC01/pysui/pull/197) - Documentation
- [PR](https://github.com/FrankC01/pysui/pull/198) - Documentation


### Changed

- Bump support to Sui 1.24.0
- SuiCoinObjectGQL now supports various owner types (AddressOwner, Immutable, Shared, Parent)

### Removed

## [0.57.0] - 2024-04-15

### Added

- Support for using bech32 encoded private keys in `SuiConfig.user_config`
- Support using Sui GraphQL in devnet
- Add `gql_url` argument to support setting GraphQL RPC host URL to `SuiConfig.user_config(...)`

### Fixed

- Overlap on Validator and ValidatorSet data class
- [PR](https://github.com/FrankC01/pysui/pull/195) - Fix typo
- [PR](https://github.com/FrankC01/pysui/pull/196) - Remove useless sleep in subscription management

### Changed

- Bumped pysui-fastcrypto to 0.5.0 supporting bech32 private key encoding/decoding
- Persisted schema filename changed to `ENVIRONMENT_schema-YYYY.MAJOR.MINOR-PATCH.graphql` from `ENVIRONMENT_schema-YYYY_MAJOR_MINOR-PATCH.graphql`

### Removed

## [0.56.0] - 2024-04-02

### Added

- `walletg` in samples providing CLI using Sui GraphQL RPC
  - Includes dry run for either TransactionData or TransactionKind
  - Includes executing signed transactions

### Fixed

### Changed

- SPDX-License-Identifiers
- GraphQL support custom URL
- GraphQL clients now have explicit execute for string, DocumentNode or QueryNode
- Deprecating synch and asynch GraphQL client `execute_query`

### Removed

## [0.55.0] - 2024-03-22

### Added

- DryRun (GraphQL) result now contains return values (if any) of transaction block
- ObjectReadDeletedGQL for objects that have been wrapped into other object or deleted

### Fixed

- Removed ValueError exception if the dry run transaction block status not equal to 'SUCCESS'. This dry run is
the one invokved to obtain a budget value when none provided.
- Fixed GraphQL Protocol Configuration fetch by explictly requesting the latest known version in production.

### Changed

### Removed

## [0.54.0] - 2024-03-18

### Added

- Beta Transaction building version using GraphQL -> `from pysui.sui.sui_pgql.pgql_sync_txn import SuiTransaction`
  - Simplified interface using basic python types for all commands (split_coin, move_call, etc.)
  - Argument inferencing will encode arguments from basic python types to expected parameters
- BCS `Optional` factory for GraphQL transaction builder
- Dataclass for GraphQL Staked coins
- ObjectRef (ImmOrOwnedObject, SharedObject) added ingestion for ObjectReadGQL and SuiCoinObjectGQL
- Simple GraphQL PTB demo `pgql_s_ptb.py`

### Fixed

### Changed

- Bump Sui version support to include 1.18.x - 1.21.0

### Removed

## [0.53.0] - 2024-02-29

### Added

- DryRunTransactionKind GraphQL QueryNode

### Fixed

### Changed

- [change](https://github.com/FrankC01/pysui/issues/184) Devnet Faucet V1
- [change](https://github.com/FrankC01/pysui/issues/193) Support Sui SharedObject delete
- Deprecating chain data queries on Sync JSON-RPC SuiClient and Async JSON-RPC SuiClient
- Bumped support to Sui 1.20.0

### Removed

## [0.52.0] - 2024-02-12

### Added

- Support for GraphQL on mainnet
- Continue porting of Builders to QueryNodes for GraphQL. Note not all Builders may be ported and the data
fields and format results, while similar, are not guarenteed to be identical. See pgql_query.py for details.

### Fixed

- [bug](https://github.com/FrankC01/pysui/issues/192) Fixed pure string length encoding [PR](https://github.com/FrankC01/pysui/pull/191)

### Changed

### Removed

## [0.51.3] - Unpublished

### Added

- Continue porting of Builders to QueryNodes for GraphQL

### Fixed

- [PR](https://github.com/FrankC01/pysui/pull/188) Fixed type arguments BCS with nested type array
- [PR](https://github.com/FrankC01/pysui/pull/189) Fixed type parsing in Read Object results

### Changed

- Bumped support to Sui 1.18.0, back compatible from 1.17.x

### Removed

## [0.51.2] - 2024-01-29

** BREAKING CHANGES **

### Added

### Fixed

- [bug](https://github.com/FrankC01/pysui/issues/187) Fixed type arguments BCS with nested type array
- [bug](https://github.com/FrankC01/pysui/issues/186) sui_devInspectTransactionBlock now takes addtional args

### Changed

- **BREAKING** Sui GraphQL RPC new update, only testnet support. Most pre-defined QueryNode's changed.

### Removed

## [0.51.0] - 2024-01-20

### Added

- DEFAULT_SUI_CONFIG_PATH and DEFAULT_SUI_CLIENT_CONFIG constants
- SuiConfig.pysui_config(_path_to_folder_) - Unique client.yaml, sui.aliases and sui.keystore with persist support.

### Fixed

### Changed

### Removed

## [0.50.2] - Unpublished

### Added

### Fixed

- test_emphemeral_creates
- test_txb_publish
- Alias and GraphQL Docs

### Changed

- Bumped httpx to 0.26.x
- Changed Sui support to include >= 1.12.0 through >=0.17.0
- Allow '.' in address alias names, regex = `^[a-zA-Z][a-zA-Z0-9._-]*$`

### Removed

## [0.50.1] - 2023-12-28

### Added

### Fixed

- [bug](https://github.com/FrankC01/pysui/issues/181) Address generation from private keys included in
SuiConfig.user_config() regression.

### Changed

### Removed

## [0.50.0] - 2023-12-27

** BREAKING CHANGES **

### Added

- GraphQL (queries, fragments, client) for testnet or mainnet snapshot queries.

### Fixed

### Changed

- **Breaking**: SuiTransaction publish, publish_upgrade and custom_upgrade [args_list](https://github.com/FrankC01/pysui/issues/174)
- Wallet added alias listing and change alias
- Wallet commands that took Sui Address can now take an alias
- Wallet `new-address` command now takes optional alias name argument [-a,--alias]
- **Breaking**:
    - SuiConfig.create_new_keypair_and_address now requires keyword arguments
    - Wallet `gas` command added alias option [-a,--alias] and renamed the address option to [-o,--owner]
    - Wallet `objects` command added alias option [-a,--alias] and renamed the address option to [-o,--owner]
    - Wallet `faucet` command added alias option [-a,--alias] and renamed the address option to [-o,--owner]
    - Wallet `transfer-object`
        - Added alias option [-a,--alias] and renamed the signer [-s,--signer] option to [-o,--owner]
        - See `wallet transfer-object -h` for additional command changes
    - Wallet `transfer-sui`
        - Added alias option [-a,--alias] and renamed the signer [-s,--signer] option to [-o,--owner]
        - See `wallet transfer-sui -h` for additional command changes
    - Wallet `pay`
        - Added alias option [-a,--alias] and renamed the signer [-s,--signer] option to [-o,--owner]
        - See `wallet pay -h` for additional command changes
    - Wallet `paysui`
        - Added alias option [-a,--alias] and renamed the signer [-s,--signer] option to [-o,--owner]
        - See `wallet paysui -h` for additional command changes
    - Wallet `payallsui`
        - Added alias option [-a,--alias] and renamed the signer [-s,--signer] option to [-o,--owner]
        - See `wallet payallsui -h` for additional command changes
    - Wallet `split-coin`
        - Added alias option [-a,--alias] and renamed the signer [-s,--signer] option to [-o,--owner]
        - See `wallet split-coin -h` for additional command changes
    - Wallet `merge-coin`
        - Added alias option [-a,--alias] and renamed the signer [-s,--signer] option to [-o,--owner]
        - See `wallet merge-coin -h` for additional command changes
    - Wallet `split-coin-equally`
        - Added alias option [-a,--alias] and renamed the signer [-s,--signer] option to [-o,--owner]
        - See `wallet split-coin-equally -h` for additional command changes
    - Wallet `publish`
        - Added alias option [-a,--alias] and renamed the signer [-s,--signer] option to [-o,--owner]
        - See `wallet publish -h` for additional command changes
    - Wallet `call`
        - Added alias option [-a,--alias] and renamed the signer [-s,--signer] option to [-o,--owner]
        - See `wallet call -h` for additional command changes

### Removed

## [0.41.1] - Unpublished

### Added

### Fixed

- [bug](https://github.com/FrankC01/pysui/issues/180) Publish was breaking due to change in `sui move build` output generation.

### Changed

### Removed

## [0.41.0] - 2023-12-13

### Added

- [enhancement](https://github.com/FrankC01/pysui/issues/176) Support for address/kp aliases

### Fixed

### Changed

- [enhancement](https://github.com/FrankC01/pysui/issues/176):
  * Added 'aliases' topic in documentation with more details and examples
- Added optional 'make_active' flag to:
  * SuiConfig.create_new_keypair_and_address
  * SuiConfig.recover_keypair_and_address


### Removed

## [0.40.1] - Unpublished

### Added

- ConsensusCommitPrologueV2 type transaction added to TxResult.

### Fixed

### Changed

- Bumped libraries: dataclasses-json, httpx, websockets
- Bumped dev libraries: mypy, pytest, pylint, sphinx_rtd_theme
- [change](https://github.com/FrankC01/pysui/issues/175) Default 'compress_inputs' on SuiTransaction to True
- Deprecating 'round' from RandomnessStateUpdate transaction type as of Sui 1.16.0

### Removed

## [0.40.0] - 2023-11-27

### Added

### Fixed

### Changed

- [change](https://github.com/FrankC01/pysui/issues/173) Removed constraint on SuiTransaction.make_move_vector that failed if arguments were pure.
- TransactionData added 3 new transaction kinds: AuthenticatorStateUpdate, RandomnessStateUpdate and EndOfEpochTransaction.

### Removed

## [0.39.1] - Unpublished

### Added

### Fixed

### Changed

- Low end Sui support version set to 1.10.0
- Restructure README

### Removed

## [0.39.0] - 2023-11-06

### Added

- [enhancement](https://github.com/FrankC01/pysui/issues/170) The added compress_inputs option, if set, compresses same input types with same values.

### Fixed

### Changed

- [BREAKING change](https://github.com/FrankC01/pysui/issues/171) SuiTransaction (sync and async) now require key value arguments in constructors.

- [BREAKING change](https://github.com/FrankC01/pysui/issues/172) Added type "Receiving" to object_registry for ser/de support.

### Removed

## [0.38.0] - 2023-10-25

### Added

### Fixed

### Changed

- Bumped supported pysui-fastcrypto from 0.2.0 to 0.3.0

### Removed


## [0.37.2] - Unpublished

### Added

### Fixed

### Changed

- Move to VSC bundled formatter `ms-python.black-formatter`
- Url for testnet faucet
- Bumped supported Sui RPC to 1.13.0

### Removed


## [0.37.1] - 2023-10-09

### Added

### Fixed

- [bug](https://github.com/FrankC01/pysui/issues/167) Fix for checking for Receiving. Manifested in `make_move_vector`

### Changed

- Updated doc theme dependency

### Removed

## [0.37.0] - 2023-10-02

### Added

- [enhancement](https://github.com/FrankC01/pysui/issues/165) Receiving object call argument
- [enhancement](https://github.com/FrankC01/pysui/issues/166) Start using protocol config for feature constraints. First application is for Receiving

### Fixed

### Changed

### Removed

## [0.36.1] - Unpublished

### Added

### Fixed

### Changed

- Bumped httpx and h2 lib versions

### Removed


## [0.36.0] - 2023-09-16

### Added

- Sui RPC 1.11.0 support

### Fixed

### Changed

### Removed

- Sui RPC  1.6.0 support
- `legacy_digest` option from `sui_utils.publish_build`

## [0.35.1] - Unpublished

### Added

- Sui RPC 1.11.0 support

### Fixed

- [bug](https://github.com/FrankC01/pysui/issues/163) uleb128 encoding of
pure vectors (i.e. vector<u8>, etc.)

### Changed

- Bumped dataclasses-json to 0.6.0
- `gas_budget` now optional on `SuiTransaction.get_transaction_data`

### Removed

- Sui RPC  1.6.0 support
- `legacy_digest` option from `sui_utils.publish_build`

## [0.35.0] - 2023-08-28

### Added

- [enhcancement](https://github.com/FrankC01/pysui/issues/161) SuiTransaction supports offline signing.
`SuiTransaction.deferred_execution` takes same arguments as `SuiTransaction.execute` but returns a
base64 string that can be signed and then used in the `ExecuteTransaction` builder.
- `BaseMultiSig`, base class for `MultiSig`, that supports constructing with just publickeys. When
signatures are gathered then use `BaseMultiSig.signature_from` for generating the MultiSig signature. Attemptinig
to `SuiTransaction.execute` when using BaseMultiSig will fail
- `SuiConfig.keypair_for_publickey` method

### Fixed

- [bug](https://github.com/FrankC01/pysui/issues/162) Constraint on vector limits constant
was replaced but validation routine not updated

### Changed

### Removed

## [0.34.1] - Unpublished

### Added

### Fixed

- [bug](https://github.com/FrankC01/pysui/issues/160) MultiSig constraints changed to address.

### Changed

### Removed

## [0.34.0] - 2023-08-28

### Added

- KeyPair: signing (`sign_message`) arbitrary base64 strings and verifying (`verify_signature`) signatures.

### Fixed

- [bug](https://github.com/FrankC01/pysui/issues/158) Failure evaluating Command in `verify_transaction(...)`
- Fails gracefully if calling `get_gas_from_faucet` on SuiClient's with non-supported config.

### Changed

- [change](https://github.com/FrankC01/pysui/issues/154) Changes in align with new suibase proxy configuration
- [change](https://github.com/FrankC01/pysui/issues/155) Bump pysui-fastcrypto version requirement [see](https://github.com/FrankC01/pysui-fastcrypto/issues/1)
- [deprecating](https://github.com/FrankC01/pysui/issues/153) sui_utils `publish_build` option. Will remove in 0.36.0
- bumped pysui-fastcrypto depedency to >= 0.2.0

### Removed

- pkg_resources dependency in sui_clients.common.py

## [0.33.1] - Unpublished

### Added

### Fixed

### Changed

- Bumped pysui version
- Bumped RPC API versions

### Removed


## [0.33.0] - 2023-08-11

**BREAKING CHANGE**

With this release, the `bip-utils` library has been removed in favor of `pysui-fastcrypto`. This is a
Python wrapper around the MystenLabs `fastcrypto` Rust crate.

Because of this change, installing pysui now requires Rust and Cargo to be installed,
see [Rust Install](https://www.rust-lang.org/tools/install). This will allow the Rust crate and wrapper to be
built specific to your platform.

### Added

- [enhancement](https://github.com/FrankC01/pysui/issues/116) SuiTransaction serialize/deseralize
- [enhancement](https://github.com/FrankC01/pysui/issues/143) Ability to add a new key to the
  SuiConfig. The argument can either be a Sui keystring _or_ a dict for importing keys exported from Wallet. The
  dict must take the form of:
  ```python
    {
      'wallet_key':'0x.....',             # Wallet exported key hex string (66 chars with 0x prefix)
      'key_scheme': SignatureScheme.XYZ   # Where XYZ is one of {ED25519, SECP256k1, SECP256r1}
    }
- The concert with the above enhancement, if initiating `pysui` with `SuiConfig.user_config(...)` the `prv_keys`
  parameter can be a list of Sui keystrings, the dict as described above, or both.

### Fixed

- [bug](https://github.com/FrankC01/pysui/issues/148) Attempt to write to non-existant keystore

### Changed

- [change]((https://github.com/FrankC01/pysui/issues/144) `pysui` now requires pysui-fastcrypto
- [change]((https://github.com/FrankC01/pysui/issues/145) Per change above, removed all
  but generic SuiKeyPair, SuiPublicKey and SuiPrivateKey classes
- [change](https://github.com/FrankC01/pysui/issues/147) Allowing transaction command Result in split_coin amounts list
- `create_new_keypair_and_address` on SuiConfig now takes word_counts (int) instead of mnemonic phrase
- Simplified MultiSig BCS construct
- Documentation

### Removed

- `pyroaring` and `bip-utils` libraries. **_You should rebuild your virtual environment using new requirements.txt_**
- bcs MultiSigLegacy that used `pyroaring` bitmap construct

## [0.32.0] - 2023-08-03

**BREAKING CHANGE**

### Added

- OP_STRATEGIES.md explaining deprecation, release and publishing strategies

### Fixed

- [**BREAKING bug**](https://github.com/FrankC01/pysui/issues/146) See 'Changed' below this line...

### Changed

- The SuiTransaction execute method's `gas_budget` argument now strictly sets the gas budget for the transaction. Prior, an inspection
would be run and pysui used the greater of the two. Now, `gas_budget`'s default is an emptry string ("") and by leaving it that
way a dryRun will be run prior to execution to set the budget.

### Removed

## [0.31.2] - Unpublished

### Added

- OP_STRATEGIES.md explaining deprecation, release and publishing strategies

### Fixed

- Typos

### Changed

- RPC API version range check in `pysui/sui/sui_clients/sui_common.py` covering 1.5.x to 1.7.x
- Documentation

### Removed

## [0.31.1] - Unpublished

### Added

### Fixed

### Changed

- **Deprecating** in `sui_crypto` all specific keytype classes  (i.e. suffixed ED25519, SECP256K1 and SECP256R1) .

### Removed

## [0.31.0] - 2023-07-27

### Added

- SuiTransaction verifies against ProtocolConfig transaction constraints. `txn.verify_transaction()` can be run prior to transaction execution
- SuiTransaction run_verification flag to `txn.execute(...)`.
- TransactionKindInQuery QueryTransaction filter, supported in indexer nodes
- FromOrToAddressQuery QueryTransaction filter, supported in indexer nodes

### Fixed

### Changed

- **Deprecating** legacy MultiSig support in favor of Sui 1.4.0 MultiSig changes, will be removed in pysui 0.33.0.
- TxResponse `checkpoint` field to Optional[str] type, was previously Optional[int]
- [change](https://github.com/FrankC01/pysui/issues/127) - Protocol constraints
- [change](https://github.com/FrankC01/pysui/issues/142) - Dependencies update in **_requirements.txt_**

### Removed

- Documentation (removed legacy add/change/deprecated footnotes)

## [0.30.2] - 2023-07-18

### Added

### Fixed

- [bug](https://github.com/FrankC01/pysui/issues/141) Reuse of identical 'pure' values breaks on move contract

### Changed

### Removed

## [0.30.1] - 2023-07-17

### Added

### Fixed

- [bug](https://github.com/FrankC01/pysui/issues/140) Invalid assertion in merge_coins removed

### Changed

### Removed

## [0.30.0] - 2023-07-17

**MAJOR BREAKING CHANGES**

### Added

- `non_refundable_storage_fee` to GasCostSummary as part of TxResult effects
- CODE_OF_CONDUCT.md
- Extend debug logging in low level transaction builder

### Fixed

- [bug](https://github.com/FrankC01/pysui/issues/137)

### Changed

- **BREAKING** [change](https://github.com/FrankC01/pysui/issues/132) Transaction package (sui_txn)
- [change](https://github.com/FrankC01/pysui/issues/134) samples updated to accomodate breaking #132
- [change](https://github.com/FrankC01/pysui/issues/139) changes to gas payment strategy
- Generalized raising Value error(s) during transaction execution **_prep_** whereas previously it would exit the application
- Document typo tweaks

### Removed

- **BREAKING** [change](https://github.com/FrankC01/pysui/issues/133) Builders removed use SuiTransaction:
  - BatchTransaction
  - Publish
  - MoveCall
  - RequestAddStake
  - RequestWithdrawStake
  - SplitCoinEqually
  - SplitCoin
  - MergeCoin
  - PaySui
  - Pay
  - TransferSui
  - TransferObject

- **BREAKING** [change](https://github.com/FrankC01/pysui/issues/133) Client methods removed (both sync and async SuiClient)
use SuiTransaction:
  - publish_package_txn
  - move_call_txn
  - split_coin_equally_txn
  - split_coin_txn
  - merge_coin_txn
  - transfer_object_txn
  - transfer_sui_txn
  - pay_allsui_txn
  - pay_sui_txn
  - pay_txn



## [0.29.1] - Unpublished

### Added

### Fixed

- [bug](https://github.com/FrankC01/pysui/issues/135) - SuiClient `get_events`

### Changed

- [change](https://github.com/FrankC01/pysui/issues/131) - improve SuiTransaction constructor performance

### Removed

## [0.29.0] - 2023-07-07

### Added

- `continue_on_close` argument to subscription `new_event_subscription()` and `new_transaction_subscription()`
- `client.get_gas()`, `client.get_coin()` and `client.get_objects()` now include a `fetch_all` option.
- `client.get_objects_for()` now handles large lists
- Common convenient imports in pysui.__init__.py

### Fixed

- `samples/async_gas.py` now returns **_all_** gas objects
- `samples/wallet.py` "gas" command now returns **_all_** gas objects
- SuiConfig now respects non-standard aliases in `client.yaml`
- Cleaned up modules still logging to root

### Changed

- Refactored subscription connection handling

### Removed

## [0.28.0] - 2023-07-05

### Added

- Preliminary logging docs
- [enhancement](https://github.com/FrankC01/pysui/issues/68)
- [enhancement](https://github.com/FrankC01/pysui/issues/120)
- [enhancement](https://github.com/FrankC01/pysui/issues/124)

### Fixed

- [bug](https://github.com/FrankC01/pysui/issues/125)
- [bug](https://github.com/FrankC01/pysui/issues/126)
- Contributed by Debjit Bhowal, thank you! [bug](https://github.com/FrankC01/pysui/issues/129)

### Changed

- synch and asynch SuiClient methods marked for deprecation, use
  equivalent SuiTransaction/SuiTransactionAsync methods instead.
  Will be removed from code in `pysui` v0.30.0:
  - publish_package_txn
  - move_call_txn
  - split_coin_equally_txn
  - split_coin_txn
  - merge_coin_txn
  - transfer_object_txn
  - transfer_sui_txn
  - pay_allsui_txn
  - pay_sui_txn
  - pay_txn

### Removed

## [0.27.1] - 2023-06-28

### Added

### Fixed

### Changed

- Fell back to minimum RPC version support from 1.4.0 to 1.3.0

### Removed

## [0.27.0] - 2023-06-27

### Added

- Added additional Exception handler in subscription._subscription_drive

### Fixed

### Changed

- Renabled 'ping' on subscription
- Any exception in subscription._subscription_drive now returns any accumulated handler data returns

### Removed

## [0.26.1] - Unpublished

### Added

- SSL context on sync and async SuiClients
- subscriptions now support both sync/async handlers
- async_sub.py -> Include a dump of data collected during handling subscription events

### Fixed

- Bug in secp256k1 signing, indirectly also impacted MultiSig

### Changed

- Support for new MultiSig format (1.4.x+) and maintaining backlevel support (1.3.x) [change](https://github.com/FrankC01/pysui/issues/118)
- Atomic Builders marked for deprecation, use
  equivalent SuiTransaction/SuiTransactionAsync methods instead.
  Will be removed from code in `pysui` v0.30.0:
  - BatchTransaction
  - Publish
  - MoveCall
  - RequestAddStake
  - RequestWithdrawStake
  - SplitCoinEqually
  - SplitCoin
  - MergeCoin
  - PaySui
  - Pay
  - TransferSui
  - TransferObject

### Removed


## [0.26.0] - 2023-06-20

### Added

- SuiTransactionAsync [enhancement](https://github.com/FrankC01/pysui/issues/114)

### Fixed

- Subscription switch from list to dict [bug](https://github.com/FrankC01/pysui/issues/119)

### Changed

- README.md
- Relaxed user configuration initialization, initial private keystring no longer required

### Removed

## [0.25.0] - 2023-06-12

### Added

- New 'binary-free' SuiConfig load option `SuiConfig.user_config`. See documentation

### Fixed

### Changed

- Publish utiilty now throws a ValueError if attempting while using `SuiConfig.user_config`
- SuiTransaction `execute` argument `gas_budget` is now optional, defaults to 1M Mists
- Extended SuiTransaction `execute` to include options to provide to `sui_executeTransactionBlock`

### Removed

## [0.24.1] - Unpublished

### Added

- GetStakesById builder supporting Sui RPC API `suix_getStakesByIds`
- MultiSig and Sponsor SuiTransaction test
- Publish SuiTransaction test

### Fixed

- README.md

### Changed

- Improved SuiTransaction `execute` performance
- Bump Deprecated library version

### Removed

## [0.24.0] - 2023-06-01

### Added

- SuiConfig method to recover key from mnemonics and derivation path [enhancement](https://github.com/FrankC01/pysui/issues/112)

### Fixed

- Object mutabilty in SuiTransaction [bug](https://github.com/FrankC01/pysui/issues/111)

### Changed

- RPC parameter changed to map from array [change](https://github.com/FrankC01/pysui/issues/80)
- Refresh docs for Builder references

### Removed

## [0.23.1] - Unpublished

### Added

- Object options test individual flags

### Fixed

- Object fetch options [bug](https://github.com/FrankC01/pysui/issues/110)

### Changed

### Removed

## [0.23.0] - 2023-05-23

### Added

- GetChainID builder supporting Sui RPC API `sui_getChainIdentifier` in 1.2.0

### Fixed

### Changed

### Removed

## [0.22.2] - Unpublished

### Added

### Fixed

### Changed

- Upgraded library dependencies websockets, httpx
- Upgraded dev library dependencies pylint, pydocstyle, pytest, black, build, twine, sphinx_rtd_theme

### Removed

## [0.22.1] - 2023-05-20

### Added

- SigningMultiSig example documentation in Programmable Transaction section

### Fixed

- PyPi packaging repository link

### Changed

- Removed dependency on `secp256k1` library and converted key handling to use `bip-utils`
- Publish documentation emphasizing that UpgradeCap must be transferred as part of SuiTransaction
- Minor documentation changes

### Removed

## [0.22.0] - 2023-05-16

### Added

- Added MoveEventModuleQuery filter for queryEvents

### Fixed

### Changed

- Renamed from MoveEventField to MoveEventFieldQuery for queryEvents

### Removed

## [0.21.2] - 2023-05-14

### Added

- `split_coin_and_return` on SuiTransaction. Like split_coin_equally but splits and doesn't transfer back to self, instead
  returns list where each element and list can be sent/transferred/used in subsequent transactions.
- `public_transfer_object` on SuiTransaction, exposes 0x2::transfer::public_transfer

### Fixed

- MultiSig signing regression in SuiTransaction

### Changed

- Refactored sui_crypto.create_new_keypair

### Removed

## [0.21.1] - 2023-05-10

### Added

- Pure python multisig signing, reducing dependencies on Sui binaries [enhancement](https://github.com/FrankC01/pysui/issues/100)
- `pyroaring` added to requirements.txt and package build

### Fixed

- Use of multisigs in SuiTransaction [bug](https://github.com/FrankC01/pysui/issues/109)

### Changed

- SuiTransaction now takes an optional `item_type` argument that is a string triple of the
  type of objects you are making a vector of

### Removed

## [0.21.0] - 2023-05-09

### Added

- GetProtocolConfig builder and response supporting Sui RPC API `sui_getProtocolConfig` in 1.1.0

### Fixed

### Changed

### Removed

## [0.20.3] - Unpublished

### Added

- SuiTransaction now has convenient `gas` property: `tx.split_coin(coin=tx.gas,amounts=[1000000000])` [enhancment](https://github.com/FrankC01/pysui/issues/106)

### Fixed

### Changed

### Removed

## [0.20.2] - 2023-05-05

### Added

### Fixed

- SharedObject mutablity resolution in SuiTransaction [bug](https://github.com/FrankC01/pysui/issues/107)

### Changed

### Removed

## [0.20.1] - 2023-05-03

### Added

### Fixed

- mainnet in SuiConfig regression [bug](https://github.com/FrankC01/pysui/issues/103)

### Changed

### Removed

## [0.20.0] - 2023-05-03

Breaking Changes

### Added

- GetValidatorsApy builder and response supporting Sui RPC API `suix_getValidatorsApy` in 1.0.0
- SubscribeTransaction builder supporting Sui RPC API `suix_subscribeTransaction` in 1.0.0
- `asynch_sub_txn` demo for SubscribeTransaction
- `custom_upgrade` method to SuiTransaction

### Fixed

- Fixed argument error in low level builder for transfer using split which expected a list of amounts.
- Duplicate inputs generated from SuiTransaction building [bug](https://github.com/FrankC01/pysui/issues/99)

### Changed

- Bump version to 0.20.0
- **Breaking Change** SuiTransaction `publish` command now returns an UpgradeCap result. Up to author to transfer
- `publish_build` utility that builds a move project for publishing now uses updated digest creation unless flag to use legacy set
- Updated documentation

### Removed

- **Breaking Change** `locked_in_epoch` field remmoved in SuiCoinObject result.
- Deprecated methods marked in 0.16.1

## [0.19.0] - Repo Only

### Added

- [enhancement](https://github.com/FrankC01/pysui/issues/92) SuiTransaction builder supports Optional in move_call arguments for Sui unsigned integer types
- `libtool` in README dependencies list

### Fixed

- Mutable flag on ObjectRead of ownertype Shared [bug](https://github.com/FrankC01/pysui/issues/97)
- Pure string encoding [bug](https://github.com/FrankC01/pysui/issues/91)
- Exclude simple types from SuiTransaction `make_move_vec` [bug](https://github.com/FrankC01/pysui/issues/93)
- Simple empty list as `arguments` was failing [bug](https://github.com/FrankC01/pysui/issues/94)
- bcs.Address conversion of strings of varying lengths [bug](https://github.com/FrankC01/pysui/issues/95)

### Changed

- `sui-base` to `suibase` in documentation

### Removed

## [0.18.0] - 2023-04-25

Breaking Changes

### Added

- Handling move call argument nested lists/vectors
- More documentation on SuiTransaction (programmable transactions)
- GetLoadedChildObjects builder and reponse supporting Sui RPC API `sui_getLoadedChildObjects` in 0.33.0

### Fixed

- On testnet code has changes in `rpc.discover` making required field optional on method parameters.
- Nested types [bug](https://github.com/FrankC01/pysui/issues/90)

### Changed

### Removed

- **Breaking Change** `additional_signature`, other than sender and sponsor, are not supported by the tx processor in Sui. Removed
  the property in `SignerBlock`

## [0.17.0] - 2023-04-22

Breaking Changes

### Added

- **Breaking Change** Assertion on SuiTransaction that will fail operations on it if it's been executed already
- Implemented NameServiceAddress and NameServiceNames builders and results for supporing `suix_resolveNameServiceAddress` and `suix_resolveNameServiceNames` respectivly.
- `merge_gas_budget` to SuiTransaction constructor. When attempting to find available gas coin for transaction, this flag if true,
  allows a merge of coins to meet budget demand. Defaults to False

### Fixed

- Field declaration in Effects result.
- Bug in SuiTransaction builder argument resolution method.

### Changed

- Extended CompiledPackage to hold blake2b digest to match chain digest calculation. Used in package upgrades in SuiTransaction.
- Introspection on SuiTransaction `move_call` target function to better return reusuable command results
- **Breaking Change** SuiTransaction constructor and execute methods simplified while making signing more powerful
- **Breaking Change** SuiTransaction `split_coin` now takes list of amounts and returns list of results.
- **Breaking Change** SuiTransaction `move_call` now takes target string in form: `"package_id::module_name::function_name"`
- **Breaking Change** `build_for_execute` method made private on SuiTransaction

### Removed

- **Breaking Change** `gasses` property from SuiTransaction

## [0.16.1] 2023-04-16

We've started to 'deprecate' various functions, classes and methods to provide early warnings where
your usage of `pysui` should consider changing.

### Added

- `split_coin_equal` to SuiTransaction (a.k.a. Transaction Builder)
- Support for signing with MultiSig in SuiTransaction
- Support for running locally using [sui-base](https://github.com/sui-base/sui-base). The advantages are
  the availabbility of highly configurable local nodes, management of different versions of Sui and consistent
  wallet addresses across configuration.
- New pytests leveraging `sui-base`

### Fixed

### Changed

- Changed methods for loading a configuration. Choices are now:
  1. `SuiClient.default_config()` (default configuration loading)
  2. `SuiClient.sui_base_config()` (if running sui-base locally)

### Removed

## [0.16.0] 2023-04-13

### Added

- Added missing options for querying transactions
- Implemented QueryTransactions [enhancement](https://github.com/FrankC01/pysui/issues/84) builder and results supporing `suix_queryTransactions`
- MultiSig added [enhancement](https://github.com/FrankC01/pysui/issues/75)
- Implemented pysui.sui.sui_clients.Transaction/Transaction builder supporting Programmable Transactions [enhancement](https://github.com/FrankC01/pysui/issues/83)
- Documentation for Programmable Transaction in read-the-docs

### Fixed

- GetTotalTxCount underlying RPC API method [fixed](https://github.com/FrankC01/pysui/issues/82)
- GetMultipleTx was calling obsolete RPC API method.
- Result type from calling faucet
- Added default dependency IDs for 0x1 and 0x2 in sui_utils.py for publishing

### Changed

- _**Most, if not all, integer values as arguments to RPC methods have been changes in Sui 0.31.0 to strings
  to support bigger integers for platforms without arbitrarily large numbers (ALN). This has resulted in
  changes to many `pysui` Builder and result types.**_
- Gas requirements for transactions have increased 1000x on devnet. Use `GetReferenceGasPrice` and `DryRunTransaction` often until you get used to the [changes](https://docs.sui.io/devnet/build/sui-gas-charges).
- Increased default RPC timeout from 30 to 120 seconds on synch and asynch SuiClients.

### Removed

- GetTxs aligning to dropped methods in RPC API 0.29.1
- GetTransactionsInRange aligning to dropped methods in RPC API 0.29.1

## [0.15.0] 2023-03-30

### Added

- Added `get_objects` to synchronous and asynchronous SuiClients
- Address SignatureType in constant pool (base_deserailizers.py - deserialize_constants)
- GetCheckpoint builder and Checkpoint result for `sui_getCheckpoint` as per Sui 0.28.0
- GetCheckpoints builder and Checkpoint paginated results for `sui_getCheckpoints` as per Sui 0.28.1
- GetLatestSuiSystemState builder and results for `sui_getLatestSuiSystemState` as per Sui 0.28.0
- GetMultipleTx builder and TxResponseArray result for `sui_multiGetTransactions` as per Sui 0.28.0
- GetMultipleObjects builder for `sui_multiGetObjects` as per Sui 0.28.0
- QueryEvents builder for `sui_queryEvents` as per Sui 0.28.0

### Fixed

- [bug](https://github.com/FrankC01/pysui/issues/76)
- [bug](https://github.com/FrankC01/pysui/issues/78)
- [bug](https://github.com/FrankC01/pysui/issues/67)

### Changed

- **Breaking Change** Addresses are now 32 bytes (as apposed to 20) and are generated from keys using `blake2b` instead of `sha3_256`
- **Breaking Change** Prior 'module build' functions in `sui_utils.py` to support publishing have been replaced with `publish_build`. At the moment this will only prepare the core package modules. We will follow up with publishing unpublished dependencies in a later release. If you need that capabilit, use `sui client publish ...` from command line.
- **Breaking Change** event filters for QueryEvents and SubscribeEvents moved to `sui_types/event_filter.py`. Note that per Sui 0.28.0 the filters have changed.
- **Breaking Change** TxEffectResult renamed to TxResponse and restructured as per Sui 0.28.0
- **Breaking Change** Sui has moved from 20 byte address to 32 byte addresses. This changes all SuiAddress and ObjectID constructs.
- **Breaking Change** ValidatorMetaData changes as per Sui 0.28.0
- **Breaking Change** DelegatedStake changes as per Sui 0.28.0
- **Breaking Change** Added DryRunTxResult for new result definition as per Sui 0.28.0
- **Breaking Change** GetDynamicFieldObject now takes a mapping for name as per Sui 0.28.0
- **Breaking Change** GetTx result changes as per Sui 0.28.0
- **Breaking Change** GetObject options and result changes as per Sui 0.28.0
- **Breaking Change** ExecuteTransaction now takes a list of signatures as per Sui 0.28.0
- **Breaking Change** Result types (TxResult, TxInspectionResult and DryRunTxResult) changes as per Sui 0.28.0
- **Breaking Change** Pay and PaySui now takes a list of SuiStrings for amounts as per Sui 0.28.0
- **Breaking Change** GetEvents now take a transaction digest as parameter as per Sui 0.28.0. See Added above for QueryEvent for old behavior.
- Subscribing to events now only gets events emitted by a module as per Sui 0.28.0
- Renamed GetDelegatedStakes builder to GetStakes aligning with `sui_getStakes` as per Sui 0.28.1
- Renamed RequestAddDelegation builder to RequestAddStake aligning with `sui_requestAddStake` as per Sui 0.28.0
- Renamed RequestWithdrawDelegation builder to RequestWithdrawStake, aligning with `sui_requestWithdrawStake` as per Sui 0.28.0
- All transaction RPC API calls (Batch,Publish,MoveCall,PayXX,SplitXX,MergeXX,StakeXX) now invoke `unsafe_<NAME>` as per Sui 0.28.0 in light of the new ProgrammableTransaction.
- async_client and sync_client now take optional `additional_signers` towards support Sui multi-sign
- async_client and sync_client "execute_no_sign" now returns a PreExecutionResult data object in SuiRpcResult
- GetObject now takes flag options on what to include or not in result
- Removed `protocol_version` field from CommitteeInfo results as per Sui 0.28.0
- InspectTransaction results now include eveents as per Sui 0.28.0
- Renamed `bcs_from_rpcresult` to `bcs_struct_from_rpcresult` in

### Removed

- **Breaking Change** GetTxAuthSignatures removed for `sui_getTransactionAuthSigners` removed as per Sui 0.28.0
- **Breaking Change** RequestSwitchDelegation removed for `sui_requestSwitchDelegation` removed as per Sui 0.28.0
- **Breaking Change** GetRawObject removed for `sui_getRawObject` removed as per Sui 0.28.0. Raw information is now part of GetObject
- **Breaking Change** GetSuiSystemState removed for `sui_getSuiSystemState` as per Sui 0.28.0. Use GetLatestSuiSystemState instead.
- **Breaking Change** ExecuteSerializedTransaction removed for `sui_executeTransactionSerializedSig` as per Sui 0.28.0
- **Breaking Change** GetCheckpointContentsByDigest, GetCheckpointSummary,GetCheckpointSummaryByDigest as per Sui 0.28.0
- **Breaking Change** Removed `get_address_object_descriptors` from synchronous and asynchronous SuiClients

## [0.14.1] 2023-02-24

### Added

### Fixed

### Changed

- Docs:
  - Updated subscription primer
  - Updated builders x-ref listing

### Removed

## [0.14.0] 2023-02-23

BREAKING Changes

### Added

### Fixed

### Changed

- samples/async_sub.py updated to remove transaction subscriptions (see 'Removed' below)
- `name`, `description` and `image_url` changed from int list to strings in ValidatorMetadata as per Sui 0.27.0 updates
- Added `unwrappedThenDeleted` to Effects as per Sui 0.27.0 updates
- Added `gas_data` to transaction execution results as per Sui 0.27.0 updates
- Added `checkpoint` field to results of GetTx (sui_getTransaction), None otherwise, as per Sui 0.27.0 updates
- Added `executedEpoch` to Effects as per Sui 0.27.0 updates
- CheckpointContents `user_signatures` change to support multi-sig as per Sui 0.27.0 updates
- Remove redundant code for `sui_config.create_new_keypair_and_address `
- Refactor `sui_bcs.py`
- Rename `sui_bcs.tkind_from_result` to `sui_bcw.bcs_txkind_from_result`

### Removed

- **BREAKING:** `sui_subscribeTransaction` removed from Sui RPC API as per Sui 0.27.0 updates as a result:
  - new_txn_subscription removed from `sui_client.subscribe`
  - SubscribeTransaction removed from sui_builders and respective results from sui_txresults

## [0.13.0] 2023-02-16

BREAKING Changes

### Added

- **Experimental** `sui_bcs.py` - work in progress to enable `sui_devInspectTransaction`

  - Sui 0.25.0 only supports inspection on:

    - sui_transferObject
    - sui_transferSui
    - sui_pay
    - sui_moveCall
    - sui_batchTransaction

  - There are a few ways to get the BCS serialized TransactionKind argument for InspectTransaction builder

    - `sui_bcs.bcs_txkind_from_result` - Takes result from a `client.execute_no_sign`. However; because calling
      SUI RPC requires providing a `gas` object and `gas_budget` value that may not be feasible for your use case.

      ```python
      try:
          batch_params = SuiArray(
              [
                  TransferObjectParams(
                      receiver=SuiAddress("0x7c7a86b564d5db0c5837191bd17980b2fb9934db"),
                      transfer_object=ObjectID("0x1A0535C87DE089F4417CA874A646A04914C073D6"),
                  ),
                  MoveCallRequestParams(
                      package_object=ObjectID("0x2"),
                      module_str=SuiString("pay"),
                      function_str=SuiString("join"),
                      type_arguments=SuiArray([SuiString("0x2::sui::SUI")]),
                      arguments=SuiArray(
                          [
                              SuiString("0x0b5b6f3f2e407d1a3f6c82d716ede72b394b7ca9"),
                              SuiString("0x30082e169ba9f2c92b1be1763870ea9a9a7b6180"),
                          ]
                      ),
                  ),
              ]
          )
          builder = BatchTransaction(
              cfg.active_address,
              batch_params,
              ObjectID("0x0b5b6f3f2e407d1a3f6c82d716ede72b394b7ca9"),
              SuiInteger(2000),
          )

          # Call execution but do not sign and submit
          rpc_result = client.execute_no_sign(builder)

          iresult = sync_client.execute(
              InspectTransaction(
                  sender_address=cfg.active_address,
                  tx_bytes=bcs_txkind_from_result(rpc_result),
              )
          )
          if iresult.is_ok():
            print(iresult.result_data.to_json(indent=2))
          else:
            print(iresult.result_string)
      # And so on...
      except ..:

      ```

    - `sui_bcs.bcs_base64_from_builder` - Takes a Builder and returns BCS encoded base64 string. Here the
      `gas` object and `gas_budget` use a stock substitue value (FAKE_ADDRESS_OR_OBJECT) that are ignored.

      ```python
      transfer_params = SuiArray(
          [
              MoveCallRequestParams(
                  package_object=ObjectID("0x2"),
                  module_str=SuiString("pay"),
                  function_str=SuiString("join"),
                  type_arguments=SuiArray([SuiString("0x2::sui::SUI")]),
                  arguments=SuiArray(
                      [
                          SuiString("0x0b5b6f3f2e407d1a3f6c82d716ede72b394b7ca9"),
                          SuiString("0x30082e169ba9f2c92b1be1763870ea9a9a7b6180"),
                      ]
                  ),
              ),
              TransferObjectParams(
                  receiver=SuiAddress("0x7c7a86b564d5db0c5837191bd17980b2fb9934db"),
                  transfer_object=ObjectID("0xd999644f6da53cc516ca6c6da76d463053fc3dc4"),
              ),
          ]
      )
      bt_builder = BatchTransaction(
          SuiAddress(FAKE_ADDRESS_OR_OBJECT), transfer_params, ObjectID(FAKE_ADDRESS_OR_OBJECT), SuiInteger(1)
      )
      bcs_bt = bcs_from_builder(sync_client, bt_builder)

      iresult = sync_client.execute(
          InspectTransaction(
            sender_address=sync_client.config.active_address,
            tx_bytes=base64.b64encode(bcs_bt.serialize()).decode())
      )
      if iresult.is_ok():
          print(iresult.result_data.to_json(indent=2))
      else:
          print(iresult.result_string)
      ```

    - We are working on the 3rd option (low level) where you can directly code the BCS constructs and
      serialize directly into the InspectTransaction `tx_bytes` field.

### Fixed

- ~~secp256r1 signing~~ [workaround](https://github.com/FrankC01/pysui/issues/67)
- InspectTransaction alignment to TransactionKind [bug](https://github.com/FrankC01/pysui/issues/69)

### Changed

- **BREAKING** Bumped minimal supported sui binaries from 0.19.0 to 0.25.0
- **BREAKING** TransferObjectParams (for Batch) builder now expects ObjectID as `transfer_object` parameter
- Updated CheckpointSummary as per updated result in SUI 0.26.0
- Updated CommitteeInfo as per updated result in SUI 0.26.0
- Updated SuiSystemState as per updated result in SUI 0.26.0
- Made `sui_token_lock` on `StakedSui` optional result

### Removed

- **BREAKING** GetObjectsOwnedByObject (i.e. sui_getObjectsOwnedByObject) has been removed in SUI 0.26.0

## [0.12.0] 2023-02-09

Breaking change.

### Added

- A new package, `sui_move` for deserialization of move compiled modules. This is primarily used in Publish supporting `--with-unpublished-dependencies`

### Fixed

### Changed

- Results from `sui_executeTransaction` and `sui_executeTransactionSerializedSig` changes aligning to SUI 0.25.0
- secp256k1 transaction signing changes as per [sui](https://github.com/MystenLabs/sui/pull/7423)
- Added optional mnemonic phrase and derivation path arguments to `create_new_keypair_and_address` SuiConfig methods.
- Move build distro to pyproject.toml from setup.cfg [build](https://github.com/FrankC01/pysui/issues/61)

### Removed

- setup.cfg

## [0.11.0] 2023-02-02

Breaking changes

### Added

- Reintroduce GetRawObject builder and results

### Fixed

### Changed

- Added new required field for DevInspectTransaction `sender_address` as per [SUI 0.24.0](https://github.com/MystenLabs/sui/releases/tag/devnet-0.24.0)
- `package` on MoveCall transaction result type is now just a object ID string as per [SUI 0.24.0](https://github.com/MystenLabs/sui/releases/tag/devnet-0.24.0)

### Removed

- DevInspectMoveCall as per [SUI 0.24.0](https://github.com/MystenLabs/sui/releases/tag/devnet-0.24.0)

## [0.10.0] 2023-01-25

Breaking changes

### Added

- `previous_transaction` field on SuiCoinObject result as per SUI 0.23.0
- `voting_power` field on Validator result (part of SuiSystemState) as per SUI 0.23.0
- More documentation
- Support for `secp256r1` [feature](https://github.com/FrankC01/pysui/issues/59)
  - Caveat: Key recovery not supported yet
  - Caveat: Due to the requirement of generating a recovery ID a brute force hack was added to signing with secp256r1 keys. However; this requirement for recovery ID is going to be lifted at some point in SUI [feature](https://github.com/MystenLabs/sui/issues/5654)

### Fixed

- [bug](https://github.com/FrankC01/pysui/issues/62)
- [bug](https://github.com/FrankC01/pysui/issues/63)
- [bug](https://github.com/FrankC01/pysui/issues/64)

### Changed

- `pending_delegations` field structure change from TableVec to LinkedTableForObjectID
- GetCheckpointContents now takes `sequence_number` (SuiInteger) vs `digest` (SuiString) as per SUI 0.23.0
- GetCheckpointContentsBySequence renamed to _GetCheckpointContentsByDigest_ with argument `digest` as per SUI 0.23.0
- Updated SuiSystemState result definition to include `safe_mode` field as per SUI 0.22.1
- Updated CheckpointSummary result definition to include `timestamp_ms` field as per SUI 0.22.1

### Removed

- `storage_gas_price` field from StateParameters result (part of SuiSystemState) as per SUI 0.23.0
- `quorum_stake_threshold` field from ValidatorSet result (part of SuiSystemState) as per SUI 0.23.0

## [0.9.0] 2023-01-20

Breaking changes

### Added

- `description`, `image_url` and `project_url` ValidatorMetadata in SystemState result as per SUI 0.22.0
- `epoch` optional arguments added to InspectTransaction and InspectMoveCall builders as per SUI 0.22.0
- GetCheckpointContents builder added as per SUI 0.22.0
- GetCheckpointContentsBySequence builder added as per SUI 0.22.0
- GetCheckpointSummary builder added as per SUI 0.22.0
- GetLatestCheckpointSequence builder added as per SUI 0.22.0
- ChangeEpocTx added to transaction execution result as per SUI 0.21.0
- GenesisTx added to transaction execution result as per SUI 0.21.0

### Fixed

- arguments from transaction 'Call' event supports empty list, list strings or int arrays

### Changed

- Code refactoring for most builders in `builders/exec_builders.py` (BatchTransaction is the exception)
- SuiConfig: documentation
- Wallet: SUI RPC API version printed with SDK version `wallet -v`
- pending_delegations and pending_withdraws in StakingPool changed to TableVec from list of obsolete structures.
- DelegatedStakes: Built out result type (from GetDelegatedStakes builder)

### Removed

- `sig_scheme` and `pubkey` from ExecuteTransaction builder as per SUI 0.22.0
- `switch_pool_token_amount` from RequestSwitchDelegation builder as per SUI 0.22.0
- `principal_withdraw_amount` from RequestWithdrawDelegation builder as per SUI 0.22.0
- `chain_id` from result of GetSystemState as per SUI 0.22.0

## [0.8.0] 2023-01-14

BREAKING CHANGES (Keys)

### Added

- Utility `keys_to_0210.py` [about](utility/README.md)
- GetDelegatedStakes builder and return types supporting **new** SUI RPC API (0.21.0)
- GetValidators builder and return types supporting **new** SUI RPC API (0.21.0)
- RequestAddDelegation builder supporting **new** SUI RPC API (0.21.0)
- RequestSwitchDelegation builder supporting **new** SUI RPC API (0.21.0)
- RequestWithdrawDelegation builder supporting **new** SUI RPC API (0.21.0)

### Fixed

- GetObjectsOwnedByObject result parsing [bug](https://github.com/FrankC01/pysui/issues/58)

### Changed

- Keystring processing as per [sui 0.21.0 change](https://github.com/MystenLabs/sui/pull/6989)
- GetTxn now references result dataclass. Updated samples/cmd.py to use new result.
- Code refactoring for all builders in `builders/get_builders.py`
- Added 'lockedUntilEpoch`field to`SuiCoinObject` results (Sui 0.21.0)

### Removed

- `unique` from SuiKeyPairED25519 and SuiKeyPairSECP256K1

## [0.7.0] 2023-01-06

Breaking changes

### Added

- async_gas and async_sub support calling with `--local path/file to non-standard client.yaml`
- Prelim subscription docs
- Elaborated subscription doc with examples
- **StakeSubsidy** added to SuiSystemState result from GetSuiSystemState [0.20.0](https://github.com/FrankC01/pysui/issues/55)
- **delegator_staked_sui_id** field added to PendingDelegator result from GetSuiSystemState [0.20.0](https://github.com/FrankC01/pysui/issues/55)
- **SuiTransactionBuilderMode** enum added in support of executing `sui_batchTransaction` and `sui_moveCall` [0.20.0](https://github.com/FrankC01/pysui/issues/55)
- **GetAllCoinBalances** builder [0.20.0](https://github.com/FrankC01/pysui/issues/55)
- **GetAllCoins** builder [0.20.0](https://github.com/FrankC01/pysui/issues/55)
- **GetDynamicFieldObject** builder [0.20.0](https://github.com/FrankC01/pysui/issues/55)
- **GetDynamicFields** builder [0.20.0](https://github.com/FrankC01/pysui/issues/55)
- **InspectTransaction** builder [0.20.0](https://github.com/FrankC01/pysui/issues/55)
- **InspectMoveCall** builder [0.20.0](https://github.com/FrankC01/pysui/issues/55)
- **consensus_address, worker_address and worker_pubkey_bytes** fields added to ValidatorMetaData

### Fixed

- Signature on subscription handlers (typing Callable)

### Changed

- Workaround for [sui defect](https://github.com/MystenLabs/sui/issues/7052)
- Using new 'temporary' gas retrival API to optimize `async_gas` [discussion](https://github.com/FrankC01/pysui/discussions/50). Targetting
  [milestone](https://github.com/FrankC01/pysui/milestone/5) with [enhancement](https://github.com/FrankC01/pysui/issues/54)
- Dataclasses for result of calling `sui_getSuiSystemState`
- GetCoinTypeBalance (`sui_getBalance`) now returns a single SuiCoinBalance instead of SuiCoinBalance**s** (array of SuiCoinBalance). See above, in Added, GetAllCoinBalances support [0.20.0](https://github.com/FrankC01/pysui/issues/55)
- request_type: SuiRequestType to constructors of sync and async SuiClients. Defaults to WAITFORLOCALEXECUTION

### Removed

- IMMEDIATERETURN and WAITFORTXCERT removed from `SuiRequestType` for txn execution [0.20.0](https://github.com/FrankC01/pysui/issues/55)

## [0.6.0] 2022-12-29

### Added

- New Provider: SuiClient in `sui.sui_clients.subscribe.py` [enhancement](https://github.com/FrankC01/pysui/issues/40)

### Fixed

- ObjectRead supporting dynamic field type representation
- SuiParameterReference supporting str or dict in `reference_to` for scalar types
- Samples: `wallet objects -a ...` was ignoring address

### Changed

BIG BREAKING CHANGES!

- Refactored `sui.sui_types` as a package [breaking changes](https://github.com/FrankC01/pysui/issues/48)
- Refactored `sui.sui_builders` as a package [breaking changes](https://github.com/FrankC01/pysui/issues/48)
- Refactored `sui.sui_txresults` as a package [breaking changes](https://github.com/FrankC01/pysui/issues/48)
- Refactored `sui.sui_rpc` as a package (`sui.sui_clients`) [breaking changes](https://github.com/FrankC01/pysui/issues/48)
- Renamed `SuiAsynchClient` to `SuiClient` [breaking changes](https://github.com/FrankC01/pysui/issues/48)

### Removed

- faux_wallet.py in samples package

## [0.5.1] - 2022-12-20

### Added

- Builders section to documentation

### Fixed

- [bug](https://github.com/FrankC01/pysui/issues/47)

### Changed

### Removed

## [0.5.0] - 2022-12-19

### Added

- Support for `sui_getBalance` [enhancement](https://github.com/FrankC01/pysui/issues/46). This returns
  total balance per coin type (i.e. `0x2::sui::SUI`) for owner (SuiAddress) and is more efficient than getting all coins and
  totalling.
- Support for `sui_getCoins` [enhancement](https://github.com/FrankC01/pysui/issues/46). This returns
  address coins for coin type (i.e. `0x2::sui::SUI`) and is more efficient than getting all coin descriptors and
  sui_getObject for each descriptor.
- Support for `sui_getTotalSupply` [enhancement](https://github.com/FrankC01/pysui/issues/46). This returns the
  total supply of coin_type (i.e. `0x2::sui::SUI`).
- Support for `sui_getSuiSystemState` [enhancement](https://github.com/FrankC01/pysui/issues/46). This returns
  SUI system state information.
- Support for `sui_getTransactionsInRange` [enhancement](https://github.com/FrankC01/pysui/issues/46). This returns a list of transaction digests strings within the queried transaction sequence range: `start` (inclusive) and `end` (exclusive).

### Fixed

- [bug] (https://github.com/FrankC01/pysui/issues/46)

### Changed

### Removed

## [0.4.1] - 2022-12-16

### Added

### Fixed

- SUI 0.19.0 changed type of ObjectRead coin 'balance' from int to string. [bug](https://github.com/FrankC01/pysui/issues/46)

### Changed

### Removed

## [0.4.0] - 2022-12-15

### Added

- Pushed `pysui` 0.3.0 to [PyPi](https://pypi.org/project/pysui/)
- Pushed `pysui` 0.3.0 to [readthedocs](https://pysui.readthedocs.io)
- `dry_run` method added to SuiClient(s) [enhancement](https://github.com/FrankC01/pysui/issues/37)
- `execute_no_sign` method added to SuiClient(s) [enhancement](https://github.com/FrankC01/pysui/issues/37)
- `sign_and_submit` method added to SuiClient(s) [enhancement](https://github.com/FrankC01/pysui/issues/37)
- New 'state' returned from `sui_tryGetPastObject`: `VersionNotFound`
- Support for `sui_executeTransactionSerializedSig`
- `sign_and_submit` uses `sui_executeTransactionSerializedSig` if sui version >= '0.18.0'
- Support (builders and types) for `sui_getTransactionAuthSigners`

### Fixed

- SuiRpcResult [bug](https://github.com/FrankC01/pysui/issues/38)
- [bug](https://github.com/FrankC01/pysui/issues/41)

### Changed

- GetPastObject default version fell back to 1, which no longer exists as the SUI system changed to reflect the
  transaction sequence number that created the object. Version is no longer an optional argument to GetPastObject
- Renamed `asynch_gas.py` to `async_gas.py` in samples
- Extrapolate `type_arg`, if any, in ObjectRead post_init
- Removed creation of a event.loop in the SuiAsyncClient `__init__`

### Removed

## [0.3.0] - 2022-12-04

**Breaking** Changes (noted in bold)

### Added

- Pushed `pysui` 0.2.0-beta to [PyPi](https://pypi.org/project/pysui/)
- Pushed `pysui` 0.2.0-beta to [readthedocs](https://pysui.readthedocs.io/en/v0.2.0-beta/)
- SuiMoveScalarArgument as type for processing results of `sui_getNormalized...` calls
- Added 15 second timeout on SuiClient execute
- Support for `sui_getCoinMetadata` (introduced in sui 0.17.0)

### Fixed

- Corrected return signature `type_arguments` on SuiParameterStruct [fixed](https://github.com/FrankC01/pysui/issues/35)
- Corrected handling of GetObject where ID is package [fixed](https://github.com/FrankC01/pysui/issues/34)
- Various readthedocs nuances
- Added `SuiNullType` with alias tx properties and checking API schema for required/not-required parameters

### Changed

- Added consistent format for `gas` and `mist` in sample scripts
- Factored out command line argument validators for sample scripts
- **\_ClientMixin in `sui_rpc` now check RPC API schema version. Minimmal support is 0.17.0**

### Removed

## [0.2.0] - 2022-12-01

Was originally `0.1.2` but changed to `0.2.0` in line with semantic versioning, well, semantics!

**Breaking** Changes (noted in bold)

### Added

- Pushed `pysui` 0.1.1 to [PyPi](https://pypi.org/project/pysui/)
- Support for `sui_splitCoinEqual` in `sui/sui_builders.py`
- Support for `sui_batchTransaction` in `sui/sui_builders.py`
- **SuiConfig** retains the fully qualified path to `client.yaml` used to initialize it
- SuiConfig adds property (read only) `configuration_path` to `client.yaml`
- SuiConfig adds property (read only) `environment` to the environment in use from client.yaml
- Support for `sui_getNormalizedMoveModule` in sui/sui_builders.py [change](https://github.com/FrankC01/pysui/issues/33)
- Support for `sui_getNormalizedMoveFunction` in sui/sui_builders.py [change](https://github.com/FrankC01/pysui/issues/33)
- Support for `sui_getNormalizedMoveStruct` in sui/sui_builders.py [change](https://github.com/FrankC01/pysui/issues/33)
- Support for `sui_getMoveFunctionArgTypes` in sui/sui_builders.py [change](https://github.com/FrankC01/pysui/issues/33)
- Sphinx generated HTML docs [documentation](https://github.com/FrankC01/pysui/issues/32)

### Fixed

- Object version result [closed](https://github.com/FrankC01/pysui/issues/29)
- Sample wallet construction of object version type and `GetPastObject` in `sui/sui_builders.py`
- **Builder** keyword expansion and initial docs [closed](https://github.com/FrankC01/pysui/issues/30)
- **SuiType** keyword expansion and initial docs [closed](https://github.com/FrankC01/pysui/issues/31)

### Changed

- **SuiClient** and **SuiAsynchClinet** [issue](https://github.com/FrankC01/pysui/issues/27)
- Relaxed build initializer validations [closed](https://github.com/FrankC01/pysui/issues/28)
- **Refactored data model for results of GetPackage. Now produces SuiMovePackage vs MovePackage**
- Renamed `samples/asynch.py` to `samples/asynch_gas.py`

### Removed

## [0.1.1] - 2022-11-23

**Breaking** Changes (noted in bold)

### Added

- Pushed `pysui` 0.0.11 to [PyPi](https://pypi.org/project/pysui/)
- `get_gas_from_faucet` **devnet** only [enhancement](https://github.com/FrankC01/pysui/issues/23)
- Integration testing (**devnet synchronous**) [enhancement](https://github.com/FrankC01/pysui/issues/24)
- Started SuiAsynchClient [enhancement](https://github.com/FrankC01/pysui/issues/17)
- GetPastObject builder implementing `sui_tryGetPastObject` [closes](https://github.com/FrankC01/pysui/issues/25)
- Support for mnemonics and derivation path[closes](https://github.com/FrankC01/pysui/issues/9)
- `recover_key_and_address` in `sui/sui_crypto.py` for lost/destroyed keypair
- `pysui-dev.env` for vscode python module debugging
- `sui-test` (sui move package) added to `tests` for integration testing publish and move-calls
- `samples/asynch.py` small asynchronous sample code

### Fixed

- **Secp256k1** bug fixed [issue](https://github.com/FrankC01/pysui/issues/26)

### Changed

- **SuiClient** and **SuiAsynchClient** deriving from abstracts `Provider`
- `samples.wallet` gas and objects formatting

### Removed

- **SyncHttpRPC** and **AsyncHttpRPC** from `abstracts/client_rpc.py` as part of [issue](https://github.com/FrankC01/pysui/issues/17)
- `mnemonic` and `pynacl` from requirements... redundant with use of `bip-utils`

## [0.0.11] - 2022-11-18

Breaking Release

### Added

- Pushed `pysui` 0.0.10 to [PyPi](https://pypi.org/project/pysui/)
- SUI_COIN_DENOMINATOR: int = 1000000000 to `sui_constants.py`
- CommitteeInfo type , in `sui_types.py`, for `sui_getCommitteeInfo` RPC API response
- `bin/build.sh` for building only and not publishing to PyPi
- EventQueryEnvelope type, in `sui_types.py`, for `sui_getEvents` RPC API response
- `GetTxs` builder in `sui_builders.py` and TransactionQueryEnvelope, in `sui_types.py` for `sui_getTransactions` RPC API response.

### Fixed

- Builder and RPC API parameter name fixes.
- Re-enabled event queries (`sui_getEvents`) on SuiClient (`sui_rpc.py`)
- Closed [issue](https://github.com/FrankC01/pysui/issues/1)
- Closed [issue](https://github.com/FrankC01/pysui/issues/20)
- Closed [issue](https://github.com/FrankC01/pysui/issues/22)

### Changed

- ObjectInfo, and subclasses, moved to dataclass types as per [issue](https://github.com/FrankC01/pysui/issues/1)
- ObjectRead, and subclasses, moved to dataclass types as per [issue](https://github.com/FrankC01/pysui/issues/1)
- SuiNumber renamed to SuiInteger as per [issue](https://github.com/FrankC01/pysui/issues/22)
- Update README.md example to reflect RPC Client method additions
- Handle different 'owner' types in ObjectRead type

### Removed

## [0.0.10] - 2022-11-14

### Added

- CHANGELOG.md
- Hydrate object results from Sui `sui_executeTransaction` API (see sui/sui_tx_return_types.py)
- Transaction result tests (results are static via conftest.py fixtures in tests/unit)
- MovePackage dataclasses from API result
- Added requirements-dev.txt for local development
- DEVELOP.md for local development
- SDK version command in samples wallet
- `bin/` folder for utility functions
- `bin/publish.sh` for publishing `pysui` package to PyPi
- `-v,--version` command to `samples.wallet`
- `sphinx` in `requirements-dev.txt`
- `get_address_object_descriptors` on SuiClient [issue](https://github.com/FrankC01/pysui/issues/20)
- `get_objects_for` on SuiClient [issue](https://github.com/FrankC01/pysui/issues/20)
- `get_object` on SuiClient [issue](https://github.com/FrankC01/pysui/issues/20)
- `get_package` on SuiClient [issue](https://github.com/FrankC01/pysui/issues/20)
- `pay_txn` on SuiClient [issue](https://github.com/FrankC01/pysui/issues/20)
- `pay_sui_txn` on SuiClient [issue](https://github.com/FrankC01/pysui/issues/20)
- `pay_allsui_txn` on SuiClient [issue](https://github.com/FrankC01/pysui/issues/20)
- `transfer_sui_txn` on SuiClient [issue](https://github.com/FrankC01/pysui/issues/20)
- `transfer_object_txn` on SuiClient [issue](https://github.com/FrankC01/pysui/issues/20)
- `merge_coin_txn` on SuiClient [issue](https://github.com/FrankC01/pysui/issues/20)
- `split_coin_txn` on SuiClient [issue](https://github.com/FrankC01/pysui/issues/20)
- `move_call_txn` on SuiClient [issue](https://github.com/FrankC01/pysui/issues/20)
- `publish_package_txn` on SuiClient [issue](https://github.com/FrankC01/pysui/issues/20)

### Changed

- Absolute to relative imports
- Fixed [issue](https://github.com/FrankC01/pysui/issues/12)
- Moved signed transaction handling to sui/sui_rpc.py from faux_wallet
- Moved configuration management to ClientConfig and SuiConfig from faux_wallet
- Moved content of sui/sui_tx_return_types to sui/sui_types
- Fixed typo in transaction return type class `Status`
- Added builder callback for handling RPC response to types (sui/sui_builder.py)
- Changes to support Sui configuration files (both devnet and local) changes for RPC endpoints
- Added new RCP API type introduced 'boolean' in RPC API calls and results
- Simplified requirements.txt
- Added `pysui` to PyPi for ease of installing and using
- Changed sample command line to use `--local` instead of `--cfg`
- When parsing sui configurations, the 'active_env' now drives RPC selection
- Added `build`, and `twine` to `requirements-dev.txt`
- Published 0.0.8 to PyPi
- Published 0.0.9 to PyPi
- Moved `get_type_descriptor` in `faux_wallet.py` heavy lifting to `get_address_object_descriptors` on SuiClient
- Fixed transaction result `deleted` effect for merge-coin transaction to use `GenericRef` result versus `GenericOwnerRef`

### Removed

- sui/sui_tx_return_types.py
- All `events` commands from sample as they've been removed in RPC API in favor of general `sui_getEvents`. Will support in future.
- `get_package_object`
- NFT qualifiers [issue](https://github.com/FrankC01/pysui/issues/21)
