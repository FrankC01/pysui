# develop pysui

SUI Python Client SDK for Sui

This document is for contributors or the curious developer

## Ready to run

Requires:

- Linux or macos (x86_64 or M1)
- Rust (stable) which also includes rustup and cargo
- python 3.10 or greater
- Rust (stable) which also includes rustup and cargo
- pkg-config
- libtool
- git
- sui binaries to support `publish` function
- protoc for protobuf generation

### Clone the pysui repo

`git clone git@github.com:FrankC01/pysui.git

### Setup virtual environment

`python3 -m venv env`

### Activate

`source env/bin/activate`

### Load core packages

`pip list`

- If you get a warning about upgrading pip... do so

`pip install -r requirements.txt`

### Load anciallary development packages

`pip install -r requirements-dev.txt` .

At this point you can decide to run samples, etc. or build and install
pysui into your own development environment. For the latter, first build the pysui
distribution:

`bin/package-build.sh`

You can then `pip install <LOCAL-PATH-TO-PYSUI-REPO>` to your own virtual environment
assuming you've set one up for own app/library development.

### Run sample wallet app for help

See [README](https://github.com/FrankC01/pysui/blob/main/README.md)

## Integration Tests

Integration tests live in `tests/integration_tests/` and require a live Sui node with a funded wallet.

### Recommended environment: devnet

Devnet is the recommended profile for running the integration test suite:

- The devnet faucet dispenses **10 SUI per request** (testnet gives 1 SUI and there is no faucet for mainnet).
- The devnet faucet tolerates back-to-back requests without rate-limiting.
- The testnet faucet rate-limits aggressively — consecutive requests return HTTP 429,
  which can leave the test session under-funded mid-run and cause non-deterministic failures.

To run against testnet or mainnet, **pre-fund your testnet wallet to at least 15 SUI** before starting
the suite and do not rely on the faucet being called during the run.

Mainnet and local node profiles are skipped automatically (no faucet is configured for them).

### Serial execution required

Sui equivocation: parallel transactions on the same non-shared object (e.g. the gas coin)
lock those objects until the next epoch. **Never run integration tests with `-n` / `--dist` flags.**

```bash
pytest tests/integration_tests/   # correct
pytest tests/integration_tests/ -n4  # WRONG — will cause equivocation errors
```

### Publish tests require the sui CLI binary

Tests that exercise `publish` and `publish_upgrade` compile Move source with the `sui` CLI.
If the binary is not configured in your PysuiConfiguration, those tests are skipped automatically.

### Running

```bash
# Ensure your active pysui profile points to devnet
pytest tests/integration_tests/ -v
```
