# Release 1.0.0 — Module Cut Analysis (Revised: Symbol-Level Deep Scan 2026-05-17)

**Cut:** Remove all JSON-RPC and synchronous GQL code.
**Keep:** Async GQL (`sui_pgql/` async paths), gRPC (`sui_grpc/`), shared infrastructure (`sui_common/`, `sui_bcs/`, `sui_crypto.py`, `sui_config.py`, `sui_constants.py`, `sui_excepts.py`).

Legend: **CD** = Can Delete (entire file) | **PD** = Partial Delete (keep list noted) | **K** = Keep (no changes)
*(reloc)* = confirmed K for now; candidate for relocation after this cut is applied

---

## pysui/abstracts/

```
__init__.py          PD  strip AbstractType import/export only
                         (all other exports remain: Builder/RpcResult/Provider
                         from client_rpc.py which is now K;
                         AsyncClientBase, ClientConfiguration, CrefType,
                         KeyPair, PrivateKey, PublicKey, SignatureScheme,
                         SuiBaseType, SuiScalarType from PD files)
async_client.py      PD  keep: AsyncClientBase
                         delete: all other classes
client_config.py     PD  keep: ClientConfiguration, CrefType
                         delete: all other classes
client_keypair.py    PD  keep: KeyPair, PrivateKey, PublicKey, SignatureScheme
                         delete: all other classes
client_rpc.py        K   Builder/RpcResult/Provider still imported by K files
                         (pgql_query.py, txb_transaction_builder.py, trxn_base.py)
                         *(reloc)*
client_types.py      PD  keep: SuiBaseType, SuiScalarType
                         delete: AbstractType (only other top-level name)
```

## pysui/sui/ (top-level)

```
sui_apidesc.py       CD
sui_bcsl.py          CD
sui_txn_validator.py CD
sui_utils.py         PD  keep: serialize_uint32_as_uleb128, hexstring_to_sui_id,
                             publish_buildg2 (+ _compile_projectg2, CompiledPackage),
                             partition,
                             hexstring_to_list, b58str_to_list, from_list_to_b58str,
                             sui_base_get_config
                         delete: all coercion functions (as_sui_address, as_object_id,
                             as_sui_string, as_sui_integer, as_sui_array, as_sui_map,
                             as_sui_boolean, as_sui_txbytes, as_sui_signature,
                             as_sui_txdigest) and COERCION_* dicts
                         note: hexstring_to_list / b58str_to_list / from_list_to_b58str
                               added to keep — imported by sui_bcs/bcs_stnd.py and bcs.py
                               sui_base_get_config added — imported by sui_config.py
                               *(reloc candidates post-cut)*
```

## pysui/sui/sui_bcs/

```
(all files)          K
```

## pysui/sui/sui_builders/

```
(all files)          CD
```

## pysui/sui/sui_clients/

```
__init__.py          CD
async_client.py      CD
subscribe.py         CD
sync_client.py       CD
common.py            K   SuiRpcResult still imported by pysui/__init__.py and K files
                         *(reloc)*
```

## pysui/sui/sui_common/ (only files with changes)

```
_internal_commands.py  CD
bcs_ast.py             PD  keep: BcsAst, Node, NodeVisitor
                            (used by move_to_bcs.py)
```
txb_transaction_builder.py  K   Protocol-agnostic PTB builder (gRPC + async GQL)
                                 *(cleanup)* contains duplicate PureInput class —
                                 identical copy exists in txb_pure.py (the canonical
                                 source); all 5 import sites use txb_pure.py;
                                 txb_transaction_builder.py should import PureInput
                                 from txb_pure instead of defining its own

All other `sui_common/` files: **K**

## pysui/sui/sui_grpc/

```
(all files)          K
```

## pysui/sui/sui_pgql/ (only files with changes)

```
pgql_clients.py           PD  keep: full file; remove sync deprecation shim (~line 250)
pgql_fragments_beta.py    CD  (confirmed: zero K-file imports)
pgql_schema.py            K
pgql_sync_txn.py          CD
pgql_wallet_deser.py      CD
pgql_wallet_ser.py        CD
pgql_wallet2txn_deser.py  CD
```
All other `sui_pgql/` files: **K**

