# scratch/ — Integration Test Gas Management Tools

Dev scripts and data files for pysui integration test gas budgeting.
These are git-tracked but excluded from wheel builds (not a Python package).

## Files

### `test_cost_model.json`
Source of truth for all PTB patterns exercised by the integration test suite.
Each pattern records: withdrawal form, fee tier, fee_mist, sui_draw, sui_coins,
and whether it is ignored (contract-dependent patterns with static fee estimates).
Edit this file when adding new integration test PTB patterns.

### `simulate_costs.py`
**Hits the live chain (devnet).** Runs SimulateTransactionKind for fee tiers A/B/C,
updates `test_cost_model.json` if any tier has changed, then prints fat-coin and
address-balance budget totals across all patterns.

Run when adding new PTB patterns to verify reserve totals still fit within
`REQUIRED_COIN_BUDGET` / `REQUIRED_ADDR_BUDGET` in `conftest.py`.

```
. env/bin/activate && python scratch/simulate_costs.py
```

### `gas_management_sim.py`
**Safe to run anytime — no chain mutations.** Math-only simulation of the full
bank setup and withdraw sequence across all 65 call sites in conftest.py.
Reads `test_cost_model.json` and `gas_management_xref.json`; prints coverage
and budget totals. Use to verify model consistency without touching devnet.

```
. env/bin/activate && python scratch/gas_management_sim.py
```

### `gas_management_xref.json`
65-entry cross-reference mapping every `bank.withdraw()` call site in conftest.py
to its pattern in `test_cost_model.json`. Authoritative source for Step 6
insertion — do not re-scan conftest.py; consult this file.

### `bank_gas_impl.py`
**DO NOT RUN.** Write-only review artifact showing the live `bank.withdraw()`
implementation. Running it would mutate account coins and objects on devnet.
Exists for code review only — Frank and any review agent assess it in-editor.
