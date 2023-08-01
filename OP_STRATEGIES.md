# pysui Operational Strategies

## pysui Release Strategy

We routinely verify the `pysui`  SDK ahead of the any upcoming release/deployments from MystenLabs:

### MystenLabs/Sui deployments

- MystenLabs/Sui deployment schedule _**roughly**_ follows
  - New major or minor release deploy to `devnet` (weekly) on Monday's
  - The release is then propogated to `testnet` on or around Tuesday's
  - Depending on testnet issues, one or more patch releases may redeploy on `testnet`
  - The release, when ready, deploys to `mainnet` on Wednesday's

Ultimatley, the Sui discord "updates" channels are the best places to find when deployments actually do happen.

### pysui release pushes and publishing

We will always accumulate and push changes with `pysui` to github first. However, we will publish to PyPi when:
- MystenLab's introduce breaking changes in their releases that we align `pysui` with
- **We** introduce breaking changes and/or introduce new features (bumps the minor version)
- **We** bump versions of any depedencies of `pysui` (bumps minor and/or path version)
- **We** remove any previously marked 'Deprecated' functions, classes and/or methods (bumps minor version)
- **We** fix more than corner, or edge, bugs that would affect the general population.

## Deprecation Strategy

Functions, classes and/or methods marked 'Deprecated' will be removed from the code base (after initial markup)
following 2 releases on PyPi.

Refer to the [CHANGELOG](https://github.com/FrankC01/pysui/blob/main/CHANGELOG.md) for awareness when we first include Deprecated markups.
