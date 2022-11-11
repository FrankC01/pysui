# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - Cummulative: Current dev version - 0.0.9
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
- Added `build` and `twine` to `requirements-dev.txt`
- Published 0.0.8 to PyPi


### Removed
- sui/sui_tx_return_types.py
- All "events" from sample as they've been removed in RPC API in favor of general `sui_getEvents`. Will support in future.