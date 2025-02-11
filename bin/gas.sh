#! /bin/bash

#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# Refresh gas on address

for i in {1..10}
do
    sui client faucet --address $1
done
