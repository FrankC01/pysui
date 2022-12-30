# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unpublished]

### Added
- async_gas and async_sub support calling with `--local path/file to non-standard client.yaml`
- Prelim subscription docs
- Elaborated subscription doc with examples

### Fixed
- Signature on subscription handlers (typing Callable)

### Changed
- Workaround for [sui defect](https://github.com/MystenLabs/sui/issues/7052)

### Removed

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
- **_ClientMixin in `sui_rpc` now check RPC API schema version. Minimmal support is 0.17.0**

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