## pysui/sui/sui_txn/

```
(all files)          CD
```

## pysui/sui/sui_txresults/

```
__init__.py          PD  strip package_meta.py imports/re-exports only
                         (complex_tx.py, single_tx.py, common.py are now K;
                         keep all their exports)
                         Import line to strip: from pysui.sui.sui_txresults.package_meta import *
common.py            K   GenericRef still imported by sui_bcs/bcs.py
                         *(reloc)*
complex_tx.py        K   Transaction, TransactionData, ProgrammableTransaction,
                         GasCostSummary, MultiSig, Event, ZkLoginAuthenticator
                         and others still imported by pgql_query.py,
                         pgql_fragments.py, sui_bcs/bcs.py, sui_grpc/,
                         sui_common/async_txn.py, sui_common/trxn_base.py
                         *(reloc)*
package_meta.py      CD
single_tx.py         K   AddressOwner, SharedOwner, ObjectOwner, ImmutableOwner,
                         ObjectRead, ObjectReadData, GenericRef, ProtocolConfig,
                         StakedSui, Validator, ValidatorSet, TransactionConstraints
                         and others still imported by pgql_query.py,
                         pgql_fragments.py, sui_bcs/bcs_txne.py, sui_grpc/,
                         sui_common/ modules
                         *(reloc)*
```

## pysui/sui/sui_types/

```
__init__.py          PD  strip event_filter, transaction_filter, collections
                         imports/re-exports; keep address.py exports (now K),
                         keep scalars.py exports (PD with expanded keep list)
address.py           K   SuiAddress deeply embedded in sui_config.py, sui_bcs/bcs.py,
                         sui_crypto.py, sui_common/ modules
                         *(elim)* — SuiAddress is a legacy str wrapper; most usages
                         construct from str then immediately unwrap via .address;
                         client_config.py already handles str|SuiAddress interchangeably;
                         candidate for full elimination (replace with plain str) rather
                         than relocation
collections.py       CD
event_filter.py      CD
scalars.py           K   all top-level names still in use by K files
                         *(reloc)*
transaction_filter.py  CD
```

---

## tests/

```
sync_tests/__init__.py          CD
unit_tests/test_deprecations.py PD  remove sync txn imports and test cases
                                    (pgql_sync_txn refs)
```
All other `tests/` files: **K**

---

## samples/

```
(all files)          K   all async dual protocol; no legacy dependencies
```

---

## Symbol-Level Scan Summary (2026-05-17)

**Reclassifications from original analysis:**
- `abstracts/client_rpc.py`: CD → K (Builder/RpcResult/Provider still imported by K files)
- `sui_txresults/common.py`: CD → K (GenericRef imported by bcs.py)
- `sui_txresults/complex_tx.py`: CD → K (Transaction/TransactionData/etc. imported by pgql+grpc+sui_common)
- `sui_txresults/single_tx.py`: PD (keep TransactionConstraints only) → K (most types still consumed by K files)
- `sui_types/address.py`: CD → K (SuiAddress embedded throughout)
- `sui_pgql/pgql_fragments_beta.py`: CD confirmed (zero K-file imports)
- `sui_utils.py`: PD keep list expanded (hexstring_to_list, b58str_to_list, from_list_to_b58str, sui_base_get_config added)
- `sui_types/scalars.py`: PD → K (all top-level names still in use by K files)

**Potential relocations post-cut (marked *(reloc)* above):**
- `abstracts/client_rpc.py` → merge into `sui_common/` or `abstracts/async_client.py`
- `sui_common/txb_transaction_builder.py` → *(cleanup)* remove duplicate PureInput class;
  replace with import from txb_pure.py
