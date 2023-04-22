# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unpublished]

### Added

- GetLoadedChildObjects builder and reponse supporting Sui RPC API `sui_getLoadedChildObjects` in 0.33.0

### Fixed

- On testnet code has changes in `rpc.discover` making a field optional.

### Changed

### Removed

- `additional_signature`, other than sender and sponsor, are not supported by the tx processor in Sui. Removed
  the property in `SignerBlock`

## [0.17.0] - 2023-04-22

Breaking Changes

### Added

- Breaking: Assertion on SuiTransaction that will fail operations on it if it's been executed already
- Implemented NameServiceAddress and NameServiceNames builders and results for supporing `suix_resolveNameServiceAddress` and `suix_resolveNameServiceNames` respectivly.
- `merge_gas_budget` to SuiTransaction constructor. When attempting to find available gas coin for transaction, this flag if true,
  allows a merge of coins to meet budget demand. Defaults to False

### Fixed

- Field declaration in Effects result.
- Bug in SuiTransaction builder argument resolution method.

### Changed

- Extended CompiledPackage to hold blake2b digest to match chain digest calculation. Used in package upgrades in SuiTransaction.
- Introspection on SuiTransaction `move_call` target function to better return reusuable command results
- Breaking: SuiTransaction constructor and execute methods simplified while making signing more powerful
- Breaking: SuiTransaction `split_coin` now takes list of amounts and returns list of results.
- Breaking: SuiTransaction `move_call` now takes target string in form: `"package_id::module_name::function_name"`
- Breaking: `build_for_execute` method made private on SuiTransaction

### Removed

- Breaking: `gasses` property from SuiTransaction

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
