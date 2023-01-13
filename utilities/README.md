# pysui utilities

Various helper utilities for users and developers.

## keys_to_0210 - Sui 0.20.0 and below keystore to 0.21.0 keystore convert

SUI 0.21.0 introduces a change to keystore (file) keystring persist. We are providing
a utility here to transition existing keys to the new format for those
who want to keep any keys created prior. For reference, see [sui change](https://github.com/MystenLabs/sui/pull/6989).

This utility SHOULD BE RUN BEFORE USING ANY OF `pysui` Sui Clients. If you've deleted your previous keystore and created
new keys with SUI 0.21.0 binaries, you can ignore running this utility

### Usage

Utilitiy operation:

1. Backs up the keystore file as defined by options below
2. Each ed25519, secp256k1 and/or secp256r1 key will be disassembled as per the SUI keystring definition
3. The converted keys will be written back to the source, overwritting original
4. If any error occurs, you can go to the path and `rm sui.keystore` and then `mv sui.keystore.bak sui.keystore`
5. If errors continue after trying again, please open an issue

```bash
fastfrank@~/frankc01/pysui $ utilities/keys_to_0210.py -h
usage: keys_to_0210.py [options] command [--command_options]

Convert ed25519, secp256k1 and secp256r1 keys to new 0.21.0 keystore format. A backup (.bak) of file is created

options:
  -h, --help            show this help message and exit
  -d, --default         Convert default SUI keystore keystrings
  -p USEPATH, --path-to-keystore USEPATH
                        Convert keystrings from keystore in path
```

`-d` Option will look for keys in keystore file to convert in `~/.sui/sui_config/sui.keystore`

`-p` Option allows you to specify path to keystore to convert keys in (example below)

### Example using `-p path_to_file` option

```bash
fastfrank@~/frankc01/pysui $ utilities/keys_to_0210.py -p ~/sui_0201/sui_config/sui.keystore

Backing up existing keystore to '/Users/fastfrank/sui_0201/sui_config/sui.keystore.bak'
Created backup: '/Users/fastfrank/sui_0201/sui_config/sui.keystore.bak'

Converting keys in keystore: '/Users/fastfrank/sui_0201/sui_config/sui.keystore'
Old keystrings [
  "AKcurSAcUDafzezOTYPd+7wdBRbL1nCwa95ebl/Wc1wyEYI+ozwxNs1IuNZDiU1GL2B8Sqfsg7FgUT55m3If148=",
  "APZBPYYFPAF1bQLN6sAI362UcFJNkAfxyjbNc1m1njwDiOsV/paaGyppmwXVMGeH7vmG+2/BGd2iwp9yUHFIJ9s=",
  "AGbpmvhjNXKGLMkvMHnw03HwSerM3hAyEQ+OVzmGH43qqAt5XDjCGshLh/axD7MLHBcGkpTWdNWRJBPE7dNaCLY=",
  "AQOHn7v/wZzH9XNJAhl6jfSpaXDbtzPCCBzNGrtybVAtoc+Y9kNwaPpzYTY/0zVJvPMS60ou6qrVDLTzizC550Gc"
]
Converting AKcurSAcUDafzezOTYPd+7wdBRbL1nCwa95ebl/Wc1wyEYI+ozwxNs1IuNZDiU1GL2B8Sqfsg7FgUT55m3If148=
    keytype signature 0 len 65 -> ed25519

Converting APZBPYYFPAF1bQLN6sAI362UcFJNkAfxyjbNc1m1njwDiOsV/paaGyppmwXVMGeH7vmG+2/BGd2iwp9yUHFIJ9s=
    keytype signature 0 len 65 -> ed25519

Converting AGbpmvhjNXKGLMkvMHnw03HwSerM3hAyEQ+OVzmGH43qqAt5XDjCGshLh/axD7MLHBcGkpTWdNWRJBPE7dNaCLY=
    keytype signature 0 len 65 -> ed25519

Converting AQOHn7v/wZzH9XNJAhl6jfSpaXDbtzPCCBzNGrtybVAtoc+Y9kNwaPpzYTY/0zVJvPMS60ou6qrVDLTzizC550Gc
    keytype signature 1 len 66 -> secp256k1

Writing new keystrings [
  "ABGCPqM8MTbNSLjWQ4lNRi9gfEqn7IOxYFE+eZtyH9eP",
  "AIjrFf6WmhsqaZsF1TBnh+75hvtvwRndosKfclBxSCfb",
  "AKgLeVw4whrIS4f2sQ+zCxwXBpKU1nTVkSQTxO3TWgi2",
  "Ac+Y9kNwaPpzYTY/0zVJvPMS60ou6qrVDLTzizC550Gc"
]

Operation completed!
```
