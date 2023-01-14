#!/usr/bin/env python3
#    Copyright 2022 Frank V. Castellucci
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#        http://www.apache.org/licenses/LICENSE-2.0
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

# -*- coding: utf-8 -*-

"""SUI Keystore conversion utility."""

import os
import sys
import shutil
import json
import base64
import argparse
from pathlib import Path

DEFAULT_SUI_KEYSTORE: str = "~/.sui/sui_config/sui.keystore"
OLD_SUI_KEYPAIR_LEN: int = 88
NEW_SUI_KEYPAIR_LEN: int = 44


def build_parser(in_args: list) -> argparse.Namespace:
    """Build the argument parser structure."""
    # Base menu
    parser = argparse.ArgumentParser(
        description="Convert ed25519, secp256k1 and secp256r1 keys to new 0.21.0 keystore format. A backup (.bak) of file is created",
        add_help=True,
        usage="%(prog)s [options] command [--command_options]",
    )
    exc_group = parser.add_mutually_exclusive_group(required=True)
    exc_group.add_argument(
        "-d", "--default", help="Convert default SUI keystore keystrings", dest="default", action="store_true"
    )
    exc_group.add_argument("-p", "--path-to-keystore", help="Convert keystrings from keystore in path", dest="usepath")

    return parser.parse_args(in_args if in_args else ["--help"])


def conver_key(in_key_str: str) -> str:
    """conver_key Converts an old base64 keystring to new base64 keystring.

    :param in_key_str: Keystring from keystore
    :type in_key_str: str
    :return: New keystring minus the public key bytes as base64 string.
    :rtype: str
    """
    if len(in_key_str) == OLD_SUI_KEYPAIR_LEN:
        print(f"Converting {in_key_str}")
        raw_ks = base64.b64decode(in_key_str)
        key_scheme = raw_ks[0]
        new_bytes = bytearray([key_scheme])
        print(f"    keytype signature {key_scheme} len {len(raw_ks)} ", end="")
        match key_scheme:
            case 0:
                print("-> ed25519")
                new_bytes.extend(bytes(raw_ks[-32:]))
            case 1:
                print("-> secp256k1")
                new_bytes.extend(bytes(raw_ks[-32:]))
            case 2:
                print("-> secp256r1")
                new_bytes.extend(bytes(raw_ks[-32:]))
            case _:
                raise ValueError(f"ERROR: Unknown keytype {key_scheme}")
        out_key_str = base64.b64encode(bytes(new_bytes)).decode()
    elif len(in_key_str) == NEW_SUI_KEYPAIR_LEN:
        print("Keypair has already been converted, re-saving")
        out_key_str = in_key_str
    else:
        raise ValueError(f"{in_key_str} is not a valid pre 0.21.0 keystring length")
    print()
    if len(out_key_str) == NEW_SUI_KEYPAIR_LEN:
        return out_key_str
    raise ValueError(f"{out_key_str} does not conform to new keypair string length")


def covert_keys(keystore_file_path: Path) -> None:
    """Manage file backup and iterate through keys."""
    if keystore_file_path.exists():
        try:
            keyfile = keystore_file_path.name + ".bak"
            backup = keystore_file_path.parent.joinpath(keyfile)
            print(f"\nBacking up existing keystore to '{backup}'")
            if backup.exists():
                print(f"ERROR: Backup file '{backup}' already exists. Move the backup file and re-run")
                sys.exit(-1)
            shutil.copyfile(keystore_file_path, backup)
            print(f"Created backup: '{backup}'\n")
            print(f"Converting keys in keystore: '{keystore_file_path}'")
            with open(keystore_file_path, encoding="utf8") as keyfile:
                keystrings = json.load(keyfile)
            print(f"Old keystrings {json.dumps(keystrings,indent=2)}")
            new_keystrings = [conver_key(x) for x in keystrings]
            json_keys = json.dumps(new_keystrings, indent=2)
            print(f"Writing new keystrings {json_keys}")
            with open(keystore_file_path, "w", encoding="utf8") as keystore:
                keystore.write(json_keys)
            print("\nOperation completed!\n")
        except (IOError, ValueError) as ioe:
            print(f"Exception received: {ioe}")
            print(f"Restoring keyfile from {backup}")
            shutil.copyfile(backup, keystore_file_path)
            sys.exit(-1)
    else:
        print(f"ERROR: Keystore file not found at '{keystore_file_path}'")
        sys.exit(-1)


def main():
    """Main entry point for utility."""
    parsed = build_parser(sys.argv[1:].copy())
    if parsed.default:
        covert_keys(Path(os.path.expanduser(DEFAULT_SUI_KEYSTORE)))
    elif parsed.usepath:
        covert_keys(Path(os.path.expanduser(parsed.usepath)))


if __name__ == "__main__":
    main()
