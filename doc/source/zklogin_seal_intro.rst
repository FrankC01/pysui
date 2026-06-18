Introduction
============

pysui 1.1.0 adds support for two complementary privacy and authentication primitives for
the Sui blockchains: **zkLogin** and **SEAL**. Both are accessed through the
``pysui.zklogin_seal`` package, which requires the ``pysui[zklogin-seal]`` extra.

zkLogin
-------

zkLogin is a Sui authentication primitive that lets users sign transactions using an
existing OAuth2 identity — Google, Facebook, or Twitch — without exposing a
traditional private key.

The flow works by:

#. Generating a short-lived *ephemeral keypair* tied to a *nonce* embedded in the OAuth login.
#. Obtaining a JWT (id_token) from the OAuth provider with the nonce embedded.
#. Deriving a deterministic Sui address from the JWT's key claim (e.g. ``sub``).
#. Fetching a *zero-knowledge proof* from a prover service that proves possession of
   the JWT without revealing it on-chain.
#. Signing transactions with the ephemeral keypair + ZK proof — the result is a
   standard Sui signature accepted by validators.

The same salt + same provider identity always produces the same Sui address.

SEAL
----

SEAL (Sui Encryption and Access Layer) is an Identity-Based Encryption (IBE) system
built on Sui. It enables threshold encryption of arbitrary data under on-chain
access policies — only addresses that satisfy the policy (e.g. membership in an
allowlist) can decrypt.

The flow works by:

#. **Encrypting**: the sender fetches IBE public keys from one or more on-chain key
   servers and encrypts data under a policy identity derived from a Sui object ID.
#. **Decrypting**: the recipient builds an unsigned ``seal_approve`` PTB that proves
   eligibility, submits it to each key server, and reassembles the decryption key
   from the returned shares (threshold scheme).

Key servers come in two flavours:

* **Non-committee**: individual key servers, each holding an independent share.
* **Committee** (aggregator): a single endpoint that fans out to multiple committee
  members internally and returns aggregated shares — simpler for callers but backed
  by a quorum.

See :doc:`seal` for a full walkthrough including code examples.