- `sui_txresults/common.py` → merge into `sui_common/types.py`
- `sui_txresults/complex_tx.py` → merge into `sui_common/types.py`
- `sui_txresults/single_tx.py` → merge into `sui_common/types.py`
- `sui_types/address.py` → *(elim)* eliminate SuiAddress entirely; replace with plain str
                            throughout (sui_config.py, sui_crypto.py, sui_bcs/, sui_common/,
                            sui_clients/common.py, sui_txresults/single_tx.py, pysui/__init__.py)
- `sui_types/scalars.py` → consolidate into `sui_common/` or `sui_bcs/`
- `sui_utils.py` utility functions → consolidate into `sui_common/`

---

## Detailed Fill-In Report

### 1. abstracts/client_types.py — Names to Delete

**Top-level names found:**
- `AbstractType` — DELETE (marked as ABC base class; only SuiBaseType/SuiScalarType subclasses are used)
- `SuiBaseType` — KEEP
- `SuiScalarType` — KEEP

**Conclusion:** Only `AbstractType` needs to be stripped from `__init__.py` exports.

### 2. sui_types/scalars.py — Names to Delete

**Top-level names found:**
- `SuiNullType` — KEEP (deprecated but still exported and used)
- `SuiString` — KEEP (deprecated but still exported and used)
- `SuiTxBytes` — KEEP (deprecated but still exported and used)
- `SuiSignature` — KEEP (deprecated but still exported and used)
- `SuiTransactionDigest` — KEEP (deprecated but still exported and used)
- `ObjectID` — KEEP (deprecated but still exported and used)
- `SuiBoolean` — KEEP (deprecated but still exported and used)
- `SuiInteger` — KEEP (deprecated but still exported and used)
- `SuiIntegerType` — KEEP (base class for SuiU* types)
- `SuiU8`, `SuiU16`, `SuiU32`, `SuiU64`, `SuiU128`, `SuiU256` — KEEP (actively used for BCS encoding)

**Conclusion:** No deletions — scalars.py reclassified as K. All top-level names are still in use by K files.

### 3. sui_txresults/__init__.py — package_meta.py Imports to Strip

**Import line to remove:**
```python
from pysui.sui.sui_txresults.package_meta import *
```

**Replacement:** Delete this line entirely (line 19).

**Remaining imports (all KEEP):**
```python
from pysui.sui.sui_txresults.common import *
from pysui.sui.sui_txresults.single_tx import *
from pysui.sui.sui_txresults.complex_tx import *
```

---

## Lazy Import Findings (2026-05-17)

During integration testing (Step 5), a class of failure not caught by the symbol-level scan was discovered: **lazy imports** — imports placed inside method bodies rather than at module top level. The symbol-level grep enumerated module-level import lines only; imports inside function or method bodies are invisible to that approach.

### Discovered instance: `sui_crypto.py` → deleted `sui_txn/transaction_builder.py`

`pysui/sui/sui_crypto.py` contained lazy imports of `PureInput` from the deleted `pysui.sui.sui_txn.transaction_builder` module, embedded inside three method bodies:

| Method | Action taken |
|--------|-------------|
| `SuiPublicKey.verify_personal_message()` | Entire method deleted — `@deprecated`, replaced by `VerifyPersonalMessageSignature` SuiCommand (Plan #8) |
| `SuiKeyPair.verify_personal_message()` | Same — entire method deleted |
| `SuiPrivateKey.sign_secure_personal_message()` | Active method — import redirected to canonical `pysui.sui.sui_common.txb_pure.PureInput` |

**Root cause:** `sui_txn/` was swept as a bulk CD without grepping its exported symbols against all K files. K files were not reverse-checked for lazy imports — only module-level import lines were scanned.

### Implication for Step 6 (rescan)

Step 6 must grep not only module-level imports but also inline/lazy import patterns across every deleted module path (all of `sui_builders/`, `sui_clients/`, `sui_txn/`, and all scattered CDs):

```bash
grep -rn "sui_builders\|sui_clients\|sui_txn\|sui_apidesc\|sui_bcsl\|sui_txn_validator\|pgql_sync_txn\|pgql_wallet\|pgql_fragments_beta\|package_meta\|_internal_commands" pysui/ samples/ tests/
```
