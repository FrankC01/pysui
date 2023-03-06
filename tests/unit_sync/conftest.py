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

"""Fixtures for testing."""

import pytest


@pytest.fixture
def package_track_result():
    """Return a normalized package content."""
    return {
        "base": {
            "file_format_version": 6,
            "address": "0xc743a1d880d0545945b1a80d29e9f2650b884e85",
            "name": "base",
            "friends": [],
            "structs": {
                "Service": {
                    "abilities": {"abilities": ["Key"]},
                    "type_parameters": [],
                    "fields": [
                        {
                            "name": "id",
                            "type_": {
                                "Struct": {"address": "0x2", "module": "object", "name": "UID", "type_arguments": []}
                            },
                        },
                        {"name": "admin", "type_": "Address"},
                    ],
                },
                "ServiceTracker": {
                    "abilities": {"abilities": ["Key"]},
                    "type_parameters": [],
                    "fields": [
                        {
                            "name": "id",
                            "type_": {
                                "Struct": {"address": "0x2", "module": "object", "name": "UID", "type_arguments": []}
                            },
                        },
                        {"name": "initialized", "type_": "Bool"},
                        {"name": "count_accounts", "type_": "U64"},
                    ],
                },
                "Tracker": {
                    "abilities": {"abilities": ["Store", "Key"]},
                    "type_parameters": [],
                    "fields": [
                        {
                            "name": "id",
                            "type_": {
                                "Struct": {"address": "0x2", "module": "object", "name": "UID", "type_arguments": []}
                            },
                        },
                        {"name": "initialized", "type_": "Bool"},
                        {"name": "owner", "type_": "Address"},
                        {"name": "accumulator", "type_": {"Vector": "U8"}},
                    ],
                },
            },
            "exposed_functions": {
                "accounts_created": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0xc743a1d880d0545945b1a80d29e9f2650b884e85",
                                    "module": "base",
                                    "name": "ServiceTracker",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": ["U64"],
                },
                "add_from": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0xc743a1d880d0545945b1a80d29e9f2650b884e85",
                                    "module": "base",
                                    "name": "Tracker",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {"Vector": "U8"},
                    ],
                    "return_": [],
                },
                "add_to_store": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0xc743a1d880d0545945b1a80d29e9f2650b884e85",
                                    "module": "base",
                                    "name": "Tracker",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "U8",
                    ],
                    "return_": ["U64"],
                },
                "add_value": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0xc743a1d880d0545945b1a80d29e9f2650b884e85",
                                    "module": "base",
                                    "name": "Tracker",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "U8",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "add_values": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0xc743a1d880d0545945b1a80d29e9f2650b884e85",
                                    "module": "base",
                                    "name": "Tracker",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {"Vector": "U8"},
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "create_account": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0xc743a1d880d0545945b1a80d29e9f2650b884e85",
                                    "module": "base",
                                    "name": "Service",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0xc743a1d880d0545945b1a80d29e9f2650b884e85",
                                    "module": "base",
                                    "name": "ServiceTracker",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "Address",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "drop_from_store": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0xc743a1d880d0545945b1a80d29e9f2650b884e85",
                                    "module": "base",
                                    "name": "Tracker",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "U8",
                    ],
                    "return_": ["U8"],
                },
                "has_value": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0xc743a1d880d0545945b1a80d29e9f2650b884e85",
                                    "module": "base",
                                    "name": "Tracker",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "U8",
                    ],
                    "return_": ["Bool"],
                },
                "remove_value": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0xc743a1d880d0545945b1a80d29e9f2650b884e85",
                                    "module": "base",
                                    "name": "Tracker",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "U8",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "stored_count": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0xc743a1d880d0545945b1a80d29e9f2650b884e85",
                                    "module": "base",
                                    "name": "Tracker",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": ["U64"],
                },
                "transfer": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Struct": {
                                "address": "0xc743a1d880d0545945b1a80d29e9f2650b884e85",
                                "module": "base",
                                "name": "Tracker",
                                "type_arguments": [],
                            }
                        },
                        "Address",
                    ],
                    "return_": [],
                },
            },
        }
    }


@pytest.fixture
def paysui_result():
    """."""
    return {
        "transaction": {
            "data": {
                "transactions": [
                    {
                        "PaySui": {
                            "coins": [
                                {
                                    "objectId": "0x4b7c4ed369c40a029848d5844c3dfa7cf4604096f383ba1c4428cb682915de93",
                                    "version": 2,
                                    "digest": "3Jgm53JNBhohBr1aWSFKAKF53Wjkwf9s2yA7bfikZd3r",
                                }
                            ],
                            "recipients": ["0xa1d8cdcd7ab4ddbf08c790087757ab2bc0dbb65bdcb7dde1a63eaa77039ef898"],
                            "amounts": [5000000],
                        }
                    }
                ],
                "sender": "0xb1463a5d1e5773c093fc5afb813ab10110821dc650bc9be947eb7ba3f1e9b3c2",
                "gasData": {
                    "payment": {
                        "objectId": "0x4b7c4ed369c40a029848d5844c3dfa7cf4604096f383ba1c4428cb682915de93",
                        "version": 2,
                        "digest": "3Jgm53JNBhohBr1aWSFKAKF53Wjkwf9s2yA7bfikZd3r",
                    },
                    "owner": "0xb1463a5d1e5773c093fc5afb813ab10110821dc650bc9be947eb7ba3f1e9b3c2",
                    "price": 1,
                    "budget": 300,
                },
            },
            "txSignatures": [
                "AFsjG1AX2syyEF3J/wL/eONEAwb6QSE5r3Bt7x3IbKUp0xQqhRZOWhbZmCISaHbnF7fYdspgtkt3rjCSJWUmEgk8nFmyR8rkLaiOUivTRP3mYzdgMwjH+pAEbQdPn5Zu1w=="
            ],
        },
        "effects": {
            "status": {"status": "success"},
            "executedEpoch": 1,
            "gasUsed": {"computationCost": 157, "storageCost": 63, "storageRebate": 42},
            "transactionDigest": "87GGrFwZo8G4p129bT1XPNgUsvFRcWnW8z9zBQhY9fs9",
            "created": [
                {
                    "owner": {"AddressOwner": "0xa1d8cdcd7ab4ddbf08c790087757ab2bc0dbb65bdcb7dde1a63eaa77039ef898"},
                    "reference": {
                        "objectId": "0x9299cb7bcb44f0effd37371699783b799af1168432580ad337e017d72102bd11",
                        "version": 3,
                        "digest": "Czrw28uZxXAK41VjmR9y3iLi47y5AcNFktEhTJ3GTaQ4",
                    },
                }
            ],
            "mutated": [
                {
                    "owner": {"AddressOwner": "0xb1463a5d1e5773c093fc5afb813ab10110821dc650bc9be947eb7ba3f1e9b3c2"},
                    "reference": {
                        "objectId": "0x4b7c4ed369c40a029848d5844c3dfa7cf4604096f383ba1c4428cb682915de93",
                        "version": 3,
                        "digest": "3ni5jmHSeQS8VogpWsWjXUD2kHgwUwqFNmG7iCkisHtB",
                    },
                }
            ],
            "gasObject": {
                "owner": {"AddressOwner": "0xb1463a5d1e5773c093fc5afb813ab10110821dc650bc9be947eb7ba3f1e9b3c2"},
                "reference": {
                    "objectId": "0x4b7c4ed369c40a029848d5844c3dfa7cf4604096f383ba1c4428cb682915de93",
                    "version": 3,
                    "digest": "3ni5jmHSeQS8VogpWsWjXUD2kHgwUwqFNmG7iCkisHtB",
                },
            },
            "eventsDigest": "2G2Bs49NMmkUh8X4p5zfJxxJagMwZA7K328DSGzHAy76",
            "dependencies": ["HSbMb9f2GXVgzgKbbTYhT9sWRFkvqfKHHTpU9xFXfesa"],
        },
        "events": [
            {
                "coinBalanceChange": {
                    "packageId": "0x0000000000000000000000000000000000000000000000000000000000000002",
                    "transactionModule": "gas",
                    "sender": "0xb1463a5d1e5773c093fc5afb813ab10110821dc650bc9be947eb7ba3f1e9b3c2",
                    "changeType": "Gas",
                    "owner": {"AddressOwner": "0xb1463a5d1e5773c093fc5afb813ab10110821dc650bc9be947eb7ba3f1e9b3c2"},
                    "coinType": "0x2::sui::SUI",
                    "coinObjectId": "0x4b7c4ed369c40a029848d5844c3dfa7cf4604096f383ba1c4428cb682915de93",
                    "version": 2,
                    "amount": -178,
                }
            },
            {
                "coinBalanceChange": {
                    "packageId": "0x0000000000000000000000000000000000000000000000000000000000000002",
                    "transactionModule": "pay_sui",
                    "sender": "0xb1463a5d1e5773c093fc5afb813ab10110821dc650bc9be947eb7ba3f1e9b3c2",
                    "changeType": "Pay",
                    "owner": {"AddressOwner": "0xb1463a5d1e5773c093fc5afb813ab10110821dc650bc9be947eb7ba3f1e9b3c2"},
                    "coinType": "0x2::sui::SUI",
                    "coinObjectId": "0x4b7c4ed369c40a029848d5844c3dfa7cf4604096f383ba1c4428cb682915de93",
                    "version": 2,
                    "amount": -5000000,
                }
            },
            {
                "coinBalanceChange": {
                    "packageId": "0x0000000000000000000000000000000000000000000000000000000000000002",
                    "transactionModule": "pay_sui",
                    "sender": "0xb1463a5d1e5773c093fc5afb813ab10110821dc650bc9be947eb7ba3f1e9b3c2",
                    "changeType": "Receive",
                    "owner": {"AddressOwner": "0xa1d8cdcd7ab4ddbf08c790087757ab2bc0dbb65bdcb7dde1a63eaa77039ef898"},
                    "coinType": "0x2::sui::SUI",
                    "coinObjectId": "0x9299cb7bcb44f0effd37371699783b799af1168432580ad337e017d72102bd11",
                    "version": 3,
                    "amount": 5000000,
                }
            },
        ],
        "confirmedLocalExecution": True,
        "checkpoint": None,
    }


@pytest.fixture
def package_nest_result():
    """Return a normalized package content."""
    return {
        "lest": {
            "file_format_version": 6,
            "address": "0x25c82dbf8cf2fbe47a6d4a80ad4a861760e2dd13",
            "name": "lest",
            "friends": [],
            "structs": {},
            "exposed_functions": {},
        },
        "nest": {
            "file_format_version": 6,
            "address": "0x25c82dbf8cf2fbe47a6d4a80ad4a861760e2dd13",
            "name": "nest",
            "friends": [],
            "structs": {
                "Child0": {
                    "abilities": {"abilities": ["Store", "Key"]},
                    "type_parameters": [],
                    "fields": [
                        {
                            "name": "id",
                            "type_": {
                                "Struct": {"address": "0x2", "module": "object", "name": "UID", "type_arguments": []}
                            },
                        },
                        {"name": "val", "type_": "U64"},
                    ],
                },
                "Child1": {
                    "abilities": {"abilities": ["Store", "Key"]},
                    "type_parameters": [],
                    "fields": [
                        {
                            "name": "id",
                            "type_": {
                                "Struct": {"address": "0x2", "module": "object", "name": "UID", "type_arguments": []}
                            },
                        },
                        {"name": "val", "type_": "U64"},
                    ],
                },
                "Parent0": {
                    "abilities": {"abilities": ["Key"]},
                    "type_parameters": [],
                    "fields": [
                        {
                            "name": "id",
                            "type_": {
                                "Struct": {"address": "0x2", "module": "object", "name": "UID", "type_arguments": []}
                            },
                        },
                        {
                            "name": "child",
                            "type_": {
                                "Struct": {
                                    "address": "0x25c82dbf8cf2fbe47a6d4a80ad4a861760e2dd13",
                                    "module": "nest",
                                    "name": "Child0",
                                    "type_arguments": [],
                                }
                            },
                        },
                    ],
                },
                "Parent1": {
                    "abilities": {"abilities": ["Key"]},
                    "type_parameters": [],
                    "fields": [
                        {
                            "name": "id",
                            "type_": {
                                "Struct": {"address": "0x2", "module": "object", "name": "UID", "type_arguments": []}
                            },
                        },
                        {
                            "name": "child",
                            "type_": {
                                "Struct": {
                                    "address": "0x1",
                                    "module": "option",
                                    "name": "Option",
                                    "type_arguments": [
                                        {
                                            "Struct": {
                                                "address": "0x25c82dbf8cf2fbe47a6d4a80ad4a861760e2dd13",
                                                "module": "nest",
                                                "name": "Child1",
                                                "type_arguments": [],
                                            }
                                        }
                                    ],
                                }
                            },
                        },
                    ],
                },
            },
            "exposed_functions": {
                "create_data": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": [],
                }
            },
        },
    }


@pytest.fixture
def package_sui_result():
    """Return a normalized package content."""
    return {
        "bag": {
            "name": "bag",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [],
            "structs": {
                "Bag": {
                    "abilities": {"abilities": ["Store", "Key"]},
                    "fields": [
                        {
                            "name": "id",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object",
                                    "name": "UID",
                                    "type_arguments": [],
                                }
                            },
                        },
                        {"name": "size", "type_": "U64"},
                    ],
                    "type_parameters": [],
                }
            },
            "exposed_functions": {
                "add": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store"]}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {"address": "0x2", "module": "bag", "name": "Bag", "type_arguments": []}
                            }
                        },
                        {"TypeParameter": 0},
                        {"TypeParameter": 1},
                    ],
                    "return_": [],
                },
                "borrow": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store"]}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {"address": "0x2", "module": "bag", "name": "Bag", "type_arguments": []}
                            }
                        },
                        {"TypeParameter": 0},
                    ],
                    "return_": [{"Reference": {"TypeParameter": 1}}],
                },
                "borrow_mut": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store"]}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {"address": "0x2", "module": "bag", "name": "Bag", "type_arguments": []}
                            }
                        },
                        {"TypeParameter": 0},
                    ],
                    "return_": [{"MutableReference": {"TypeParameter": 1}}],
                },
                "contains_with_type": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store"]}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {"address": "0x2", "module": "bag", "name": "Bag", "type_arguments": []}
                            }
                        },
                        {"TypeParameter": 0},
                    ],
                    "return_": ["Bool"],
                },
                "destroy_empty": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {"Struct": {"address": "0x2", "module": "bag", "name": "Bag", "type_arguments": []}}
                    ],
                    "return_": [],
                },
                "is_empty": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {"address": "0x2", "module": "bag", "name": "Bag", "type_arguments": []}
                            }
                        }
                    ],
                    "return_": ["Bool"],
                },
                "length": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {"address": "0x2", "module": "bag", "name": "Bag", "type_arguments": []}
                            }
                        }
                    ],
                    "return_": ["U64"],
                },
                "new": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": [{"Struct": {"address": "0x2", "module": "bag", "name": "Bag", "type_arguments": []}}],
                },
                "remove": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store"]}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {"address": "0x2", "module": "bag", "name": "Bag", "type_arguments": []}
                            }
                        },
                        {"TypeParameter": 0},
                    ],
                    "return_": [{"TypeParameter": 1}],
                },
            },
        },
        "balance": {
            "name": "balance",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [],
            "structs": {
                "Balance": {
                    "abilities": {"abilities": ["Store"]},
                    "fields": [{"name": "value", "type_": "U64"}],
                    "type_parameters": [{"constraints": {"abilities": []}, "is_phantom": True}],
                },
                "Supply": {
                    "abilities": {"abilities": ["Store"]},
                    "fields": [{"name": "value", "type_": "U64"}],
                    "type_parameters": [{"constraints": {"abilities": []}, "is_phantom": True}],
                },
            },
            "exposed_functions": {
                "create_supply": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Drop"]}],
                    "parameters": [{"TypeParameter": 0}],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "balance",
                                "name": "Supply",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        }
                    ],
                },
                "decrease_supply": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "balance",
                                    "name": "Supply",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "balance",
                                "name": "Balance",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        },
                    ],
                    "return_": ["U64"],
                },
                "destroy_zero": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "balance",
                                "name": "Balance",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        }
                    ],
                    "return_": [],
                },
                "increase_supply": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "balance",
                                    "name": "Supply",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        "U64",
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "balance",
                                "name": "Balance",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        }
                    ],
                },
                "join": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "balance",
                                    "name": "Balance",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "balance",
                                "name": "Balance",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        },
                    ],
                    "return_": ["U64"],
                },
                "split": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "balance",
                                    "name": "Balance",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        "U64",
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "balance",
                                "name": "Balance",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        }
                    ],
                },
                "supply_value": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "balance",
                                    "name": "Supply",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        }
                    ],
                    "return_": ["U64"],
                },
                "value": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "balance",
                                    "name": "Balance",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        }
                    ],
                    "return_": ["U64"],
                },
                "zero": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "balance",
                                "name": "Balance",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        }
                    ],
                },
            },
        },
        "bcs": {
            "name": "bcs",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [],
            "structs": {
                "BCS": {
                    "abilities": {"abilities": ["Copy", "Drop", "Store"]},
                    "fields": [{"name": "bytes", "type_": {"Vector": "U8"}}],
                    "type_parameters": [],
                }
            },
            "exposed_functions": {
                "into_remainder_bytes": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {"Struct": {"address": "0x2", "module": "bcs", "name": "BCS", "type_arguments": []}}
                    ],
                    "return_": [{"Vector": "U8"}],
                },
                "new": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [{"Vector": "U8"}],
                    "return_": [{"Struct": {"address": "0x2", "module": "bcs", "name": "BCS", "type_arguments": []}}],
                },
                "peel_address": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {"address": "0x2", "module": "bcs", "name": "BCS", "type_arguments": []}
                            }
                        }
                    ],
                    "return_": ["Address"],
                },
                "peel_bool": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {"address": "0x2", "module": "bcs", "name": "BCS", "type_arguments": []}
                            }
                        }
                    ],
                    "return_": ["Bool"],
                },
                "peel_option_address": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {"address": "0x2", "module": "bcs", "name": "BCS", "type_arguments": []}
                            }
                        }
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x1",
                                "module": "option",
                                "name": "Option",
                                "type_arguments": ["Address"],
                            }
                        }
                    ],
                },
                "peel_option_bool": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {"address": "0x2", "module": "bcs", "name": "BCS", "type_arguments": []}
                            }
                        }
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x1",
                                "module": "option",
                                "name": "Option",
                                "type_arguments": ["Bool"],
                            }
                        }
                    ],
                },
                "peel_option_u128": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {"address": "0x2", "module": "bcs", "name": "BCS", "type_arguments": []}
                            }
                        }
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x1",
                                "module": "option",
                                "name": "Option",
                                "type_arguments": ["U128"],
                            }
                        }
                    ],
                },
                "peel_option_u64": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {"address": "0x2", "module": "bcs", "name": "BCS", "type_arguments": []}
                            }
                        }
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x1",
                                "module": "option",
                                "name": "Option",
                                "type_arguments": ["U64"],
                            }
                        }
                    ],
                },
                "peel_option_u8": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {"address": "0x2", "module": "bcs", "name": "BCS", "type_arguments": []}
                            }
                        }
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x1",
                                "module": "option",
                                "name": "Option",
                                "type_arguments": ["U8"],
                            }
                        }
                    ],
                },
                "peel_u128": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {"address": "0x2", "module": "bcs", "name": "BCS", "type_arguments": []}
                            }
                        }
                    ],
                    "return_": ["U128"],
                },
                "peel_u64": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {"address": "0x2", "module": "bcs", "name": "BCS", "type_arguments": []}
                            }
                        }
                    ],
                    "return_": ["U64"],
                },
                "peel_u8": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {"address": "0x2", "module": "bcs", "name": "BCS", "type_arguments": []}
                            }
                        }
                    ],
                    "return_": ["U8"],
                },
                "peel_vec_address": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {"address": "0x2", "module": "bcs", "name": "BCS", "type_arguments": []}
                            }
                        }
                    ],
                    "return_": [{"Vector": "Address"}],
                },
                "peel_vec_bool": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {"address": "0x2", "module": "bcs", "name": "BCS", "type_arguments": []}
                            }
                        }
                    ],
                    "return_": [{"Vector": "Bool"}],
                },
                "peel_vec_length": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {"address": "0x2", "module": "bcs", "name": "BCS", "type_arguments": []}
                            }
                        }
                    ],
                    "return_": ["U64"],
                },
                "peel_vec_u128": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {"address": "0x2", "module": "bcs", "name": "BCS", "type_arguments": []}
                            }
                        }
                    ],
                    "return_": [{"Vector": "U128"}],
                },
                "peel_vec_u64": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {"address": "0x2", "module": "bcs", "name": "BCS", "type_arguments": []}
                            }
                        }
                    ],
                    "return_": [{"Vector": "U64"}],
                },
                "peel_vec_u8": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {"address": "0x2", "module": "bcs", "name": "BCS", "type_arguments": []}
                            }
                        }
                    ],
                    "return_": [{"Vector": "U8"}],
                },
                "peel_vec_vec_u8": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {"address": "0x2", "module": "bcs", "name": "BCS", "type_arguments": []}
                            }
                        }
                    ],
                    "return_": [{"Vector": {"Vector": "U8"}}],
                },
                "to_bytes": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [{"Reference": {"TypeParameter": 0}}],
                    "return_": [{"Vector": "U8"}],
                },
            },
        },
        "bls12381": {
            "name": "bls12381",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [{"address": "0x2", "name": "validator"}],
            "structs": {},
            "exposed_functions": {
                "bls12381_min_pk_verify": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {"Reference": {"Vector": "U8"}},
                        {"Reference": {"Vector": "U8"}},
                        {"Reference": {"Vector": "U8"}},
                    ],
                    "return_": ["Bool"],
                },
                "bls12381_min_sig_verify": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {"Reference": {"Vector": "U8"}},
                        {"Reference": {"Vector": "U8"}},
                        {"Reference": {"Vector": "U8"}},
                    ],
                    "return_": ["Bool"],
                },
                "bls12381_min_sig_verify_with_domain": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {"Reference": {"Vector": "U8"}},
                        {"Reference": {"Vector": "U8"}},
                        {"Vector": "U8"},
                        {"Vector": "U8"},
                    ],
                    "return_": ["Bool"],
                },
            },
        },
        "bulletproofs": {
            "name": "bulletproofs",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [],
            "structs": {},
            "exposed_functions": {
                "verify_full_range_proof": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {"Reference": {"Vector": "U8"}},
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "elliptic_curve",
                                    "name": "RistrettoPoint",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "U64",
                    ],
                    "return_": [],
                }
            },
        },
        "coin": {
            "name": "coin",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [],
            "structs": {
                "Coin": {
                    "abilities": {"abilities": ["Store", "Key"]},
                    "fields": [
                        {
                            "name": "id",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object",
                                    "name": "UID",
                                    "type_arguments": [],
                                }
                            },
                        },
                        {
                            "name": "balance",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "balance",
                                    "name": "Balance",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            },
                        },
                    ],
                    "type_parameters": [{"constraints": {"abilities": []}, "is_phantom": True}],
                },
                "CurrencyCreated": {
                    "abilities": {"abilities": ["Copy", "Drop"]},
                    "fields": [{"name": "decimals", "type_": "U8"}],
                    "type_parameters": [{"constraints": {"abilities": []}, "is_phantom": True}],
                },
                "TreasuryCap": {
                    "abilities": {"abilities": ["Store", "Key"]},
                    "fields": [
                        {
                            "name": "id",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object",
                                    "name": "UID",
                                    "type_arguments": [],
                                }
                            },
                        },
                        {
                            "name": "total_supply",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "balance",
                                    "name": "Supply",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            },
                        },
                    ],
                    "type_parameters": [{"constraints": {"abilities": []}, "is_phantom": True}],
                },
            },
            "exposed_functions": {
                "balance": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "coin",
                                    "name": "Coin",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        }
                    ],
                    "return_": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "balance",
                                    "name": "Balance",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        }
                    ],
                },
                "balance_mut": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "coin",
                                    "name": "Coin",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        }
                    ],
                    "return_": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "balance",
                                    "name": "Balance",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        }
                    ],
                },
                "burn": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "coin",
                                    "name": "TreasuryCap",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "coin",
                                "name": "Coin",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        },
                    ],
                    "return_": ["U64"],
                },
                "burn_": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "coin",
                                    "name": "TreasuryCap",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "coin",
                                "name": "Coin",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        },
                    ],
                    "return_": [],
                },
                "create_currency": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Drop"]}],
                    "parameters": [
                        {"TypeParameter": 0},
                        "U8",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "coin",
                                "name": "TreasuryCap",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        }
                    ],
                },
                "destroy_zero": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "coin",
                                "name": "Coin",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        }
                    ],
                    "return_": [],
                },
                "divide_into_n": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "coin",
                                    "name": "Coin",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        "U64",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [
                        {
                            "Vector": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "coin",
                                    "name": "Coin",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        }
                    ],
                },
                "from_balance": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "balance",
                                "name": "Balance",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "coin",
                                "name": "Coin",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        }
                    ],
                },
                "into_balance": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "coin",
                                "name": "Coin",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        }
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "balance",
                                "name": "Balance",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        }
                    ],
                },
                "join": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "coin",
                                    "name": "Coin",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "coin",
                                "name": "Coin",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        },
                    ],
                    "return_": [],
                },
                "mint": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "coin",
                                    "name": "TreasuryCap",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        "U64",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "coin",
                                "name": "Coin",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        }
                    ],
                },
                "mint_and_transfer": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "coin",
                                    "name": "TreasuryCap",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        "U64",
                        "Address",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "mint_balance": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "coin",
                                    "name": "TreasuryCap",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        "U64",
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "balance",
                                "name": "Balance",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        }
                    ],
                },
                "put": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "balance",
                                    "name": "Balance",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "coin",
                                "name": "Coin",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        },
                    ],
                    "return_": [],
                },
                "split": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "coin",
                                    "name": "Coin",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        "U64",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "coin",
                                "name": "Coin",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        }
                    ],
                },
                "supply": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "coin",
                                    "name": "TreasuryCap",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        }
                    ],
                    "return_": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "balance",
                                    "name": "Supply",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        }
                    ],
                },
                "supply_mut": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "coin",
                                    "name": "TreasuryCap",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        }
                    ],
                    "return_": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "balance",
                                    "name": "Supply",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        }
                    ],
                },
                "take": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "balance",
                                    "name": "Balance",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        "U64",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "coin",
                                "name": "Coin",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        }
                    ],
                },
                "total_supply": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "coin",
                                    "name": "TreasuryCap",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        }
                    ],
                    "return_": ["U64"],
                },
                "treasury_into_supply": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "coin",
                                "name": "TreasuryCap",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        }
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "balance",
                                "name": "Supply",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        }
                    ],
                },
                "value": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "coin",
                                    "name": "Coin",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        }
                    ],
                    "return_": ["U64"],
                },
                "zero": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "coin",
                                "name": "Coin",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        }
                    ],
                },
            },
        },
        "devnet_nft": {
            "name": "devnet_nft",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [],
            "structs": {
                "DevNetNFT": {
                    "abilities": {"abilities": ["Store", "Key"]},
                    "fields": [
                        {
                            "name": "id",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object",
                                    "name": "UID",
                                    "type_arguments": [],
                                }
                            },
                        },
                        {
                            "name": "name",
                            "type_": {
                                "Struct": {
                                    "address": "0x1",
                                    "module": "string",
                                    "name": "String",
                                    "type_arguments": [],
                                }
                            },
                        },
                        {
                            "name": "description",
                            "type_": {
                                "Struct": {
                                    "address": "0x1",
                                    "module": "string",
                                    "name": "String",
                                    "type_arguments": [],
                                }
                            },
                        },
                        {
                            "name": "url",
                            "type_": {
                                "Struct": {"address": "0x2", "module": "url", "name": "Url", "type_arguments": []}
                            },
                        },
                    ],
                    "type_parameters": [],
                },
                "MintNFTEvent": {
                    "abilities": {"abilities": ["Copy", "Drop"]},
                    "fields": [
                        {
                            "name": "object_id",
                            "type_": {
                                "Struct": {"address": "0x2", "module": "object", "name": "ID", "type_arguments": []}
                            },
                        },
                        {"name": "creator", "type_": "Address"},
                        {
                            "name": "name",
                            "type_": {
                                "Struct": {
                                    "address": "0x1",
                                    "module": "string",
                                    "name": "String",
                                    "type_arguments": [],
                                }
                            },
                        },
                    ],
                    "type_parameters": [],
                },
            },
            "exposed_functions": {
                "burn": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "devnet_nft",
                                "name": "DevNetNFT",
                                "type_arguments": [],
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "description": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "devnet_nft",
                                    "name": "DevNetNFT",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x1",
                                    "module": "string",
                                    "name": "String",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                },
                "mint": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [],
                    "parameters": [
                        {"Vector": "U8"},
                        {"Vector": "U8"},
                        {"Vector": "U8"},
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "name": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "devnet_nft",
                                    "name": "DevNetNFT",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x1",
                                    "module": "string",
                                    "name": "String",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                },
                "update_description": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "devnet_nft",
                                    "name": "DevNetNFT",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {"Vector": "U8"},
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "url": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "devnet_nft",
                                    "name": "DevNetNFT",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": [
                        {
                            "Reference": {
                                "Struct": {"address": "0x2", "module": "url", "name": "Url", "type_arguments": []}
                            }
                        }
                    ],
                },
            },
        },
        "digest": {
            "name": "digest",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [],
            "structs": {
                "Sha3256Digest": {
                    "abilities": {"abilities": ["Copy", "Drop", "Store"]},
                    "fields": [{"name": "digest", "type_": {"Vector": "U8"}}],
                    "type_parameters": [],
                }
            },
            "exposed_functions": {
                "sha3_256_digest_from_bytes": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [{"Vector": "U8"}],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "digest",
                                "name": "Sha3256Digest",
                                "type_arguments": [],
                            }
                        }
                    ],
                },
                "sha3_256_digest_to_bytes": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "digest",
                                    "name": "Sha3256Digest",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": [{"Vector": "U8"}],
                },
            },
        },
        "dynamic_field": {
            "name": "dynamic_field",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [{"address": "0x2", "name": "dynamic_object_field"}],
            "structs": {
                "Field": {
                    "abilities": {"abilities": ["Key"]},
                    "fields": [
                        {
                            "name": "id",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object",
                                    "name": "UID",
                                    "type_arguments": [],
                                }
                            },
                        },
                        {"name": "name", "type_": {"TypeParameter": 0}},
                        {
                            "name": "value",
                            "type_": {
                                "Struct": {
                                    "address": "0x1",
                                    "module": "option",
                                    "name": "Option",
                                    "type_arguments": [{"TypeParameter": 1}],
                                }
                            },
                        },
                    ],
                    "type_parameters": [
                        {"constraints": {"abilities": ["Copy", "Drop", "Store"]}, "is_phantom": False},
                        {"constraints": {"abilities": ["Store"]}, "is_phantom": False},
                    ],
                }
            },
            "exposed_functions": {
                "add": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store"]}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object",
                                    "name": "UID",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {"TypeParameter": 0},
                        {"TypeParameter": 1},
                    ],
                    "return_": [],
                },
                "add_child_object": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Key"]}],
                    "parameters": ["Address", {"TypeParameter": 0}],
                    "return_": [],
                },
                "borrow": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store"]}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object",
                                    "name": "UID",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {"TypeParameter": 0},
                    ],
                    "return_": [{"Reference": {"TypeParameter": 1}}],
                },
                "borrow_child_object": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Key"]}],
                    "parameters": ["Address", "Address"],
                    "return_": [{"MutableReference": {"TypeParameter": 0}}],
                },
                "borrow_mut": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store"]}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object",
                                    "name": "UID",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {"TypeParameter": 0},
                    ],
                    "return_": [{"MutableReference": {"TypeParameter": 1}}],
                },
                "exists_with_type": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store"]}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object",
                                    "name": "UID",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {"TypeParameter": 0},
                    ],
                    "return_": ["Bool"],
                },
                "field_ids": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object",
                                    "name": "UID",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {"TypeParameter": 0},
                    ],
                    "return_": ["Address", "Address"],
                },
                "has_child_object": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": ["Address", "Address"],
                    "return_": ["Bool"],
                },
                "has_child_object_with_ty": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Key"]}],
                    "parameters": ["Address", "Address"],
                    "return_": ["Bool"],
                },
                "hash_type_and_key": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}],
                    "parameters": ["Address", {"TypeParameter": 0}],
                    "return_": ["Address"],
                },
                "remove": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store"]}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object",
                                    "name": "UID",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {"TypeParameter": 0},
                    ],
                    "return_": [{"TypeParameter": 1}],
                },
                "remove_child_object": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Key"]}],
                    "parameters": ["Address", "Address"],
                    "return_": [{"TypeParameter": 0}],
                },
            },
        },
        "dynamic_object_field": {
            "name": "dynamic_object_field",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [],
            "structs": {
                "Wrapper": {
                    "abilities": {"abilities": ["Copy", "Drop", "Store"]},
                    "fields": [{"name": "name", "type_": {"TypeParameter": 0}}],
                    "type_parameters": [{"constraints": {"abilities": []}, "is_phantom": False}],
                }
            },
            "exposed_functions": {
                "add": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store", "Key"]}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object",
                                    "name": "UID",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {"TypeParameter": 0},
                        {"TypeParameter": 1},
                    ],
                    "return_": [],
                },
                "borrow": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store", "Key"]}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object",
                                    "name": "UID",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {"TypeParameter": 0},
                    ],
                    "return_": [{"Reference": {"TypeParameter": 1}}],
                },
                "borrow_mut": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store", "Key"]}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object",
                                    "name": "UID",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {"TypeParameter": 0},
                    ],
                    "return_": [{"MutableReference": {"TypeParameter": 1}}],
                },
                "exists_": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object",
                                    "name": "UID",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {"TypeParameter": 0},
                    ],
                    "return_": ["Bool"],
                },
                "exists_with_type": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store", "Key"]}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object",
                                    "name": "UID",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {"TypeParameter": 0},
                    ],
                    "return_": ["Bool"],
                },
                "id": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object",
                                    "name": "UID",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {"TypeParameter": 0},
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x1",
                                "module": "option",
                                "name": "Option",
                                "type_arguments": [
                                    {
                                        "Struct": {
                                            "address": "0x2",
                                            "module": "object",
                                            "name": "ID",
                                            "type_arguments": [],
                                        }
                                    }
                                ],
                            }
                        }
                    ],
                },
                "remove": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store", "Key"]}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object",
                                    "name": "UID",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {"TypeParameter": 0},
                    ],
                    "return_": [{"TypeParameter": 1}],
                },
            },
        },
        "ecdsa": {
            "name": "ecdsa",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [],
            "structs": {},
            "exposed_functions": {
                "decompress_pubkey": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [{"Reference": {"Vector": "U8"}}],
                    "return_": [{"Vector": "U8"}],
                },
                "ecrecover": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [{"Reference": {"Vector": "U8"}}, {"Reference": {"Vector": "U8"}}],
                    "return_": [{"Vector": "U8"}],
                },
                "keccak256": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [{"Reference": {"Vector": "U8"}}],
                    "return_": [{"Vector": "U8"}],
                },
                "secp256k1_verify": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {"Reference": {"Vector": "U8"}},
                        {"Reference": {"Vector": "U8"}},
                        {"Reference": {"Vector": "U8"}},
                    ],
                    "return_": ["Bool"],
                },
            },
        },
        "ed25519": {
            "name": "ed25519",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [{"address": "0x2", "name": "validator"}],
            "structs": {},
            "exposed_functions": {
                "ed25519_verify": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {"Reference": {"Vector": "U8"}},
                        {"Reference": {"Vector": "U8"}},
                        {"Reference": {"Vector": "U8"}},
                    ],
                    "return_": ["Bool"],
                },
                "ed25519_verify_with_domain": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {"Reference": {"Vector": "U8"}},
                        {"Reference": {"Vector": "U8"}},
                        {"Vector": "U8"},
                        {"Vector": "U8"},
                    ],
                    "return_": ["Bool"],
                },
            },
        },
        "elliptic_curve": {
            "name": "elliptic_curve",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [],
            "structs": {
                "RistrettoPoint": {
                    "abilities": {"abilities": ["Copy", "Drop", "Store"]},
                    "fields": [{"name": "value", "type_": {"Vector": "U8"}}],
                    "type_parameters": [],
                },
                "Scalar": {
                    "abilities": {"abilities": ["Copy", "Drop", "Store"]},
                    "fields": [{"name": "value", "type_": {"Vector": "U8"}}],
                    "type_parameters": [],
                },
            },
            "exposed_functions": {
                "add": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "elliptic_curve",
                                    "name": "RistrettoPoint",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "elliptic_curve",
                                    "name": "RistrettoPoint",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "elliptic_curve",
                                "name": "RistrettoPoint",
                                "type_arguments": [],
                            }
                        }
                    ],
                },
                "bytes": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "elliptic_curve",
                                    "name": "RistrettoPoint",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": [{"Vector": "U8"}],
                },
                "create_pedersen_commitment": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "elliptic_curve",
                                "name": "Scalar",
                                "type_arguments": [],
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "elliptic_curve",
                                "name": "Scalar",
                                "type_arguments": [],
                            }
                        },
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "elliptic_curve",
                                "name": "RistrettoPoint",
                                "type_arguments": [],
                            }
                        }
                    ],
                },
                "new_from_bytes": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [{"Vector": "U8"}],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "elliptic_curve",
                                "name": "RistrettoPoint",
                                "type_arguments": [],
                            }
                        }
                    ],
                },
                "new_scalar_from_bytes": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [{"Vector": "U8"}],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "elliptic_curve",
                                "name": "Scalar",
                                "type_arguments": [],
                            }
                        }
                    ],
                },
                "new_scalar_from_u64": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": ["U64"],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "elliptic_curve",
                                "name": "Scalar",
                                "type_arguments": [],
                            }
                        }
                    ],
                },
                "scalar_bytes": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "elliptic_curve",
                                    "name": "Scalar",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": [{"Vector": "U8"}],
                },
                "subtract": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "elliptic_curve",
                                    "name": "RistrettoPoint",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "elliptic_curve",
                                    "name": "RistrettoPoint",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "elliptic_curve",
                                "name": "RistrettoPoint",
                                "type_arguments": [],
                            }
                        }
                    ],
                },
            },
        },
        "epoch_time_lock": {
            "name": "epoch_time_lock",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [],
            "structs": {
                "EpochTimeLock": {
                    "abilities": {"abilities": ["Copy", "Store"]},
                    "fields": [{"name": "epoch", "type_": "U64"}],
                    "type_parameters": [],
                }
            },
            "exposed_functions": {
                "destroy": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "epoch_time_lock",
                                "name": "EpochTimeLock",
                                "type_arguments": [],
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "epoch": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "epoch_time_lock",
                                    "name": "EpochTimeLock",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": ["U64"],
                },
                "new": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        "U64",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "epoch_time_lock",
                                "name": "EpochTimeLock",
                                "type_arguments": [],
                            }
                        }
                    ],
                },
            },
        },
        "erc721_metadata": {
            "name": "erc721_metadata",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [],
            "structs": {
                "ERC721Metadata": {
                    "abilities": {"abilities": ["Store"]},
                    "fields": [
                        {
                            "name": "token_id",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "erc721_metadata",
                                    "name": "TokenID",
                                    "type_arguments": [],
                                }
                            },
                        },
                        {
                            "name": "name",
                            "type_": {
                                "Struct": {
                                    "address": "0x1",
                                    "module": "string",
                                    "name": "String",
                                    "type_arguments": [],
                                }
                            },
                        },
                        {
                            "name": "token_uri",
                            "type_": {
                                "Struct": {"address": "0x2", "module": "url", "name": "Url", "type_arguments": []}
                            },
                        },
                    ],
                    "type_parameters": [],
                },
                "TokenID": {
                    "abilities": {"abilities": ["Copy", "Store"]},
                    "fields": [{"name": "id", "type_": "U64"}],
                    "type_parameters": [],
                },
            },
            "exposed_functions": {
                "name": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "erc721_metadata",
                                    "name": "ERC721Metadata",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x1",
                                    "module": "string",
                                    "name": "String",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                },
                "new": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "erc721_metadata",
                                "name": "TokenID",
                                "type_arguments": [],
                            }
                        },
                        {"Vector": "U8"},
                        {"Vector": "U8"},
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "erc721_metadata",
                                "name": "ERC721Metadata",
                                "type_arguments": [],
                            }
                        }
                    ],
                },
                "new_token_id": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": ["U64"],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "erc721_metadata",
                                "name": "TokenID",
                                "type_arguments": [],
                            }
                        }
                    ],
                },
                "token_id": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "erc721_metadata",
                                    "name": "ERC721Metadata",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "erc721_metadata",
                                    "name": "TokenID",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                },
                "token_uri": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "erc721_metadata",
                                    "name": "ERC721Metadata",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": [
                        {
                            "Reference": {
                                "Struct": {"address": "0x2", "module": "url", "name": "Url", "type_arguments": []}
                            }
                        }
                    ],
                },
            },
        },
        "event": {
            "name": "event",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [],
            "structs": {},
            "exposed_functions": {
                "emit": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop"]}],
                    "parameters": [{"TypeParameter": 0}],
                    "return_": [],
                }
            },
        },
        "genesis": {
            "name": "genesis",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [],
            "structs": {},
            "exposed_functions": {},
        },
        "hmac": {
            "name": "hmac",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [],
            "structs": {},
            "exposed_functions": {
                "hmac_sha3_256": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [{"Reference": {"Vector": "U8"}}, {"Reference": {"Vector": "U8"}}],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "digest",
                                "name": "Sha3256Digest",
                                "type_arguments": [],
                            }
                        }
                    ],
                }
            },
        },
        "immutable_external_resource": {
            "name": "immutable_external_resource",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [],
            "structs": {
                "ImmutableExternalResource": {
                    "abilities": {"abilities": ["Copy", "Drop", "Store"]},
                    "fields": [
                        {
                            "name": "url",
                            "type_": {
                                "Struct": {"address": "0x2", "module": "url", "name": "Url", "type_arguments": []}
                            },
                        },
                        {
                            "name": "digest",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "digest",
                                    "name": "Sha3256Digest",
                                    "type_arguments": [],
                                }
                            },
                        },
                    ],
                    "type_parameters": [],
                }
            },
            "exposed_functions": {
                "digest": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "immutable_external_resource",
                                    "name": "ImmutableExternalResource",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "digest",
                                "name": "Sha3256Digest",
                                "type_arguments": [],
                            }
                        }
                    ],
                },
                "new": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {"Struct": {"address": "0x2", "module": "url", "name": "Url", "type_arguments": []}},
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "digest",
                                "name": "Sha3256Digest",
                                "type_arguments": [],
                            }
                        },
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "immutable_external_resource",
                                "name": "ImmutableExternalResource",
                                "type_arguments": [],
                            }
                        }
                    ],
                },
                "update": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "immutable_external_resource",
                                    "name": "ImmutableExternalResource",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {"Struct": {"address": "0x2", "module": "url", "name": "Url", "type_arguments": []}},
                    ],
                    "return_": [],
                },
                "url": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "immutable_external_resource",
                                    "name": "ImmutableExternalResource",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": [{"Struct": {"address": "0x2", "module": "url", "name": "Url", "type_arguments": []}}],
                },
            },
        },
        "locked_coin": {
            "name": "locked_coin",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [{"address": "0x2", "name": "sui_system"}],
            "structs": {
                "LockedCoin": {
                    "abilities": {"abilities": ["Key"]},
                    "fields": [
                        {
                            "name": "id",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object",
                                    "name": "UID",
                                    "type_arguments": [],
                                }
                            },
                        },
                        {
                            "name": "balance",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "balance",
                                    "name": "Balance",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            },
                        },
                        {
                            "name": "locked_until_epoch",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "epoch_time_lock",
                                    "name": "EpochTimeLock",
                                    "type_arguments": [],
                                }
                            },
                        },
                    ],
                    "type_parameters": [{"constraints": {"abilities": []}, "is_phantom": True}],
                }
            },
            "exposed_functions": {
                "into_balance": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "locked_coin",
                                "name": "LockedCoin",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        }
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "balance",
                                "name": "Balance",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "epoch_time_lock",
                                "name": "EpochTimeLock",
                                "type_arguments": [],
                            }
                        },
                    ],
                },
                "lock_coin": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "coin",
                                "name": "Coin",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        },
                        "Address",
                        "U64",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "new_from_balance": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "balance",
                                "name": "Balance",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "epoch_time_lock",
                                "name": "EpochTimeLock",
                                "type_arguments": [],
                            }
                        },
                        "Address",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "unlock_coin": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "locked_coin",
                                "name": "LockedCoin",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "value": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "locked_coin",
                                    "name": "LockedCoin",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        }
                    ],
                    "return_": ["U64"],
                },
            },
        },
        "math": {
            "name": "math",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [],
            "structs": {},
            "exposed_functions": {
                "max": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": ["U64", "U64"],
                    "return_": ["U64"],
                },
                "min": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": ["U64", "U64"],
                    "return_": ["U64"],
                },
                "pow": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": ["U64", "U8"],
                    "return_": ["U64"],
                },
                "sqrt": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": ["U64"],
                    "return_": ["U64"],
                },
                "sqrt_u128": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": ["U128"],
                    "return_": ["U128"],
                },
            },
        },
        "object": {
            "name": "object",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [
                {"address": "0x2", "name": "dynamic_field"},
                {"address": "0x2", "name": "dynamic_object_field"},
                {"address": "0x2", "name": "sui_system"},
                {"address": "0x2", "name": "transfer"},
            ],
            "structs": {
                "ID": {
                    "abilities": {"abilities": ["Copy", "Drop", "Store"]},
                    "fields": [{"name": "bytes", "type_": "Address"}],
                    "type_parameters": [],
                },
                "UID": {
                    "abilities": {"abilities": ["Store"]},
                    "fields": [
                        {
                            "name": "id",
                            "type_": {
                                "Struct": {"address": "0x2", "module": "object", "name": "ID", "type_arguments": []}
                            },
                        }
                    ],
                    "type_parameters": [],
                },
            },
            "exposed_functions": {
                "address_from_bytes": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [{"Vector": "U8"}],
                    "return_": ["Address"],
                },
                "borrow_id": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Key"]}],
                    "parameters": [{"Reference": {"TypeParameter": 0}}],
                    "return_": [
                        {
                            "Reference": {
                                "Struct": {"address": "0x2", "module": "object", "name": "ID", "type_arguments": []}
                            }
                        }
                    ],
                },
                "delete": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {"Struct": {"address": "0x2", "module": "object", "name": "UID", "type_arguments": []}}
                    ],
                    "return_": [],
                },
                "id": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Key"]}],
                    "parameters": [{"Reference": {"TypeParameter": 0}}],
                    "return_": [{"Struct": {"address": "0x2", "module": "object", "name": "ID", "type_arguments": []}}],
                },
                "id_address": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Key"]}],
                    "parameters": [{"Reference": {"TypeParameter": 0}}],
                    "return_": ["Address"],
                },
                "id_bytes": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Key"]}],
                    "parameters": [{"Reference": {"TypeParameter": 0}}],
                    "return_": [{"Vector": "U8"}],
                },
                "id_from_address": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": ["Address"],
                    "return_": [{"Struct": {"address": "0x2", "module": "object", "name": "ID", "type_arguments": []}}],
                },
                "id_from_bytes": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [{"Vector": "U8"}],
                    "return_": [{"Struct": {"address": "0x2", "module": "object", "name": "ID", "type_arguments": []}}],
                },
                "id_to_address": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {"address": "0x2", "module": "object", "name": "ID", "type_arguments": []}
                            }
                        }
                    ],
                    "return_": ["Address"],
                },
                "id_to_bytes": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {"address": "0x2", "module": "object", "name": "ID", "type_arguments": []}
                            }
                        }
                    ],
                    "return_": [{"Vector": "U8"}],
                },
                "new": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": [
                        {"Struct": {"address": "0x2", "module": "object", "name": "UID", "type_arguments": []}}
                    ],
                },
                "new_uid_from_hash": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": ["Address"],
                    "return_": [
                        {"Struct": {"address": "0x2", "module": "object", "name": "UID", "type_arguments": []}}
                    ],
                },
                "sui_system_state": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [],
                    "return_": [
                        {"Struct": {"address": "0x2", "module": "object", "name": "UID", "type_arguments": []}}
                    ],
                },
                "uid_as_inner": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object",
                                    "name": "UID",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": [
                        {
                            "Reference": {
                                "Struct": {"address": "0x2", "module": "object", "name": "ID", "type_arguments": []}
                            }
                        }
                    ],
                },
                "uid_to_address": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object",
                                    "name": "UID",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": ["Address"],
                },
                "uid_to_bytes": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object",
                                    "name": "UID",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": [{"Vector": "U8"}],
                },
                "uid_to_inner": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object",
                                    "name": "UID",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": [{"Struct": {"address": "0x2", "module": "object", "name": "ID", "type_arguments": []}}],
                },
            },
        },
        "object_bag": {
            "name": "object_bag",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [],
            "structs": {
                "ObjectBag": {
                    "abilities": {"abilities": ["Store", "Key"]},
                    "fields": [
                        {
                            "name": "id",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object",
                                    "name": "UID",
                                    "type_arguments": [],
                                }
                            },
                        },
                        {"name": "size", "type_": "U64"},
                    ],
                    "type_parameters": [],
                }
            },
            "exposed_functions": {
                "add": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store", "Key"]}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object_bag",
                                    "name": "ObjectBag",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {"TypeParameter": 0},
                        {"TypeParameter": 1},
                    ],
                    "return_": [],
                },
                "borrow": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store", "Key"]}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object_bag",
                                    "name": "ObjectBag",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {"TypeParameter": 0},
                    ],
                    "return_": [{"Reference": {"TypeParameter": 1}}],
                },
                "borrow_mut": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store", "Key"]}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object_bag",
                                    "name": "ObjectBag",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {"TypeParameter": 0},
                    ],
                    "return_": [{"MutableReference": {"TypeParameter": 1}}],
                },
                "contains": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object_bag",
                                    "name": "ObjectBag",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {"TypeParameter": 0},
                    ],
                    "return_": ["Bool"],
                },
                "contains_with_type": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store", "Key"]}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object_bag",
                                    "name": "ObjectBag",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {"TypeParameter": 0},
                    ],
                    "return_": ["Bool"],
                },
                "destroy_empty": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "object_bag",
                                "name": "ObjectBag",
                                "type_arguments": [],
                            }
                        }
                    ],
                    "return_": [],
                },
                "is_empty": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object_bag",
                                    "name": "ObjectBag",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": ["Bool"],
                },
                "length": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object_bag",
                                    "name": "ObjectBag",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": ["U64"],
                },
                "new": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "object_bag",
                                "name": "ObjectBag",
                                "type_arguments": [],
                            }
                        }
                    ],
                },
                "remove": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store", "Key"]}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object_bag",
                                    "name": "ObjectBag",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {"TypeParameter": 0},
                    ],
                    "return_": [{"TypeParameter": 1}],
                },
                "value_id": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object_bag",
                                    "name": "ObjectBag",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {"TypeParameter": 0},
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x1",
                                "module": "option",
                                "name": "Option",
                                "type_arguments": [
                                    {
                                        "Struct": {
                                            "address": "0x2",
                                            "module": "object",
                                            "name": "ID",
                                            "type_arguments": [],
                                        }
                                    }
                                ],
                            }
                        }
                    ],
                },
            },
        },
        "object_table": {
            "name": "object_table",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [],
            "structs": {
                "ObjectTable": {
                    "abilities": {"abilities": ["Store", "Key"]},
                    "fields": [
                        {
                            "name": "id",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object",
                                    "name": "UID",
                                    "type_arguments": [],
                                }
                            },
                        },
                        {"name": "size", "type_": "U64"},
                    ],
                    "type_parameters": [
                        {"constraints": {"abilities": ["Copy", "Drop", "Store"]}, "is_phantom": True},
                        {"constraints": {"abilities": ["Store", "Key"]}, "is_phantom": True},
                    ],
                }
            },
            "exposed_functions": {
                "add": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store", "Key"]}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object_table",
                                    "name": "ObjectTable",
                                    "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                                }
                            }
                        },
                        {"TypeParameter": 0},
                        {"TypeParameter": 1},
                    ],
                    "return_": [],
                },
                "borrow": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store", "Key"]}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object_table",
                                    "name": "ObjectTable",
                                    "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                                }
                            }
                        },
                        {"TypeParameter": 0},
                    ],
                    "return_": [{"Reference": {"TypeParameter": 1}}],
                },
                "borrow_mut": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store", "Key"]}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object_table",
                                    "name": "ObjectTable",
                                    "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                                }
                            }
                        },
                        {"TypeParameter": 0},
                    ],
                    "return_": [{"MutableReference": {"TypeParameter": 1}}],
                },
                "contains": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store", "Key"]}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object_table",
                                    "name": "ObjectTable",
                                    "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                                }
                            }
                        },
                        {"TypeParameter": 0},
                    ],
                    "return_": ["Bool"],
                },
                "destroy_empty": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store", "Key"]}],
                    "parameters": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "object_table",
                                "name": "ObjectTable",
                                "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                            }
                        }
                    ],
                    "return_": [],
                },
                "is_empty": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store", "Key"]}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object_table",
                                    "name": "ObjectTable",
                                    "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                                }
                            }
                        }
                    ],
                    "return_": ["Bool"],
                },
                "length": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store", "Key"]}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object_table",
                                    "name": "ObjectTable",
                                    "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                                }
                            }
                        }
                    ],
                    "return_": ["U64"],
                },
                "new": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store", "Key"]}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "object_table",
                                "name": "ObjectTable",
                                "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                            }
                        }
                    ],
                },
                "remove": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store", "Key"]}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object_table",
                                    "name": "ObjectTable",
                                    "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                                }
                            }
                        },
                        {"TypeParameter": 0},
                    ],
                    "return_": [{"TypeParameter": 1}],
                },
                "value_id": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store", "Key"]}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object_table",
                                    "name": "ObjectTable",
                                    "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                                }
                            }
                        },
                        {"TypeParameter": 0},
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x1",
                                "module": "option",
                                "name": "Option",
                                "type_arguments": [
                                    {
                                        "Struct": {
                                            "address": "0x2",
                                            "module": "object",
                                            "name": "ID",
                                            "type_arguments": [],
                                        }
                                    }
                                ],
                            }
                        }
                    ],
                },
            },
        },
        "pay": {
            "name": "pay",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [],
            "structs": {},
            "exposed_functions": {
                "divide_and_keep": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "coin",
                                    "name": "Coin",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        "U64",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "join": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "coin",
                                    "name": "Coin",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "coin",
                                "name": "Coin",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        },
                    ],
                    "return_": [],
                },
                "join_vec": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "coin",
                                    "name": "Coin",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        {
                            "Vector": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "coin",
                                    "name": "Coin",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "join_vec_and_transfer": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "Vector": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "coin",
                                    "name": "Coin",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        "Address",
                    ],
                    "return_": [],
                },
                "keep": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "coin",
                                "name": "Coin",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        },
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "split": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "coin",
                                    "name": "Coin",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        "U64",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "split_and_transfer": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "coin",
                                    "name": "Coin",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        "U64",
                        "Address",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "split_vec": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "coin",
                                    "name": "Coin",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        {"Vector": "U64"},
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
            },
        },
        "priority_queue": {
            "name": "priority_queue",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [],
            "structs": {
                "Entry": {
                    "abilities": {"abilities": ["Drop", "Store"]},
                    "fields": [
                        {"name": "priority", "type_": "U64"},
                        {"name": "value", "type_": {"TypeParameter": 0}},
                    ],
                    "type_parameters": [{"constraints": {"abilities": ["Drop"]}, "is_phantom": False}],
                },
                "PriorityQueue": {
                    "abilities": {"abilities": ["Drop", "Store"]},
                    "fields": [
                        {
                            "name": "entries",
                            "type_": {
                                "Vector": {
                                    "Struct": {
                                        "address": "0x2",
                                        "module": "priority_queue",
                                        "name": "Entry",
                                        "type_arguments": [{"TypeParameter": 0}],
                                    }
                                }
                            },
                        }
                    ],
                    "type_parameters": [{"constraints": {"abilities": ["Drop"]}, "is_phantom": False}],
                },
            },
            "exposed_functions": {
                "create_entries": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Drop"]}],
                    "parameters": [{"Vector": "U64"}, {"Vector": {"TypeParameter": 0}}],
                    "return_": [
                        {
                            "Vector": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "priority_queue",
                                    "name": "Entry",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        }
                    ],
                },
                "insert": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Drop"]}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "priority_queue",
                                    "name": "PriorityQueue",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        "U64",
                        {"TypeParameter": 0},
                    ],
                    "return_": [],
                },
                "new": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Drop"]}],
                    "parameters": [
                        {
                            "Vector": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "priority_queue",
                                    "name": "Entry",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        }
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "priority_queue",
                                "name": "PriorityQueue",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        }
                    ],
                },
                "new_entry": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Drop"]}],
                    "parameters": ["U64", {"TypeParameter": 0}],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "priority_queue",
                                "name": "Entry",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        }
                    ],
                },
                "pop_max": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Drop"]}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "priority_queue",
                                    "name": "PriorityQueue",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        }
                    ],
                    "return_": ["U64", {"TypeParameter": 0}],
                },
            },
        },
        "safe": {
            "name": "safe",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [],
            "structs": {
                "OwnerCapability": {
                    "abilities": {"abilities": ["Store", "Key"]},
                    "fields": [
                        {
                            "name": "id",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object",
                                    "name": "UID",
                                    "type_arguments": [],
                                }
                            },
                        },
                        {
                            "name": "safe_id",
                            "type_": {
                                "Struct": {"address": "0x2", "module": "object", "name": "ID", "type_arguments": []}
                            },
                        },
                    ],
                    "type_parameters": [{"constraints": {"abilities": []}, "is_phantom": True}],
                },
                "Safe": {
                    "abilities": {"abilities": ["Key"]},
                    "fields": [
                        {
                            "name": "id",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object",
                                    "name": "UID",
                                    "type_arguments": [],
                                }
                            },
                        },
                        {
                            "name": "balance",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "balance",
                                    "name": "Balance",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            },
                        },
                        {
                            "name": "allowed_safes",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "vec_set",
                                    "name": "VecSet",
                                    "type_arguments": [
                                        {
                                            "Struct": {
                                                "address": "0x2",
                                                "module": "object",
                                                "name": "ID",
                                                "type_arguments": [],
                                            }
                                        }
                                    ],
                                }
                            },
                        },
                    ],
                    "type_parameters": [{"constraints": {"abilities": []}, "is_phantom": True}],
                },
                "TransferCapability": {
                    "abilities": {"abilities": ["Store", "Key"]},
                    "fields": [
                        {
                            "name": "id",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object",
                                    "name": "UID",
                                    "type_arguments": [],
                                }
                            },
                        },
                        {
                            "name": "safe_id",
                            "type_": {
                                "Struct": {"address": "0x2", "module": "object", "name": "ID", "type_arguments": []}
                            },
                        },
                        {"name": "amount", "type_": "U64"},
                    ],
                    "type_parameters": [{"constraints": {"abilities": []}, "is_phantom": True}],
                },
            },
            "exposed_functions": {
                "balance": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "safe",
                                    "name": "Safe",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        }
                    ],
                    "return_": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "balance",
                                    "name": "Balance",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        }
                    ],
                },
                "create": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "coin",
                                "name": "Coin",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "create_": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "balance",
                                "name": "Balance",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "safe",
                                "name": "OwnerCapability",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        }
                    ],
                },
                "create_empty": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": [],
                },
                "create_transfer_capability": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "safe",
                                    "name": "Safe",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "safe",
                                    "name": "OwnerCapability",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        "U64",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "safe",
                                "name": "TransferCapability",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        }
                    ],
                },
                "debit": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "safe",
                                    "name": "Safe",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "safe",
                                    "name": "TransferCapability",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        "U64",
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "balance",
                                "name": "Balance",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        }
                    ],
                },
                "deposit": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "safe",
                                    "name": "Safe",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "coin",
                                "name": "Coin",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        },
                    ],
                    "return_": [],
                },
                "deposit_": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "safe",
                                    "name": "Safe",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "balance",
                                "name": "Balance",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        },
                    ],
                    "return_": [],
                },
                "revoke_transfer_capability": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "safe",
                                    "name": "Safe",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "safe",
                                    "name": "OwnerCapability",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        {"Struct": {"address": "0x2", "module": "object", "name": "ID", "type_arguments": []}},
                    ],
                    "return_": [],
                },
                "self_revoke_transfer_capability": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "safe",
                                    "name": "Safe",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "safe",
                                    "name": "TransferCapability",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "withdraw": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "safe",
                                    "name": "Safe",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "safe",
                                    "name": "OwnerCapability",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        "U64",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "withdraw_": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "safe",
                                    "name": "Safe",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "safe",
                                    "name": "OwnerCapability",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        "U64",
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "balance",
                                "name": "Balance",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        }
                    ],
                },
            },
        },
        "stake": {
            "name": "stake",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [{"address": "0x2", "name": "sui_system"}, {"address": "0x2", "name": "validator"}],
            "structs": {
                "Stake": {
                    "abilities": {"abilities": ["Key"]},
                    "fields": [
                        {
                            "name": "id",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object",
                                    "name": "UID",
                                    "type_arguments": [],
                                }
                            },
                        },
                        {
                            "name": "balance",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "balance",
                                    "name": "Balance",
                                    "type_arguments": [
                                        {
                                            "Struct": {
                                                "address": "0x2",
                                                "module": "sui",
                                                "name": "SUI",
                                                "type_arguments": [],
                                            }
                                        }
                                    ],
                                }
                            },
                        },
                        {
                            "name": "locked_until_epoch",
                            "type_": {
                                "Struct": {
                                    "address": "0x1",
                                    "module": "option",
                                    "name": "Option",
                                    "type_arguments": [
                                        {
                                            "Struct": {
                                                "address": "0x2",
                                                "module": "epoch_time_lock",
                                                "name": "EpochTimeLock",
                                                "type_arguments": [],
                                            }
                                        }
                                    ],
                                }
                            },
                        },
                    ],
                    "type_parameters": [],
                }
            },
            "exposed_functions": {
                "burn": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [],
                    "parameters": [
                        {"Struct": {"address": "0x2", "module": "stake", "name": "Stake", "type_arguments": []}},
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "create": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "balance",
                                "name": "Balance",
                                "type_arguments": [
                                    {
                                        "Struct": {
                                            "address": "0x2",
                                            "module": "sui",
                                            "name": "SUI",
                                            "type_arguments": [],
                                        }
                                    }
                                ],
                            }
                        },
                        "Address",
                        {
                            "Struct": {
                                "address": "0x1",
                                "module": "option",
                                "name": "Option",
                                "type_arguments": [
                                    {
                                        "Struct": {
                                            "address": "0x2",
                                            "module": "epoch_time_lock",
                                            "name": "EpochTimeLock",
                                            "type_arguments": [],
                                        }
                                    }
                                ],
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "value": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "stake",
                                    "name": "Stake",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": ["U64"],
                },
                "withdraw_stake": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "stake",
                                    "name": "Stake",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "U64",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
            },
        },
        "staking_pool": {
            "name": "staking_pool",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [{"address": "0x2", "name": "validator"}, {"address": "0x2", "name": "validator_set"}],
            "structs": {
                "Delegation": {
                    "abilities": {"abilities": ["Key"]},
                    "fields": [
                        {
                            "name": "id",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object",
                                    "name": "UID",
                                    "type_arguments": [],
                                }
                            },
                        },
                        {"name": "validator_address", "type_": "Address"},
                        {"name": "pool_starting_epoch", "type_": "U64"},
                        {
                            "name": "pool_tokens",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "balance",
                                    "name": "Balance",
                                    "type_arguments": [
                                        {
                                            "Struct": {
                                                "address": "0x2",
                                                "module": "staking_pool",
                                                "name": "DelegationToken",
                                                "type_arguments": [],
                                            }
                                        }
                                    ],
                                }
                            },
                        },
                        {"name": "principal_sui_amount", "type_": "U64"},
                    ],
                    "type_parameters": [],
                },
                "DelegationToken": {
                    "abilities": {"abilities": ["Drop"]},
                    "fields": [{"name": "dummy_field", "type_": "Bool"}],
                    "type_parameters": [],
                },
                "InactiveStakingPool": {
                    "abilities": {"abilities": ["Key"]},
                    "fields": [
                        {
                            "name": "id",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object",
                                    "name": "UID",
                                    "type_arguments": [],
                                }
                            },
                        },
                        {
                            "name": "pool",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "staking_pool",
                                    "name": "StakingPool",
                                    "type_arguments": [],
                                }
                            },
                        },
                    ],
                    "type_parameters": [],
                },
                "PendingDelegationEntry": {
                    "abilities": {"abilities": ["Drop", "Store"]},
                    "fields": [{"name": "delegator", "type_": "Address"}, {"name": "sui_amount", "type_": "U64"}],
                    "type_parameters": [],
                },
                "StakedSui": {
                    "abilities": {"abilities": ["Key"]},
                    "fields": [
                        {
                            "name": "id",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object",
                                    "name": "UID",
                                    "type_arguments": [],
                                }
                            },
                        },
                        {
                            "name": "principal",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "balance",
                                    "name": "Balance",
                                    "type_arguments": [
                                        {
                                            "Struct": {
                                                "address": "0x2",
                                                "module": "sui",
                                                "name": "SUI",
                                                "type_arguments": [],
                                            }
                                        }
                                    ],
                                }
                            },
                        },
                        {
                            "name": "sui_token_lock",
                            "type_": {
                                "Struct": {
                                    "address": "0x1",
                                    "module": "option",
                                    "name": "Option",
                                    "type_arguments": [
                                        {
                                            "Struct": {
                                                "address": "0x2",
                                                "module": "epoch_time_lock",
                                                "name": "EpochTimeLock",
                                                "type_arguments": [],
                                            }
                                        }
                                    ],
                                }
                            },
                        },
                    ],
                    "type_parameters": [],
                },
                "StakingPool": {
                    "abilities": {"abilities": ["Store"]},
                    "fields": [
                        {"name": "validator_address", "type_": "Address"},
                        {"name": "starting_epoch", "type_": "U64"},
                        {"name": "epoch_starting_sui_balance", "type_": "U64"},
                        {"name": "epoch_starting_delegation_token_supply", "type_": "U64"},
                        {"name": "sui_balance", "type_": "U64"},
                        {
                            "name": "rewards_pool",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "balance",
                                    "name": "Balance",
                                    "type_arguments": [
                                        {
                                            "Struct": {
                                                "address": "0x2",
                                                "module": "sui",
                                                "name": "SUI",
                                                "type_arguments": [],
                                            }
                                        }
                                    ],
                                }
                            },
                        },
                        {
                            "name": "delegation_token_supply",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "balance",
                                    "name": "Supply",
                                    "type_arguments": [
                                        {
                                            "Struct": {
                                                "address": "0x2",
                                                "module": "staking_pool",
                                                "name": "DelegationToken",
                                                "type_arguments": [],
                                            }
                                        }
                                    ],
                                }
                            },
                        },
                        {
                            "name": "pending_delegations",
                            "type_": {
                                "Vector": {
                                    "Struct": {
                                        "address": "0x2",
                                        "module": "staking_pool",
                                        "name": "PendingDelegationEntry",
                                        "type_arguments": [],
                                    }
                                }
                            },
                        },
                    ],
                    "type_parameters": [],
                },
            },
            "exposed_functions": {
                "advance_epoch": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "staking_pool",
                                    "name": "StakingPool",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "balance",
                                "name": "Balance",
                                "type_arguments": [
                                    {
                                        "Struct": {
                                            "address": "0x2",
                                            "module": "sui",
                                            "name": "SUI",
                                            "type_arguments": [],
                                        }
                                    }
                                ],
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "deactivate_staking_pool": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "staking_pool",
                                "name": "StakingPool",
                                "type_arguments": [],
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "delegation_token_amount": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "staking_pool",
                                    "name": "Delegation",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": ["U64"],
                },
                "destroy_empty_delegation": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "staking_pool",
                                "name": "Delegation",
                                "type_arguments": [],
                            }
                        }
                    ],
                    "return_": [],
                },
                "destroy_empty_staked_sui": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "staking_pool",
                                "name": "StakedSui",
                                "type_arguments": [],
                            }
                        }
                    ],
                    "return_": [],
                },
                "mint_delegation_tokens_to_delegator": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "staking_pool",
                                    "name": "StakingPool",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "Address",
                        "U64",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "new": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": ["Address", "U64"],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "staking_pool",
                                "name": "StakingPool",
                                "type_arguments": [],
                            }
                        }
                    ],
                },
                "request_add_delegation": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "staking_pool",
                                    "name": "StakingPool",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "balance",
                                "name": "Balance",
                                "type_arguments": [
                                    {
                                        "Struct": {
                                            "address": "0x2",
                                            "module": "sui",
                                            "name": "SUI",
                                            "type_arguments": [],
                                        }
                                    }
                                ],
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x1",
                                "module": "option",
                                "name": "Option",
                                "type_arguments": [
                                    {
                                        "Struct": {
                                            "address": "0x2",
                                            "module": "epoch_time_lock",
                                            "name": "EpochTimeLock",
                                            "type_arguments": [],
                                        }
                                    }
                                ],
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "staked_sui_amount": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "staking_pool",
                                    "name": "StakedSui",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": ["U64"],
                },
                "sui_balance": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "staking_pool",
                                    "name": "StakingPool",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": ["U64"],
                },
                "validator_address": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "staking_pool",
                                    "name": "Delegation",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": ["Address"],
                },
                "withdraw_all_to_sui_tokens": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "staking_pool",
                                    "name": "StakingPool",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "staking_pool",
                                "name": "Delegation",
                                "type_arguments": [],
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "staking_pool",
                                    "name": "StakedSui",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "balance",
                                "name": "Balance",
                                "type_arguments": [
                                    {
                                        "Struct": {
                                            "address": "0x2",
                                            "module": "sui",
                                            "name": "SUI",
                                            "type_arguments": [],
                                        }
                                    }
                                ],
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "balance",
                                "name": "Balance",
                                "type_arguments": [
                                    {
                                        "Struct": {
                                            "address": "0x2",
                                            "module": "sui",
                                            "name": "SUI",
                                            "type_arguments": [],
                                        }
                                    }
                                ],
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x1",
                                "module": "option",
                                "name": "Option",
                                "type_arguments": [
                                    {
                                        "Struct": {
                                            "address": "0x2",
                                            "module": "epoch_time_lock",
                                            "name": "EpochTimeLock",
                                            "type_arguments": [],
                                        }
                                    }
                                ],
                            }
                        },
                    ],
                },
                "withdraw_from_inactive_pool": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "staking_pool",
                                    "name": "InactiveStakingPool",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "staking_pool",
                                    "name": "StakedSui",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "staking_pool",
                                    "name": "Delegation",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "U64",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "withdraw_stake": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "staking_pool",
                                    "name": "StakingPool",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "staking_pool",
                                    "name": "Delegation",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "staking_pool",
                                    "name": "StakedSui",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "U64",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": ["U64"],
                },
            },
        },
        "sui": {
            "name": "sui",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [{"address": "0x2", "name": "genesis"}],
            "structs": {
                "SUI": {
                    "abilities": {"abilities": ["Drop"]},
                    "fields": [{"name": "dummy_field", "type_": "Bool"}],
                    "type_parameters": [],
                }
            },
            "exposed_functions": {
                "new": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "balance",
                                "name": "Supply",
                                "type_arguments": [
                                    {
                                        "Struct": {
                                            "address": "0x2",
                                            "module": "sui",
                                            "name": "SUI",
                                            "type_arguments": [],
                                        }
                                    }
                                ],
                            }
                        }
                    ],
                },
                "transfer": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "coin",
                                "name": "Coin",
                                "type_arguments": [
                                    {
                                        "Struct": {
                                            "address": "0x2",
                                            "module": "sui",
                                            "name": "SUI",
                                            "type_arguments": [],
                                        }
                                    }
                                ],
                            }
                        },
                        "Address",
                    ],
                    "return_": [],
                },
            },
        },
        "sui_system": {
            "name": "sui_system",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [{"address": "0x2", "name": "genesis"}],
            "structs": {
                "SuiSystemState": {
                    "abilities": {"abilities": ["Key"]},
                    "fields": [
                        {
                            "name": "id",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object",
                                    "name": "UID",
                                    "type_arguments": [],
                                }
                            },
                        },
                        {"name": "epoch", "type_": "U64"},
                        {
                            "name": "validators",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator_set",
                                    "name": "ValidatorSet",
                                    "type_arguments": [],
                                }
                            },
                        },
                        {
                            "name": "sui_supply",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "balance",
                                    "name": "Supply",
                                    "type_arguments": [
                                        {
                                            "Struct": {
                                                "address": "0x2",
                                                "module": "sui",
                                                "name": "SUI",
                                                "type_arguments": [],
                                            }
                                        }
                                    ],
                                }
                            },
                        },
                        {
                            "name": "storage_fund",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "balance",
                                    "name": "Balance",
                                    "type_arguments": [
                                        {
                                            "Struct": {
                                                "address": "0x2",
                                                "module": "sui",
                                                "name": "SUI",
                                                "type_arguments": [],
                                            }
                                        }
                                    ],
                                }
                            },
                        },
                        {
                            "name": "parameters",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "sui_system",
                                    "name": "SystemParameters",
                                    "type_arguments": [],
                                }
                            },
                        },
                        {"name": "reference_gas_price", "type_": "U64"},
                        {
                            "name": "validator_report_records",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "vec_map",
                                    "name": "VecMap",
                                    "type_arguments": [
                                        "Address",
                                        {
                                            "Struct": {
                                                "address": "0x2",
                                                "module": "vec_set",
                                                "name": "VecSet",
                                                "type_arguments": ["Address"],
                                            }
                                        },
                                    ],
                                }
                            },
                        },
                    ],
                    "type_parameters": [],
                },
                "SystemParameters": {
                    "abilities": {"abilities": ["Store"]},
                    "fields": [
                        {"name": "min_validator_stake", "type_": "U64"},
                        {"name": "max_validator_candidate_count", "type_": "U64"},
                        {"name": "storage_gas_price", "type_": "U64"},
                    ],
                    "type_parameters": [],
                },
            },
            "exposed_functions": {
                "advance_epoch": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "sui_system",
                                    "name": "SuiSystemState",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "U64",
                        "U64",
                        "U64",
                        "U64",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "create": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Vector": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator",
                                    "name": "Validator",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "balance",
                                "name": "Supply",
                                "type_arguments": [
                                    {
                                        "Struct": {
                                            "address": "0x2",
                                            "module": "sui",
                                            "name": "SUI",
                                            "type_arguments": [],
                                        }
                                    }
                                ],
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "balance",
                                "name": "Balance",
                                "type_arguments": [
                                    {
                                        "Struct": {
                                            "address": "0x2",
                                            "module": "sui",
                                            "name": "SUI",
                                            "type_arguments": [],
                                        }
                                    }
                                ],
                            }
                        },
                        "U64",
                        "U64",
                        "U64",
                    ],
                    "return_": [],
                },
                "epoch": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "sui_system",
                                    "name": "SuiSystemState",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": ["U64"],
                },
                "get_reporters_of": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "sui_system",
                                    "name": "SuiSystemState",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "Address",
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "vec_set",
                                "name": "VecSet",
                                "type_arguments": ["Address"],
                            }
                        }
                    ],
                },
                "report_validator": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "sui_system",
                                    "name": "SuiSystemState",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "Address",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "request_add_delegation": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "sui_system",
                                    "name": "SuiSystemState",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "coin",
                                "name": "Coin",
                                "type_arguments": [
                                    {
                                        "Struct": {
                                            "address": "0x2",
                                            "module": "sui",
                                            "name": "SUI",
                                            "type_arguments": [],
                                        }
                                    }
                                ],
                            }
                        },
                        "Address",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "request_add_delegation_with_locked_coin": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "sui_system",
                                    "name": "SuiSystemState",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "locked_coin",
                                "name": "LockedCoin",
                                "type_arguments": [
                                    {
                                        "Struct": {
                                            "address": "0x2",
                                            "module": "sui",
                                            "name": "SUI",
                                            "type_arguments": [],
                                        }
                                    }
                                ],
                            }
                        },
                        "Address",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "request_add_stake": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "sui_system",
                                    "name": "SuiSystemState",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "coin",
                                "name": "Coin",
                                "type_arguments": [
                                    {
                                        "Struct": {
                                            "address": "0x2",
                                            "module": "sui",
                                            "name": "SUI",
                                            "type_arguments": [],
                                        }
                                    }
                                ],
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "request_add_stake_with_locked_coin": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "sui_system",
                                    "name": "SuiSystemState",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "locked_coin",
                                "name": "LockedCoin",
                                "type_arguments": [
                                    {
                                        "Struct": {
                                            "address": "0x2",
                                            "module": "sui",
                                            "name": "SUI",
                                            "type_arguments": [],
                                        }
                                    }
                                ],
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "request_add_validator": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "sui_system",
                                    "name": "SuiSystemState",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {"Vector": "U8"},
                        {"Vector": "U8"},
                        {"Vector": "U8"},
                        {"Vector": "U8"},
                        {"Vector": "U8"},
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "coin",
                                "name": "Coin",
                                "type_arguments": [
                                    {
                                        "Struct": {
                                            "address": "0x2",
                                            "module": "sui",
                                            "name": "SUI",
                                            "type_arguments": [],
                                        }
                                    }
                                ],
                            }
                        },
                        "U64",
                        "U64",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "request_remove_validator": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "sui_system",
                                    "name": "SuiSystemState",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "request_set_commission_rate": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "sui_system",
                                    "name": "SuiSystemState",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "U64",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "request_set_gas_price": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "sui_system",
                                    "name": "SuiSystemState",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "U64",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "request_switch_delegation": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "sui_system",
                                    "name": "SuiSystemState",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "staking_pool",
                                "name": "Delegation",
                                "type_arguments": [],
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "staking_pool",
                                    "name": "StakedSui",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "Address",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "request_withdraw_delegation": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "sui_system",
                                    "name": "SuiSystemState",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "staking_pool",
                                    "name": "Delegation",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "staking_pool",
                                    "name": "StakedSui",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "U64",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "request_withdraw_stake": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "sui_system",
                                    "name": "SuiSystemState",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "stake",
                                    "name": "Stake",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "U64",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "undo_report_validator": {
                    "visibility": "Public",
                    "is_entry": True,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "sui_system",
                                    "name": "SuiSystemState",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "Address",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "validator_delegate_amount": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "sui_system",
                                    "name": "SuiSystemState",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "Address",
                    ],
                    "return_": ["U64"],
                },
                "validator_stake_amount": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "sui_system",
                                    "name": "SuiSystemState",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "Address",
                    ],
                    "return_": ["U64"],
                },
            },
        },
        "table": {
            "name": "table",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [],
            "structs": {
                "Table": {
                    "abilities": {"abilities": ["Store", "Key"]},
                    "fields": [
                        {
                            "name": "id",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "object",
                                    "name": "UID",
                                    "type_arguments": [],
                                }
                            },
                        },
                        {"name": "size", "type_": "U64"},
                    ],
                    "type_parameters": [
                        {"constraints": {"abilities": ["Copy", "Drop", "Store"]}, "is_phantom": True},
                        {"constraints": {"abilities": ["Store"]}, "is_phantom": True},
                    ],
                }
            },
            "exposed_functions": {
                "add": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store"]}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "table",
                                    "name": "Table",
                                    "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                                }
                            }
                        },
                        {"TypeParameter": 0},
                        {"TypeParameter": 1},
                    ],
                    "return_": [],
                },
                "borrow": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store"]}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "table",
                                    "name": "Table",
                                    "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                                }
                            }
                        },
                        {"TypeParameter": 0},
                    ],
                    "return_": [{"Reference": {"TypeParameter": 1}}],
                },
                "borrow_mut": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store"]}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "table",
                                    "name": "Table",
                                    "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                                }
                            }
                        },
                        {"TypeParameter": 0},
                    ],
                    "return_": [{"MutableReference": {"TypeParameter": 1}}],
                },
                "contains": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store"]}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "table",
                                    "name": "Table",
                                    "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                                }
                            }
                        },
                        {"TypeParameter": 0},
                    ],
                    "return_": ["Bool"],
                },
                "destroy_empty": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store"]}],
                    "parameters": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "table",
                                "name": "Table",
                                "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                            }
                        }
                    ],
                    "return_": [],
                },
                "drop": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Drop", "Store"]}],
                    "parameters": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "table",
                                "name": "Table",
                                "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                            }
                        }
                    ],
                    "return_": [],
                },
                "is_empty": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store"]}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "table",
                                    "name": "Table",
                                    "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                                }
                            }
                        }
                    ],
                    "return_": ["Bool"],
                },
                "length": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store"]}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "table",
                                    "name": "Table",
                                    "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                                }
                            }
                        }
                    ],
                    "return_": ["U64"],
                },
                "new": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store"]}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "table",
                                "name": "Table",
                                "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                            }
                        }
                    ],
                },
                "remove": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop", "Store"]}, {"abilities": ["Store"]}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "table",
                                    "name": "Table",
                                    "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                                }
                            }
                        },
                        {"TypeParameter": 0},
                    ],
                    "return_": [{"TypeParameter": 1}],
                },
            },
        },
        "transfer": {
            "name": "transfer",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [],
            "structs": {},
            "exposed_functions": {
                "freeze_object": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Key"]}],
                    "parameters": [{"TypeParameter": 0}],
                    "return_": [],
                },
                "share_object": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Key"]}],
                    "parameters": [{"TypeParameter": 0}],
                    "return_": [],
                },
                "transfer": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Key"]}],
                    "parameters": [{"TypeParameter": 0}, "Address"],
                    "return_": [],
                },
            },
        },
        "tx_context": {
            "name": "tx_context",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [{"address": "0x2", "name": "object"}],
            "structs": {
                "TxContext": {
                    "abilities": {"abilities": ["Drop"]},
                    "fields": [
                        {"name": "signer", "type_": "Signer"},
                        {"name": "tx_hash", "type_": {"Vector": "U8"}},
                        {"name": "epoch", "type_": "U64"},
                        {"name": "ids_created", "type_": "U64"},
                    ],
                    "type_parameters": [],
                }
            },
            "exposed_functions": {
                "epoch": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": ["U64"],
                },
                "new_object": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": ["Address"],
                },
                "sender": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": ["Address"],
                },
                "signer_": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": [{"Reference": "Signer"}],
                },
            },
        },
        "typed_id": {
            "name": "typed_id",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [],
            "structs": {
                "TypedID": {
                    "abilities": {"abilities": ["Copy", "Drop", "Store"]},
                    "fields": [
                        {
                            "name": "id",
                            "type_": {
                                "Struct": {"address": "0x2", "module": "object", "name": "ID", "type_arguments": []}
                            },
                        }
                    ],
                    "type_parameters": [{"constraints": {"abilities": ["Key"]}, "is_phantom": True}],
                }
            },
            "exposed_functions": {
                "as_id": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Key"]}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "typed_id",
                                    "name": "TypedID",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        }
                    ],
                    "return_": [
                        {
                            "Reference": {
                                "Struct": {"address": "0x2", "module": "object", "name": "ID", "type_arguments": []}
                            }
                        }
                    ],
                },
                "equals_object": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Key"]}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "typed_id",
                                    "name": "TypedID",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        {"Reference": {"TypeParameter": 0}},
                    ],
                    "return_": ["Bool"],
                },
                "new": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Key"]}],
                    "parameters": [{"Reference": {"TypeParameter": 0}}],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "typed_id",
                                "name": "TypedID",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        }
                    ],
                },
                "to_id": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Key"]}],
                    "parameters": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "typed_id",
                                "name": "TypedID",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        }
                    ],
                    "return_": [{"Struct": {"address": "0x2", "module": "object", "name": "ID", "type_arguments": []}}],
                },
            },
        },
        "types": {
            "name": "types",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [],
            "structs": {},
            "exposed_functions": {
                "is_one_time_witness": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Drop"]}],
                    "parameters": [{"Reference": {"TypeParameter": 0}}],
                    "return_": ["Bool"],
                }
            },
        },
        "url": {
            "name": "url",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [],
            "structs": {
                "Url": {
                    "abilities": {"abilities": ["Copy", "Drop", "Store"]},
                    "fields": [
                        {
                            "name": "url",
                            "type_": {
                                "Struct": {
                                    "address": "0x1",
                                    "module": "ascii",
                                    "name": "String",
                                    "type_arguments": [],
                                }
                            },
                        }
                    ],
                    "type_parameters": [],
                }
            },
            "exposed_functions": {
                "inner_url": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {"address": "0x2", "module": "url", "name": "Url", "type_arguments": []}
                            }
                        }
                    ],
                    "return_": [
                        {"Struct": {"address": "0x1", "module": "ascii", "name": "String", "type_arguments": []}}
                    ],
                },
                "new_unsafe": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {"Struct": {"address": "0x1", "module": "ascii", "name": "String", "type_arguments": []}}
                    ],
                    "return_": [{"Struct": {"address": "0x2", "module": "url", "name": "Url", "type_arguments": []}}],
                },
                "new_unsafe_from_bytes": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [{"Vector": "U8"}],
                    "return_": [{"Struct": {"address": "0x2", "module": "url", "name": "Url", "type_arguments": []}}],
                },
                "update": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {"address": "0x2", "module": "url", "name": "Url", "type_arguments": []}
                            }
                        },
                        {"Struct": {"address": "0x1", "module": "ascii", "name": "String", "type_arguments": []}},
                    ],
                    "return_": [],
                },
            },
        },
        "validator": {
            "name": "validator",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [
                {"address": "0x2", "name": "genesis"},
                {"address": "0x2", "name": "sui_system"},
                {"address": "0x2", "name": "validator_set"},
            ],
            "structs": {
                "Validator": {
                    "abilities": {"abilities": ["Store"]},
                    "fields": [
                        {
                            "name": "metadata",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator",
                                    "name": "ValidatorMetadata",
                                    "type_arguments": [],
                                }
                            },
                        },
                        {"name": "stake_amount", "type_": "U64"},
                        {"name": "pending_stake", "type_": "U64"},
                        {"name": "pending_withdraw", "type_": "U64"},
                        {"name": "gas_price", "type_": "U64"},
                        {
                            "name": "delegation_staking_pool",
                            "type_": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "staking_pool",
                                    "name": "StakingPool",
                                    "type_arguments": [],
                                }
                            },
                        },
                        {"name": "commission_rate", "type_": "U64"},
                    ],
                    "type_parameters": [],
                },
                "ValidatorMetadata": {
                    "abilities": {"abilities": ["Copy", "Drop", "Store"]},
                    "fields": [
                        {"name": "sui_address", "type_": "Address"},
                        {"name": "pubkey_bytes", "type_": {"Vector": "U8"}},
                        {"name": "network_pubkey_bytes", "type_": {"Vector": "U8"}},
                        {"name": "proof_of_possession", "type_": {"Vector": "U8"}},
                        {"name": "name", "type_": {"Vector": "U8"}},
                        {"name": "net_address", "type_": {"Vector": "U8"}},
                        {"name": "next_epoch_stake", "type_": "U64"},
                        {"name": "next_epoch_delegation", "type_": "U64"},
                        {"name": "next_epoch_gas_price", "type_": "U64"},
                        {"name": "next_epoch_commission_rate", "type_": "U64"},
                    ],
                    "type_parameters": [],
                },
            },
            "exposed_functions": {
                "adjust_stake_and_gas_price": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator",
                                    "name": "Validator",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": [],
                },
                "commission_rate": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator",
                                    "name": "Validator",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": ["U64"],
                },
                "decrease_next_epoch_delegation": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator",
                                    "name": "Validator",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "U64",
                    ],
                    "return_": [],
                },
                "delegate_amount": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator",
                                    "name": "Validator",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": ["U64"],
                },
                "destroy": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "validator",
                                "name": "Validator",
                                "type_arguments": [],
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "distribute_rewards_and_new_delegations": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator",
                                    "name": "Validator",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "balance",
                                "name": "Balance",
                                "type_arguments": [
                                    {
                                        "Struct": {
                                            "address": "0x2",
                                            "module": "sui",
                                            "name": "SUI",
                                            "type_arguments": [],
                                        }
                                    }
                                ],
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "gas_price": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator",
                                    "name": "Validator",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": ["U64"],
                },
                "get_staking_pool_mut_ref": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator",
                                    "name": "Validator",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "staking_pool",
                                    "name": "StakingPool",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                },
                "increase_next_epoch_delegation": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator",
                                    "name": "Validator",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "U64",
                    ],
                    "return_": [],
                },
                "is_duplicate": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator",
                                    "name": "Validator",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator",
                                    "name": "Validator",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": ["Bool"],
                },
                "metadata": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator",
                                    "name": "Validator",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator",
                                    "name": "ValidatorMetadata",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                },
                "new": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        "Address",
                        {"Vector": "U8"},
                        {"Vector": "U8"},
                        {"Vector": "U8"},
                        {"Vector": "U8"},
                        {"Vector": "U8"},
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "balance",
                                "name": "Balance",
                                "type_arguments": [
                                    {
                                        "Struct": {
                                            "address": "0x2",
                                            "module": "sui",
                                            "name": "SUI",
                                            "type_arguments": [],
                                        }
                                    }
                                ],
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x1",
                                "module": "option",
                                "name": "Option",
                                "type_arguments": [
                                    {
                                        "Struct": {
                                            "address": "0x2",
                                            "module": "epoch_time_lock",
                                            "name": "EpochTimeLock",
                                            "type_arguments": [],
                                        }
                                    }
                                ],
                            }
                        },
                        "U64",
                        "U64",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "validator",
                                "name": "Validator",
                                "type_arguments": [],
                            }
                        }
                    ],
                },
                "pending_stake_amount": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator",
                                    "name": "Validator",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": ["U64"],
                },
                "pending_withdraw": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator",
                                    "name": "Validator",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": ["U64"],
                },
                "request_add_delegation": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator",
                                    "name": "Validator",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "balance",
                                "name": "Balance",
                                "type_arguments": [
                                    {
                                        "Struct": {
                                            "address": "0x2",
                                            "module": "sui",
                                            "name": "SUI",
                                            "type_arguments": [],
                                        }
                                    }
                                ],
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x1",
                                "module": "option",
                                "name": "Option",
                                "type_arguments": [
                                    {
                                        "Struct": {
                                            "address": "0x2",
                                            "module": "epoch_time_lock",
                                            "name": "EpochTimeLock",
                                            "type_arguments": [],
                                        }
                                    }
                                ],
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "request_add_stake": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator",
                                    "name": "Validator",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "balance",
                                "name": "Balance",
                                "type_arguments": [
                                    {
                                        "Struct": {
                                            "address": "0x2",
                                            "module": "sui",
                                            "name": "SUI",
                                            "type_arguments": [],
                                        }
                                    }
                                ],
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x1",
                                "module": "option",
                                "name": "Option",
                                "type_arguments": [
                                    {
                                        "Struct": {
                                            "address": "0x2",
                                            "module": "epoch_time_lock",
                                            "name": "EpochTimeLock",
                                            "type_arguments": [],
                                        }
                                    }
                                ],
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "request_set_commission_rate": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator",
                                    "name": "Validator",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "U64",
                    ],
                    "return_": [],
                },
                "request_set_gas_price": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator",
                                    "name": "Validator",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "U64",
                    ],
                    "return_": [],
                },
                "request_withdraw_delegation": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator",
                                    "name": "Validator",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "staking_pool",
                                    "name": "Delegation",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "staking_pool",
                                    "name": "StakedSui",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "U64",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "request_withdraw_stake": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator",
                                    "name": "Validator",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "stake",
                                    "name": "Stake",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "U64",
                        "U64",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "stake_amount": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator",
                                    "name": "Validator",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": ["U64"],
                },
                "sui_address": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator",
                                    "name": "Validator",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": ["Address"],
                },
            },
        },
        "validator_set": {
            "name": "validator_set",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [{"address": "0x2", "name": "sui_system"}],
            "structs": {
                "ValidatorSet": {
                    "abilities": {"abilities": ["Store"]},
                    "fields": [
                        {"name": "total_validator_stake", "type_": "U64"},
                        {"name": "total_delegation_stake", "type_": "U64"},
                        {"name": "quorum_stake_threshold", "type_": "U64"},
                        {
                            "name": "active_validators",
                            "type_": {
                                "Vector": {
                                    "Struct": {
                                        "address": "0x2",
                                        "module": "validator",
                                        "name": "Validator",
                                        "type_arguments": [],
                                    }
                                }
                            },
                        },
                        {
                            "name": "pending_validators",
                            "type_": {
                                "Vector": {
                                    "Struct": {
                                        "address": "0x2",
                                        "module": "validator",
                                        "name": "Validator",
                                        "type_arguments": [],
                                    }
                                }
                            },
                        },
                        {"name": "pending_removals", "type_": {"Vector": "U64"}},
                        {
                            "name": "next_epoch_validators",
                            "type_": {
                                "Vector": {
                                    "Struct": {
                                        "address": "0x2",
                                        "module": "validator",
                                        "name": "ValidatorMetadata",
                                        "type_arguments": [],
                                    }
                                }
                            },
                        },
                    ],
                    "type_parameters": [],
                }
            },
            "exposed_functions": {
                "advance_epoch": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator_set",
                                    "name": "ValidatorSet",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "balance",
                                    "name": "Balance",
                                    "type_arguments": [
                                        {
                                            "Struct": {
                                                "address": "0x2",
                                                "module": "sui",
                                                "name": "SUI",
                                                "type_arguments": [],
                                            }
                                        }
                                    ],
                                }
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "balance",
                                    "name": "Balance",
                                    "type_arguments": [
                                        {
                                            "Struct": {
                                                "address": "0x2",
                                                "module": "sui",
                                                "name": "SUI",
                                                "type_arguments": [],
                                            }
                                        }
                                    ],
                                }
                            }
                        },
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "vec_map",
                                    "name": "VecMap",
                                    "type_arguments": [
                                        "Address",
                                        {
                                            "Struct": {
                                                "address": "0x2",
                                                "module": "vec_set",
                                                "name": "VecSet",
                                                "type_arguments": ["Address"],
                                            }
                                        },
                                    ],
                                }
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "derive_reference_gas_price": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator_set",
                                    "name": "ValidatorSet",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": ["U64"],
                },
                "is_active_validator": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator_set",
                                    "name": "ValidatorSet",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "Address",
                    ],
                    "return_": ["Bool"],
                },
                "new": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Vector": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator",
                                    "name": "Validator",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "validator_set",
                                "name": "ValidatorSet",
                                "type_arguments": [],
                            }
                        }
                    ],
                },
                "next_epoch_validator_count": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator_set",
                                    "name": "ValidatorSet",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": ["U64"],
                },
                "request_add_delegation": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator_set",
                                    "name": "ValidatorSet",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "Address",
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "balance",
                                "name": "Balance",
                                "type_arguments": [
                                    {
                                        "Struct": {
                                            "address": "0x2",
                                            "module": "sui",
                                            "name": "SUI",
                                            "type_arguments": [],
                                        }
                                    }
                                ],
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x1",
                                "module": "option",
                                "name": "Option",
                                "type_arguments": [
                                    {
                                        "Struct": {
                                            "address": "0x2",
                                            "module": "epoch_time_lock",
                                            "name": "EpochTimeLock",
                                            "type_arguments": [],
                                        }
                                    }
                                ],
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "request_add_stake": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator_set",
                                    "name": "ValidatorSet",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "balance",
                                "name": "Balance",
                                "type_arguments": [
                                    {
                                        "Struct": {
                                            "address": "0x2",
                                            "module": "sui",
                                            "name": "SUI",
                                            "type_arguments": [],
                                        }
                                    }
                                ],
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x1",
                                "module": "option",
                                "name": "Option",
                                "type_arguments": [
                                    {
                                        "Struct": {
                                            "address": "0x2",
                                            "module": "epoch_time_lock",
                                            "name": "EpochTimeLock",
                                            "type_arguments": [],
                                        }
                                    }
                                ],
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "request_add_validator": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator_set",
                                    "name": "ValidatorSet",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "validator",
                                "name": "Validator",
                                "type_arguments": [],
                            }
                        },
                    ],
                    "return_": [],
                },
                "request_remove_validator": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator_set",
                                    "name": "ValidatorSet",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "request_set_commission_rate": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator_set",
                                    "name": "ValidatorSet",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "U64",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "request_set_gas_price": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator_set",
                                    "name": "ValidatorSet",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "U64",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "request_switch_delegation": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator_set",
                                    "name": "ValidatorSet",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "staking_pool",
                                "name": "Delegation",
                                "type_arguments": [],
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "staking_pool",
                                    "name": "StakedSui",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "Address",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "request_withdraw_delegation": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator_set",
                                    "name": "ValidatorSet",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "staking_pool",
                                    "name": "Delegation",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "staking_pool",
                                    "name": "StakedSui",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "U64",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "request_withdraw_stake": {
                    "visibility": "Friend",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator_set",
                                    "name": "ValidatorSet",
                                    "type_arguments": [],
                                }
                            }
                        },
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "stake",
                                    "name": "Stake",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "U64",
                        "U64",
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "tx_context",
                                    "name": "TxContext",
                                    "type_arguments": [],
                                }
                            }
                        },
                    ],
                    "return_": [],
                },
                "total_delegation_stake": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator_set",
                                    "name": "ValidatorSet",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": ["U64"],
                },
                "total_validator_stake": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator_set",
                                    "name": "ValidatorSet",
                                    "type_arguments": [],
                                }
                            }
                        }
                    ],
                    "return_": ["U64"],
                },
                "validator_delegate_amount": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator_set",
                                    "name": "ValidatorSet",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "Address",
                    ],
                    "return_": ["U64"],
                },
                "validator_stake_amount": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "validator_set",
                                    "name": "ValidatorSet",
                                    "type_arguments": [],
                                }
                            }
                        },
                        "Address",
                    ],
                    "return_": ["U64"],
                },
            },
        },
        "vec_map": {
            "name": "vec_map",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [],
            "structs": {
                "Entry": {
                    "abilities": {"abilities": ["Copy", "Drop", "Store"]},
                    "fields": [
                        {"name": "key", "type_": {"TypeParameter": 0}},
                        {"name": "value", "type_": {"TypeParameter": 1}},
                    ],
                    "type_parameters": [
                        {"constraints": {"abilities": ["Copy"]}, "is_phantom": False},
                        {"constraints": {"abilities": []}, "is_phantom": False},
                    ],
                },
                "VecMap": {
                    "abilities": {"abilities": ["Copy", "Drop", "Store"]},
                    "fields": [
                        {
                            "name": "contents",
                            "type_": {
                                "Vector": {
                                    "Struct": {
                                        "address": "0x2",
                                        "module": "vec_map",
                                        "name": "Entry",
                                        "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                                    }
                                }
                            },
                        }
                    ],
                    "type_parameters": [
                        {"constraints": {"abilities": ["Copy"]}, "is_phantom": False},
                        {"constraints": {"abilities": []}, "is_phantom": False},
                    ],
                },
            },
            "exposed_functions": {
                "contains": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy"]}, {"abilities": []}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "vec_map",
                                    "name": "VecMap",
                                    "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                                }
                            }
                        },
                        {"Reference": {"TypeParameter": 0}},
                    ],
                    "return_": ["Bool"],
                },
                "destroy_empty": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy"]}, {"abilities": []}],
                    "parameters": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "vec_map",
                                "name": "VecMap",
                                "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                            }
                        }
                    ],
                    "return_": [],
                },
                "empty": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy"]}, {"abilities": []}],
                    "parameters": [],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "vec_map",
                                "name": "VecMap",
                                "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                            }
                        }
                    ],
                },
                "get": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy"]}, {"abilities": []}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "vec_map",
                                    "name": "VecMap",
                                    "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                                }
                            }
                        },
                        {"Reference": {"TypeParameter": 0}},
                    ],
                    "return_": [{"Reference": {"TypeParameter": 1}}],
                },
                "get_entry_by_idx": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy"]}, {"abilities": []}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "vec_map",
                                    "name": "VecMap",
                                    "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                                }
                            }
                        },
                        "U64",
                    ],
                    "return_": [{"Reference": {"TypeParameter": 0}}, {"Reference": {"TypeParameter": 1}}],
                },
                "get_entry_by_idx_mut": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy"]}, {"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "vec_map",
                                    "name": "VecMap",
                                    "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                                }
                            }
                        },
                        "U64",
                    ],
                    "return_": [{"Reference": {"TypeParameter": 0}}, {"MutableReference": {"TypeParameter": 1}}],
                },
                "get_idx": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy"]}, {"abilities": []}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "vec_map",
                                    "name": "VecMap",
                                    "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                                }
                            }
                        },
                        {"Reference": {"TypeParameter": 0}},
                    ],
                    "return_": ["U64"],
                },
                "get_idx_opt": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy"]}, {"abilities": []}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "vec_map",
                                    "name": "VecMap",
                                    "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                                }
                            }
                        },
                        {"Reference": {"TypeParameter": 0}},
                    ],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x1",
                                "module": "option",
                                "name": "Option",
                                "type_arguments": ["U64"],
                            }
                        }
                    ],
                },
                "get_mut": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy"]}, {"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "vec_map",
                                    "name": "VecMap",
                                    "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                                }
                            }
                        },
                        {"Reference": {"TypeParameter": 0}},
                    ],
                    "return_": [{"MutableReference": {"TypeParameter": 1}}],
                },
                "insert": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy"]}, {"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "vec_map",
                                    "name": "VecMap",
                                    "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                                }
                            }
                        },
                        {"TypeParameter": 0},
                        {"TypeParameter": 1},
                    ],
                    "return_": [],
                },
                "into_keys_values": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy"]}, {"abilities": []}],
                    "parameters": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "vec_map",
                                "name": "VecMap",
                                "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                            }
                        }
                    ],
                    "return_": [{"Vector": {"TypeParameter": 0}}, {"Vector": {"TypeParameter": 1}}],
                },
                "is_empty": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy"]}, {"abilities": []}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "vec_map",
                                    "name": "VecMap",
                                    "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                                }
                            }
                        }
                    ],
                    "return_": ["Bool"],
                },
                "pop": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy"]}, {"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "vec_map",
                                    "name": "VecMap",
                                    "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                                }
                            }
                        }
                    ],
                    "return_": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                },
                "remove": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy"]}, {"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "vec_map",
                                    "name": "VecMap",
                                    "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                                }
                            }
                        },
                        {"Reference": {"TypeParameter": 0}},
                    ],
                    "return_": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                },
                "remove_entry_by_idx": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy"]}, {"abilities": []}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "vec_map",
                                    "name": "VecMap",
                                    "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                                }
                            }
                        },
                        "U64",
                    ],
                    "return_": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                },
                "size": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy"]}, {"abilities": []}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "vec_map",
                                    "name": "VecMap",
                                    "type_arguments": [{"TypeParameter": 0}, {"TypeParameter": 1}],
                                }
                            }
                        }
                    ],
                    "return_": ["U64"],
                },
            },
        },
        "vec_set": {
            "name": "vec_set",
            "address": "0x2",
            "file_format_version": 6,
            "friends": [],
            "structs": {
                "VecSet": {
                    "abilities": {"abilities": ["Copy", "Drop", "Store"]},
                    "fields": [{"name": "contents", "type_": {"Vector": {"TypeParameter": 0}}}],
                    "type_parameters": [{"constraints": {"abilities": ["Copy", "Drop"]}, "is_phantom": False}],
                }
            },
            "exposed_functions": {
                "contains": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop"]}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "vec_set",
                                    "name": "VecSet",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        {"Reference": {"TypeParameter": 0}},
                    ],
                    "return_": ["Bool"],
                },
                "empty": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop"]}],
                    "parameters": [],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "vec_set",
                                "name": "VecSet",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        }
                    ],
                },
                "insert": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop"]}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "vec_set",
                                    "name": "VecSet",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        {"TypeParameter": 0},
                    ],
                    "return_": [],
                },
                "into_keys": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop"]}],
                    "parameters": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "vec_set",
                                "name": "VecSet",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        }
                    ],
                    "return_": [{"Vector": {"TypeParameter": 0}}],
                },
                "is_empty": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop"]}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "vec_set",
                                    "name": "VecSet",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        }
                    ],
                    "return_": ["Bool"],
                },
                "remove": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop"]}],
                    "parameters": [
                        {
                            "MutableReference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "vec_set",
                                    "name": "VecSet",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        },
                        {"Reference": {"TypeParameter": 0}},
                    ],
                    "return_": [],
                },
                "singleton": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop"]}],
                    "parameters": [{"TypeParameter": 0}],
                    "return_": [
                        {
                            "Struct": {
                                "address": "0x2",
                                "module": "vec_set",
                                "name": "VecSet",
                                "type_arguments": [{"TypeParameter": 0}],
                            }
                        }
                    ],
                },
                "size": {
                    "visibility": "Public",
                    "is_entry": False,
                    "type_parameters": [{"abilities": ["Copy", "Drop"]}],
                    "parameters": [
                        {
                            "Reference": {
                                "Struct": {
                                    "address": "0x2",
                                    "module": "vec_set",
                                    "name": "VecSet",
                                    "type_arguments": [{"TypeParameter": 0}],
                                }
                            }
                        }
                    ],
                    "return_": ["U64"],
                },
            },
        },
    }


@pytest.fixture
def sui_coin_descriptor():
    """Descriptor result."""
    return {
        "objectId": "0x0e5a550c39b571fb8b1fb40da90798e4b5cfe04e",
        "version": 7,
        "digest": "jkziyuckfYtekHX02f0oQcgOKVc0VAx87crwBOzXQUw=",
        "type": "0x2::coin::Coin<0x2::sui::SUI>",
        "owner": {"AddressOwner": "0xf5f27ea854d8d5efae00b68c313057566872e7fe"},
        "previousTransaction": "aSkUwcvElhhqIHiTUjuNnNamn67X0yYVOcBUnUA1Hr4=",
    }


@pytest.fixture
def coin_descriptor():
    """Descriptor result."""


@pytest.fixture
def data_descriptor():
    """Descriptor result."""
    return {
        "objectId": "0xf48abd518562eb9bf4b0d41917e09127d308c6b5",
        "version": 1,
        "digest": "fRjliDFAFy35Fsqmud4vKgyqROZt4T+mREPl3/AqJoY=",
        "type": "0xf9b785171ece90a0cb22b487ef31b8efeb8cc254::base::ServiceTracker",
        "owner": {"AddressOwner": "0xf5f27ea854d8d5efae00b68c313057566872e7fe"},
        "previousTransaction": "YvaJdMh9neQactpKcSU3e/iAdpetqIFtn+6/dealqws=",
    }


@pytest.fixture
def data_objectread_type():
    """Return valid data type."""
    return {
        "status": "Exists",
        "details": {
            "data": {
                "dataType": "moveObject",
                "type": "0xec27e8a2343091f114d488c0d6c72a45d617fece::base::ServiceTracker",
                "has_public_transfer": False,
                "fields": {
                    "count_accounts": 0,
                    "id": {"id": "0x1e22fc1893fe2a921ac6eb1b308c1d8754a89ed5"},
                    "initialized": True,
                },
            },
            "owner": {"AddressOwner": "0xf5f27ea854d8d5efae00b68c313057566872e7fe"},
            "previousTransaction": "Bnnu7VTJWmj8umr3zHas2BhGXO6v6DcE0GsXOqo0S1A=",
            "storageRebate": 14,
            "reference": {
                "objectId": "0x1e22fc1893fe2a921ac6eb1b308c1d8754a89ed5",
                "version": 1,
                "digest": "Szvm4zIOvoGPc2w27lifhnPHWmmRhMW4Hkx7KTw6ibQ=",
            },
        },
    }


@pytest.fixture
def suicoin_objectread_type():
    """Return valid sui gas type."""
    return {
        "status": "Exists",
        "details": {
            "data": {
                "dataType": "moveObject",
                "type": "0x2::coin::Coin<0x2::sui::SUI>",
                "has_public_transfer": True,
                "fields": {"balance": 9998893, "id": {"id": "0x980ed36ad60d3a2f73e84945d274120f056b3d73"}},
            },
            "owner": {"AddressOwner": "0xf5f27ea854d8d5efae00b68c313057566872e7fe"},
            "previousTransaction": "Bnnu7VTJWmj8umr3zHas2BhGXO6v6DcE0GsXOqo0S1A=",
            "storageRebate": 16,
            "reference": {
                "objectId": "0x980ed36ad60d3a2f73e84945d274120f056b3d73",
                "version": 2,
                "digest": "wt2hg7HpYyyKh2AXLsevODMapSLKv7NtyRFgfklU3ps=",
            },
        },
    }


@pytest.fixture
def get_event_result():
    """Return valid sui_getEvents result."""
    return {
        "data": [
            {
                "timestamp": 1668472627811,
                "txDigest": "mccOyWThvnzPpJHy88NNzAfzNUCoLgmrEODSxs7Ey1Q=",
                "id": {"txDigest": 3537, "eventSeq": 10},
                "event": {
                    "coinBalanceChange": {
                        "packageId": "0x0000000000000000000000000000000000000002",
                        "transactionModule": "pay",
                        "sender": "0x7ac1cc73234f09b7c14b4757d3c959523ee4fcf4",
                        "changeType": "Pay",
                        "owner": {"AddressOwner": "0x7ac1cc73234f09b7c14b4757d3c959523ee4fcf4"},
                        "coinType": "0x2::sui::SUI",
                        "coinObjectId": "0xbe5b2bcfe8a0bf92df909e900d3e11eb25012e2c",
                        "version": 1,
                        "amount": -10000000,
                    }
                },
            },
            {
                "timestamp": 1668472627811,
                "txDigest": "mccOyWThvnzPpJHy88NNzAfzNUCoLgmrEODSxs7Ey1Q=",
                "id": {"txDigest": 3537, "eventSeq": 11},
                "event": {
                    "coinBalanceChange": {
                        "packageId": "0x0000000000000000000000000000000000000002",
                        "transactionModule": "pay",
                        "sender": "0x7ac1cc73234f09b7c14b4757d3c959523ee4fcf4",
                        "changeType": "Pay",
                        "owner": {"AddressOwner": "0x7ac1cc73234f09b7c14b4757d3c959523ee4fcf4"},
                        "coinType": "0x2::sui::SUI",
                        "coinObjectId": "0xc8b0652e0e62e76ee51536e7f017da19264db1d6",
                        "version": 1,
                        "amount": -10000000,
                    }
                },
            },
            {
                "timestamp": 1668472627811,
                "txDigest": "mccOyWThvnzPpJHy88NNzAfzNUCoLgmrEODSxs7Ey1Q=",
                "id": {"txDigest": 3537, "eventSeq": 12},
                "event": {
                    "coinBalanceChange": {
                        "packageId": "0x0000000000000000000000000000000000000002",
                        "transactionModule": "pay",
                        "sender": "0x7ac1cc73234f09b7c14b4757d3c959523ee4fcf4",
                        "changeType": "Pay",
                        "owner": {"AddressOwner": "0x7ac1cc73234f09b7c14b4757d3c959523ee4fcf4"},
                        "coinType": "0x2::sui::SUI",
                        "coinObjectId": "0xd27efc607aac2ebd0089515d17bf9e4de0524f4a",
                        "version": 1,
                        "amount": -10000000,
                    }
                },
            },
        ],
        "nextCursor": None,
    }


@pytest.fixture
def get_gas_result():
    """Return result of getting SUI gas from faucet."""
    return {
        "transferred_gas_objects": [
            {
                "amount": 10000000,
                "id": "0x3457a29e3ac20c74d93996c5c525091c88de7dfa",
                "transfer_tx_digest": "ZzEpx6Eio5F1pvEC8CVDQO9R0F2CGJYAKq1kWOtqBpQ=",
            },
            {
                "amount": 10000000,
                "id": "0x81b70d63c7df76c1e814cbd29be59056193d9bea",
                "transfer_tx_digest": "ZzEpx6Eio5F1pvEC8CVDQO9R0F2CGJYAKq1kWOtqBpQ=",
            },
            {
                "amount": 10000000,
                "id": "0xcd1c919fd290c37a31c6848eaf62dcc397b65f35",
                "transfer_tx_digest": "ZzEpx6Eio5F1pvEC8CVDQO9R0F2CGJYAKq1kWOtqBpQ=",
            },
            {
                "amount": 10000000,
                "id": "0xe1f1a852ab9136f844d4b586679003578a414e2f",
                "transfer_tx_digest": "ZzEpx6Eio5F1pvEC8CVDQO9R0F2CGJYAKq1kWOtqBpQ=",
            },
            {
                "amount": 10000000,
                "id": "0xfe0dd544dbf88d81e38fbd43c8a5db0bc42dedd5",
                "transfer_tx_digest": "ZzEpx6Eio5F1pvEC8CVDQO9R0F2CGJYAKq1kWOtqBpQ=",
            },
        ],
        "error": None,
    }


@pytest.fixture
def get_txevent_result():
    """Return valid sui_subsribeTransaction result."""
    return {
        "jsonrpc": "2.0",
        "method": "sui_subscribeTransaction",
        "params": {
            "subscription": 3209114665361176,
            "result": {
                "certificate": {
                    "transactionDigest": "9GsVP2JFc9FKKpMPqTY681CRnM1kqDcVwao33N9RJEdV",
                    "data": {
                        "transactions": [
                            {
                                "Call": {
                                    "package": {
                                        "objectId": "0x393b1b81a75697df6f21ceca589645e5d43d95bc",
                                        "version": 1,
                                        "digest": "rmXi0Hqmu9nyCluQCXWiVuVWx2Imeh1mydYbJ0cG5nQ=",
                                    },
                                    "module": "marketplace_nofee",
                                    "function": "list",
                                    "typeArguments": [
                                        "0x393b1b81a75697df6f21ceca589645e5d43d95bc::meta_nft::MetaNFT",
                                        "0x2::sui::SUI",
                                    ],
                                    "arguments": [
                                        "0xa61e4919e1fabfa57cfee1433ccce6707eda956",
                                        "0x5e435c99a0de0d865602415d47f214295fdfbd5b",
                                        [128, 150, 152, 0, 0, 0, 0, 0],
                                    ],
                                }
                            }
                        ],
                        "sender": "0x15b49685f5360c83e930410bb266896fcb676b77",
                        "gasPayment": {
                            "objectId": "0x1bc640fe42c46b94284969f77d51bcf1c88be168",
                            "version": 127923,
                            "digest": "9lVAV2AoGtjRHGOoucoeR005ao7Ddl2ZU5JpwqiE0qs=",
                        },
                        "gasPrice": 1,
                        "gasBudget": 10000,
                    },
                    "txSignature": "AJqPpR06VO9xNtSNW4CcSU+ClMgHdjMZK7Q1sdToXhCTzehLqSk6bqhoUkNQbnQPcXXgjKk4eIdl1TTFe55U4QiP2Q9j7jGq+XD9JhgVVHJZu6xHOLVLDXqSmiyXz2JAWw==",
                    "authSignInfo": {
                        "epoch": 5,
                        "signature": "AaHaRRgm8pGyqgxmCIEUfe4jUvvpG32a0Php4sMhsLPdvP44L85NkIc80xCJGo69sw==",
                        "signers_map": [58, 48, 0, 0, 1, 0, 0, 0, 0, 0, 2, 0, 16, 0, 0, 0, 1, 0, 2, 0, 3, 0],
                    },
                },
                "effects": {
                    "status": {"status": "success"},
                    "gasUsed": {"computationCost": 380, "storageCost": 97, "storageRebate": 56},
                    "sharedObjects": [
                        {
                            "objectId": "0x0a61e4919e1fabfa57cfee1433ccce6707eda956",
                            "version": 127922,
                            "digest": "WGrYA/okuXtaTQJA5QxaT8WcQraSN0wvgd8FM7wm6JY=",
                        }
                    ],
                    "transactionDigest": "9GsVP2JFc9FKKpMPqTY681CRnM1kqDcVwao33N9RJEdV",
                    "created": [
                        {
                            "owner": {"ObjectOwner": "0x94cca84604ab8892c529f0163ce233de275c2efd"},
                            "reference": {
                                "objectId": "0x24c339ca58e2469b2116e2819a25bf69e5e4724e",
                                "version": 127924,
                                "digest": "EW8WCaC026uERnxaP+sMWwAqmKW6xcvbC1600s+RmMs=",
                            },
                        },
                        {
                            "owner": {"ObjectOwner": "0x0a61e4919e1fabfa57cfee1433ccce6707eda956"},
                            "reference": {
                                "objectId": "0x94cca84604ab8892c529f0163ce233de275c2efd",
                                "version": 127924,
                                "digest": "e6e0zuqNYUwl6xee9nwNnLfYqExTeZocqN5yC3OgWPk=",
                            },
                        },
                    ],
                    "mutated": [
                        {
                            "owner": {"Shared": {"initial_shared_version": 44}},
                            "reference": {
                                "objectId": "0x0a61e4919e1fabfa57cfee1433ccce6707eda956",
                                "version": 127924,
                                "digest": "odRipsnD5bwu1PBeoq69jJUnhE+JccJTB5uGZURXqos=",
                            },
                        },
                        {
                            "owner": {"AddressOwner": "0x15b49685f5360c83e930410bb266896fcb676b77"},
                            "reference": {
                                "objectId": "0x1bc640fe42c46b94284969f77d51bcf1c88be168",
                                "version": 127924,
                                "digest": "K5ppNIXvOwFT4f0Ajjxrudxfj0ZNZ6fLssVi5O4Rzco=",
                            },
                        },
                    ],
                    "wrapped": [
                        {
                            "objectId": "0x5e435c99a0de0d865602415d47f214295fdfbd5b",
                            "version": 127924,
                            "digest": "WFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFg=",
                        }
                    ],
                    "gasObject": {
                        "owner": {"AddressOwner": "0x15b49685f5360c83e930410bb266896fcb676b77"},
                        "reference": {
                            "objectId": "0x1bc640fe42c46b94284969f77d51bcf1c88be168",
                            "version": 127924,
                            "digest": "K5ppNIXvOwFT4f0Ajjxrudxfj0ZNZ6fLssVi5O4Rzco=",
                        },
                    },
                    "events": [
                        {
                            "coinBalanceChange": {
                                "packageId": "0x0000000000000000000000000000000000000002",
                                "transactionModule": "gas",
                                "sender": "0x15b49685f5360c83e930410bb266896fcb676b77",
                                "changeType": "Gas",
                                "owner": {"AddressOwner": "0x15b49685f5360c83e930410bb266896fcb676b77"},
                                "coinType": "0x2::sui::SUI",
                                "coinObjectId": "0x1bc640fe42c46b94284969f77d51bcf1c88be168",
                                "version": 127923,
                                "amount": -421,
                            }
                        },
                        {
                            "mutateObject": {
                                "packageId": "0x393b1b81a75697df6f21ceca589645e5d43d95bc",
                                "transactionModule": "marketplace_nofee",
                                "sender": "0x15b49685f5360c83e930410bb266896fcb676b77",
                                "objectType": "0x393b1b81a75697df6f21ceca589645e5d43d95bc::marketplace_nofee::Marketplace",
                                "objectId": "0x0a61e4919e1fabfa57cfee1433ccce6707eda956",
                                "version": 127924,
                            }
                        },
                        {
                            "newObject": {
                                "packageId": "0x393b1b81a75697df6f21ceca589645e5d43d95bc",
                                "transactionModule": "marketplace_nofee",
                                "sender": "0x15b49685f5360c83e930410bb266896fcb676b77",
                                "recipient": {"ObjectOwner": "0x94cca84604ab8892c529f0163ce233de275c2efd"},
                                "objectType": "0x393b1b81a75697df6f21ceca589645e5d43d95bc::marketplace_nofee::Listing<0x393b1b81a75697df6f21ceca589645e5d43d95bc::meta_nft::MetaNFT, 0x2::sui::SUI>",
                                "objectId": "0x24c339ca58e2469b2116e2819a25bf69e5e4724e",
                                "version": 127924,
                            }
                        },
                        {
                            "newObject": {
                                "packageId": "0x393b1b81a75697df6f21ceca589645e5d43d95bc",
                                "transactionModule": "marketplace_nofee",
                                "sender": "0x15b49685f5360c83e930410bb266896fcb676b77",
                                "recipient": {"ObjectOwner": "0x0a61e4919e1fabfa57cfee1433ccce6707eda956"},
                                "objectType": "0x2::dynamic_field::Field<0x2::dynamic_object_field::Wrapper<0x2::object::ID>, 0x2::object::ID>",
                                "objectId": "0x94cca84604ab8892c529f0163ce233de275c2efd",
                                "version": 127924,
                            }
                        },
                        {
                            "deleteObject": {
                                "packageId": "0x393b1b81a75697df6f21ceca589645e5d43d95bc",
                                "transactionModule": "marketplace_nofee",
                                "sender": "0x15b49685f5360c83e930410bb266896fcb676b77",
                                "objectId": "0x5e435c99a0de0d865602415d47f214295fdfbd5b",
                                "version": 127924,
                            }
                        },
                    ],
                    "dependencies": [
                        "8VRBCQuDzKjsSiDGJdRWQxACnnN6T9mD5Pb1SvmdufPN",
                        "AcFwWyMEJzxuG3pNcXSdFAktq2SkWUhpPCE58NctyQmM",
                        "CuzekBAGTEHoBT3d6x1MDG8wJafLKqtxsGU8D4k7cBxo",
                    ],
                },
                "timestamp_ms": 1674216639927,
                "parsed_data": None,
            },
        },
    }


@pytest.fixture
def get_delegated_stakes_result():
    """Return valid sui_subsribeTransaction result."""
    return [
        {
            "staked_sui": {
                "id": {"id": "0xcf88de1b6059129213...1cb2a5bd2c"},
                "validator_address": "0x77c5faae16095f44df...b371780151",
                "pool_starting_epoch": 1,
                "delegation_request_epoch": 14,
                "principal": {"value": 1000000},
                "sui_token_lock": None,
            },
            "delegation_status": "Pending",
        }
    ]


@pytest.fixture
def get_system_state_result():
    """Return valid sui_getSystemState result."""
    return {
        "info": {"id": "0x0000000000000000000000000000000000000005"},
        "epoch": 1,
        "validators": {
            "validator_stake": 40888704,
            "delegation_stake": 30022747,
            "active_validators": [
                {
                    "metadata": {
                        "sui_address": "0x339383679a0412216560c564debefc2eed8d9fb3",
                        "pubkey_bytes": [
                            129,
                            59,
                            150,
                            147,
                            19,
                            134,
                            151,
                            242,
                            174,
                            81,
                            217,
                            181,
                            239,
                            102,
                            78,
                            93,
                            157,
                            104,
                            165,
                            41,
                            99,
                            247,
                            63,
                            114,
                            164,
                            227,
                            222,
                            13,
                            67,
                            22,
                            193,
                            56,
                            185,
                            244,
                            55,
                            237,
                            71,
                            156,
                            216,
                            160,
                            164,
                            81,
                            220,
                            17,
                            238,
                            25,
                            226,
                            48,
                            11,
                            113,
                            40,
                            126,
                            243,
                            98,
                            37,
                            221,
                            221,
                            232,
                            88,
                            150,
                            104,
                            205,
                            110,
                            208,
                            77,
                            82,
                            79,
                            43,
                            145,
                            210,
                            84,
                            62,
                            158,
                            210,
                            129,
                            1,
                            19,
                            91,
                            13,
                            2,
                            84,
                            111,
                            202,
                            60,
                            225,
                            71,
                            104,
                            118,
                            16,
                            212,
                            44,
                            225,
                            34,
                            218,
                            176,
                            245,
                        ],
                        "network_pubkey_bytes": [
                            222,
                            134,
                            66,
                            194,
                            126,
                            108,
                            36,
                            64,
                            122,
                            168,
                            220,
                            117,
                            151,
                            240,
                            193,
                            83,
                            179,
                            205,
                            91,
                            21,
                            142,
                            182,
                            247,
                            176,
                            193,
                            51,
                            183,
                            7,
                            157,
                            94,
                            150,
                            235,
                        ],
                        "worker_pubkey_bytes": [
                            174,
                            23,
                            52,
                            103,
                            29,
                            68,
                            228,
                            77,
                            42,
                            162,
                            133,
                            58,
                            231,
                            37,
                            223,
                            122,
                            186,
                            231,
                            152,
                            217,
                            251,
                            161,
                            72,
                            31,
                            118,
                            182,
                            10,
                            196,
                            0,
                            41,
                            122,
                            222,
                        ],
                        "proof_of_possession_bytes": [
                            172,
                            148,
                            52,
                            79,
                            76,
                            215,
                            22,
                            131,
                            68,
                            4,
                            59,
                            184,
                            155,
                            72,
                            153,
                            68,
                            147,
                            253,
                            54,
                            155,
                            68,
                            79,
                            243,
                            210,
                            189,
                            90,
                            216,
                            107,
                            157,
                            10,
                            82,
                            157,
                            85,
                            210,
                            40,
                            35,
                            180,
                            48,
                            226,
                            50,
                            137,
                            246,
                            12,
                            193,
                            237,
                            2,
                            148,
                            197,
                        ],
                        "name": [118, 97, 108, 105, 100, 97, 116, 111, 114, 45, 50],
                        "description": [],
                        "image_url": [],
                        "project_url": [],
                        "net_address": [
                            53,
                            30,
                            101,
                            119,
                            114,
                            45,
                            115,
                            117,
                            105,
                            118,
                            97,
                            108,
                            45,
                            97,
                            52,
                            98,
                            100,
                            100,
                            46,
                            100,
                            101,
                            118,
                            110,
                            101,
                            116,
                            46,
                            115,
                            117,
                            105,
                            46,
                            105,
                            111,
                            6,
                            31,
                            144,
                            224,
                            3,
                        ],
                        "consensus_address": [
                            53,
                            30,
                            101,
                            119,
                            114,
                            45,
                            115,
                            117,
                            105,
                            118,
                            97,
                            108,
                            45,
                            97,
                            52,
                            98,
                            100,
                            100,
                            46,
                            100,
                            101,
                            118,
                            110,
                            101,
                            116,
                            46,
                            115,
                            117,
                            105,
                            46,
                            105,
                            111,
                            145,
                            2,
                            31,
                            145,
                        ],
                        "worker_address": [
                            53,
                            30,
                            101,
                            119,
                            114,
                            45,
                            115,
                            117,
                            105,
                            118,
                            97,
                            108,
                            45,
                            97,
                            52,
                            98,
                            100,
                            100,
                            46,
                            100,
                            101,
                            118,
                            110,
                            101,
                            116,
                            46,
                            115,
                            117,
                            105,
                            46,
                            105,
                            111,
                            145,
                            2,
                            31,
                            146,
                        ],
                        "next_epoch_stake": 10222176,
                        "next_epoch_delegation": 30019853,
                        "next_epoch_gas_price": 1,
                        "next_epoch_commission_rate": 0,
                    },
                    "voting_power": 2500,
                    "stake_amount": 10222176,
                    "pending_stake": 0,
                    "pending_withdraw": 0,
                    "gas_price": 1,
                    "delegation_staking_pool": {
                        "validator_address": "0x339383679a0412216560c564debefc2eed8d9fb3",
                        "starting_epoch": 1,
                        "sui_balance": 30019853,
                        "rewards_pool": {"value": 0},
                        "delegation_token_supply": {"value": 30019853},
                        "pending_delegations": {
                            "id": "0xd5d9aa879b78dc1f516d71ab979189086eff752f",
                            "size": 0,
                            "head": {"vec": []},
                            "tail": {"vec": []},
                        },
                        "pending_withdraws": {
                            "contents": {"id": "0xab8235dace3d68c7fb48110d63cbf4d6fd81ce10", "size": 0}
                        },
                    },
                    "commission_rate": 0,
                },
                {
                    "metadata": {
                        "sui_address": "0x03a3d77a605ff1de68906262f3ca2944cf9d9306",
                        "pubkey_bytes": [
                            135,
                            189,
                            108,
                            80,
                            113,
                            120,
                            132,
                            48,
                            163,
                            202,
                            178,
                            160,
                            205,
                            67,
                            42,
                            142,
                            50,
                            90,
                            191,
                            126,
                            104,
                            242,
                            111,
                            156,
                            72,
                            109,
                            105,
                            112,
                            6,
                            129,
                            45,
                            252,
                            192,
                            158,
                            180,
                            169,
                            80,
                            230,
                            31,
                            31,
                            183,
                            40,
                            52,
                            89,
                            164,
                            122,
                            164,
                            209,
                            5,
                            225,
                            253,
                            65,
                            186,
                            207,
                            123,
                            7,
                            130,
                            20,
                            233,
                            194,
                            97,
                            181,
                            44,
                            36,
                            148,
                            245,
                            51,
                            232,
                            213,
                            190,
                            128,
                            137,
                            151,
                            220,
                            16,
                            55,
                            51,
                            108,
                            113,
                            203,
                            6,
                            68,
                            31,
                            92,
                            246,
                            139,
                            16,
                            186,
                            65,
                            70,
                            244,
                            135,
                            62,
                            89,
                            217,
                            58,
                        ],
                        "network_pubkey_bytes": [
                            124,
                            240,
                            215,
                            244,
                            25,
                            197,
                            85,
                            26,
                            245,
                            155,
                            102,
                            149,
                            240,
                            131,
                            58,
                            223,
                            252,
                            135,
                            39,
                            246,
                            169,
                            200,
                            165,
                            91,
                            177,
                            103,
                            62,
                            188,
                            12,
                            45,
                            228,
                            40,
                        ],
                        "worker_pubkey_bytes": [
                            16,
                            107,
                            83,
                            4,
                            228,
                            224,
                            137,
                            21,
                            202,
                            251,
                            187,
                            35,
                            23,
                            248,
                            138,
                            138,
                            222,
                            86,
                            226,
                            251,
                            171,
                            125,
                            211,
                            165,
                            2,
                            97,
                            19,
                            198,
                            205,
                            225,
                            69,
                            200,
                        ],
                        "proof_of_possession_bytes": [
                            136,
                            48,
                            220,
                            177,
                            58,
                            119,
                            225,
                            254,
                            138,
                            218,
                            229,
                            15,
                            25,
                            198,
                            136,
                            153,
                            183,
                            94,
                            157,
                            195,
                            45,
                            234,
                            178,
                            245,
                            199,
                            136,
                            107,
                            56,
                            193,
                            12,
                            157,
                            248,
                            22,
                            94,
                            96,
                            34,
                            165,
                            132,
                            113,
                            105,
                            207,
                            105,
                            228,
                            165,
                            194,
                            1,
                            151,
                            130,
                        ],
                        "name": [118, 97, 108, 105, 100, 97, 116, 111, 114, 45, 48],
                        "description": [],
                        "image_url": [],
                        "project_url": [],
                        "net_address": [
                            53,
                            30,
                            101,
                            119,
                            114,
                            45,
                            115,
                            117,
                            105,
                            118,
                            97,
                            108,
                            45,
                            102,
                            100,
                            99,
                            51,
                            51,
                            46,
                            100,
                            101,
                            118,
                            110,
                            101,
                            116,
                            46,
                            115,
                            117,
                            105,
                            46,
                            105,
                            111,
                            6,
                            31,
                            144,
                            224,
                            3,
                        ],
                        "consensus_address": [
                            53,
                            30,
                            101,
                            119,
                            114,
                            45,
                            115,
                            117,
                            105,
                            118,
                            97,
                            108,
                            45,
                            102,
                            100,
                            99,
                            51,
                            51,
                            46,
                            100,
                            101,
                            118,
                            110,
                            101,
                            116,
                            46,
                            115,
                            117,
                            105,
                            46,
                            105,
                            111,
                            145,
                            2,
                            31,
                            145,
                        ],
                        "worker_address": [
                            53,
                            30,
                            101,
                            119,
                            114,
                            45,
                            115,
                            117,
                            105,
                            118,
                            97,
                            108,
                            45,
                            102,
                            100,
                            99,
                            51,
                            51,
                            46,
                            100,
                            101,
                            118,
                            110,
                            101,
                            116,
                            46,
                            115,
                            117,
                            105,
                            46,
                            105,
                            111,
                            145,
                            2,
                            31,
                            146,
                        ],
                        "next_epoch_stake": 10222176,
                        "next_epoch_delegation": 20003939,
                        "next_epoch_gas_price": 1,
                        "next_epoch_commission_rate": 0,
                    },
                    "voting_power": 2500,
                    "stake_amount": 10222176,
                    "pending_stake": 0,
                    "pending_withdraw": 0,
                    "gas_price": 1,
                    "delegation_staking_pool": {
                        "validator_address": "0x03a3d77a605ff1de68906262f3ca2944cf9d9306",
                        "starting_epoch": 1,
                        "sui_balance": 2894,
                        "rewards_pool": {"value": 0},
                        "delegation_token_supply": {"value": 2894},
                        "pending_delegations": {
                            "id": "0x628ffd0e51e9a6ea32c13c2739a31a8f344b557d",
                            "size": 1046,
                            "head": {"vec": ["0x40336bec425a5649487ddf1c5dad7fe16f72f58b"]},
                            "tail": {"vec": ["0xedfa22c3f037c73cee6124e7ea98027442214b04"]},
                        },
                        "pending_withdraws": {
                            "contents": {"id": "0x1ace65f54d65a96251b3f46bfa720ab65a7ebe01", "size": 0}
                        },
                    },
                    "commission_rate": 0,
                },
                {
                    "metadata": {
                        "sui_address": "0x59c2018fde98241d15763149955f22953f8d85c2",
                        "pubkey_bytes": [
                            151,
                            242,
                            79,
                            22,
                            74,
                            174,
                            238,
                            178,
                            85,
                            55,
                            28,
                            230,
                            109,
                            165,
                            217,
                            20,
                            25,
                            145,
                            163,
                            254,
                            144,
                            12,
                            14,
                            151,
                            128,
                            99,
                            96,
                            194,
                            158,
                            250,
                            64,
                            112,
                            30,
                            13,
                            241,
                            105,
                            31,
                            124,
                            112,
                            140,
                            3,
                            189,
                            192,
                            236,
                            25,
                            219,
                            140,
                            195,
                            22,
                            99,
                            22,
                            37,
                            83,
                            82,
                            166,
                            62,
                            251,
                            213,
                            29,
                            248,
                            30,
                            233,
                            161,
                            124,
                            87,
                            59,
                            246,
                            118,
                            114,
                            26,
                            142,
                            45,
                            185,
                            163,
                            67,
                            205,
                            182,
                            242,
                            166,
                            115,
                            107,
                            176,
                            13,
                            143,
                            134,
                            90,
                            232,
                            31,
                            58,
                            215,
                            169,
                            196,
                            96,
                            109,
                            241,
                            104,
                        ],
                        "network_pubkey_bytes": [
                            20,
                            175,
                            77,
                            177,
                            105,
                            52,
                            250,
                            74,
                            66,
                            173,
                            175,
                            201,
                            220,
                            90,
                            87,
                            50,
                            185,
                            220,
                            82,
                            206,
                            156,
                            166,
                            40,
                            184,
                            56,
                            202,
                            243,
                            187,
                            249,
                            79,
                            252,
                            223,
                        ],
                        "worker_pubkey_bytes": [
                            85,
                            28,
                            194,
                            197,
                            182,
                            137,
                            21,
                            211,
                            53,
                            50,
                            56,
                            83,
                            253,
                            246,
                            115,
                            49,
                            25,
                            229,
                            154,
                            203,
                            82,
                            175,
                            243,
                            131,
                            27,
                            254,
                            110,
                            35,
                            148,
                            223,
                            2,
                            16,
                        ],
                        "proof_of_possession_bytes": [
                            148,
                            199,
                            0,
                            160,
                            39,
                            38,
                            161,
                            146,
                            255,
                            172,
                            156,
                            162,
                            26,
                            217,
                            228,
                            90,
                            110,
                            183,
                            176,
                            156,
                            245,
                            29,
                            0,
                            255,
                            132,
                            249,
                            151,
                            12,
                            229,
                            251,
                            60,
                            12,
                            2,
                            58,
                            97,
                            71,
                            161,
                            91,
                            134,
                            22,
                            45,
                            189,
                            117,
                            131,
                            193,
                            212,
                            190,
                            4,
                        ],
                        "name": [118, 97, 108, 105, 100, 97, 116, 111, 114, 45, 49],
                        "description": [],
                        "image_url": [],
                        "project_url": [],
                        "net_address": [
                            53,
                            30,
                            101,
                            119,
                            114,
                            45,
                            115,
                            117,
                            105,
                            118,
                            97,
                            108,
                            45,
                            51,
                            54,
                            49,
                            54,
                            51,
                            46,
                            100,
                            101,
                            118,
                            110,
                            101,
                            116,
                            46,
                            115,
                            117,
                            105,
                            46,
                            105,
                            111,
                            6,
                            31,
                            144,
                            224,
                            3,
                        ],
                        "consensus_address": [
                            53,
                            30,
                            101,
                            119,
                            114,
                            45,
                            115,
                            117,
                            105,
                            118,
                            97,
                            108,
                            45,
                            51,
                            54,
                            49,
                            54,
                            51,
                            46,
                            100,
                            101,
                            118,
                            110,
                            101,
                            116,
                            46,
                            115,
                            117,
                            105,
                            46,
                            105,
                            111,
                            145,
                            2,
                            31,
                            145,
                        ],
                        "worker_address": [
                            53,
                            30,
                            101,
                            119,
                            114,
                            45,
                            115,
                            117,
                            105,
                            118,
                            97,
                            108,
                            45,
                            51,
                            54,
                            49,
                            54,
                            51,
                            46,
                            100,
                            101,
                            118,
                            110,
                            101,
                            116,
                            46,
                            115,
                            117,
                            105,
                            46,
                            105,
                            111,
                            145,
                            2,
                            31,
                            146,
                        ],
                        "next_epoch_stake": 10222176,
                        "next_epoch_delegation": 0,
                        "next_epoch_gas_price": 1,
                        "next_epoch_commission_rate": 0,
                    },
                    "voting_power": 2500,
                    "stake_amount": 10222176,
                    "pending_stake": 0,
                    "pending_withdraw": 0,
                    "gas_price": 1,
                    "delegation_staking_pool": {
                        "validator_address": "0x59c2018fde98241d15763149955f22953f8d85c2",
                        "starting_epoch": 1,
                        "sui_balance": 0,
                        "rewards_pool": {"value": 0},
                        "delegation_token_supply": {"value": 0},
                        "pending_delegations": {
                            "id": "0x6d3ffc5213ed4df6802cd4535d3c18f66d85bab5",
                            "size": 0,
                            "head": {"vec": []},
                            "tail": {"vec": []},
                        },
                        "pending_withdraws": {
                            "contents": {"id": "0x2cd564ff647db701afe7b1e8a3f1a31bc071fd0b", "size": 0}
                        },
                    },
                    "commission_rate": 0,
                },
                {
                    "metadata": {
                        "sui_address": "0x0576bb66d007548916a238cd87691483f8deb41d",
                        "pubkey_bytes": [
                            168,
                            30,
                            174,
                            43,
                            96,
                            45,
                            101,
                            105,
                            40,
                            240,
                            51,
                            208,
                            138,
                            169,
                            218,
                            9,
                            0,
                            212,
                            11,
                            20,
                            26,
                            117,
                            244,
                            68,
                            66,
                            99,
                            234,
                            92,
                            121,
                            62,
                            29,
                            203,
                            126,
                            217,
                            148,
                            116,
                            226,
                            207,
                            33,
                            209,
                            231,
                            195,
                            53,
                            187,
                            132,
                            98,
                            197,
                            186,
                            11,
                            167,
                            40,
                            92,
                            76,
                            54,
                            210,
                            202,
                            12,
                            190,
                            109,
                            165,
                            218,
                            238,
                            172,
                            155,
                            189,
                            98,
                            76,
                            71,
                            222,
                            236,
                            58,
                            154,
                            24,
                            94,
                            155,
                            137,
                            57,
                            112,
                            170,
                            75,
                            93,
                            47,
                            252,
                            112,
                            135,
                            65,
                            77,
                            114,
                            252,
                            65,
                            148,
                            75,
                            163,
                            104,
                            150,
                            237,
                        ],
                        "network_pubkey_bytes": [
                            107,
                            41,
                            113,
                            235,
                            230,
                            243,
                            7,
                            97,
                            5,
                            148,
                            70,
                            66,
                            255,
                            160,
                            254,
                            53,
                            136,
                            182,
                            185,
                            235,
                            99,
                            40,
                            7,
                            182,
                            68,
                            218,
                            39,
                            8,
                            5,
                            143,
                            49,
                            210,
                        ],
                        "worker_pubkey_bytes": [
                            164,
                            198,
                            102,
                            5,
                            206,
                            106,
                            185,
                            126,
                            46,
                            178,
                            19,
                            128,
                            167,
                            124,
                            184,
                            255,
                            216,
                            222,
                            38,
                            186,
                            72,
                            228,
                            64,
                            238,
                            195,
                            234,
                            204,
                            3,
                            97,
                            95,
                            225,
                            117,
                        ],
                        "proof_of_possession_bytes": [
                            178,
                            233,
                            46,
                            117,
                            150,
                            65,
                            0,
                            238,
                            119,
                            176,
                            20,
                            88,
                            179,
                            6,
                            175,
                            193,
                            17,
                            144,
                            55,
                            218,
                            67,
                            251,
                            82,
                            122,
                            48,
                            223,
                            72,
                            193,
                            49,
                            213,
                            93,
                            20,
                            105,
                            240,
                            231,
                            89,
                            30,
                            32,
                            121,
                            35,
                            155,
                            4,
                            108,
                            249,
                            37,
                            220,
                            191,
                            165,
                        ],
                        "name": [118, 97, 108, 105, 100, 97, 116, 111, 114, 45, 51],
                        "description": [],
                        "image_url": [],
                        "project_url": [],
                        "net_address": [
                            53,
                            30,
                            101,
                            119,
                            114,
                            45,
                            115,
                            117,
                            105,
                            118,
                            97,
                            108,
                            45,
                            100,
                            98,
                            56,
                            51,
                            103,
                            46,
                            100,
                            101,
                            118,
                            110,
                            101,
                            116,
                            46,
                            115,
                            117,
                            105,
                            46,
                            105,
                            111,
                            6,
                            31,
                            144,
                            224,
                            3,
                        ],
                        "consensus_address": [
                            53,
                            30,
                            101,
                            119,
                            114,
                            45,
                            115,
                            117,
                            105,
                            118,
                            97,
                            108,
                            45,
                            100,
                            98,
                            56,
                            51,
                            103,
                            46,
                            100,
                            101,
                            118,
                            110,
                            101,
                            116,
                            46,
                            115,
                            117,
                            105,
                            46,
                            105,
                            111,
                            145,
                            2,
                            31,
                            145,
                        ],
                        "worker_address": [
                            53,
                            30,
                            101,
                            119,
                            114,
                            45,
                            115,
                            117,
                            105,
                            118,
                            97,
                            108,
                            45,
                            100,
                            98,
                            56,
                            51,
                            103,
                            46,
                            100,
                            101,
                            118,
                            110,
                            101,
                            116,
                            46,
                            115,
                            117,
                            105,
                            46,
                            105,
                            111,
                            145,
                            2,
                            31,
                            146,
                        ],
                        "next_epoch_stake": 10222176,
                        "next_epoch_delegation": 0,
                        "next_epoch_gas_price": 1,
                        "next_epoch_commission_rate": 0,
                    },
                    "voting_power": 2500,
                    "stake_amount": 10222176,
                    "pending_stake": 0,
                    "pending_withdraw": 0,
                    "gas_price": 1,
                    "delegation_staking_pool": {
                        "validator_address": "0x0576bb66d007548916a238cd87691483f8deb41d",
                        "starting_epoch": 1,
                        "sui_balance": 0,
                        "rewards_pool": {"value": 0},
                        "delegation_token_supply": {"value": 0},
                        "pending_delegations": {
                            "id": "0x01b3b1dd18a3b775fe0e0d4b873c0aa0d0cd2acf",
                            "size": 0,
                            "head": {"vec": []},
                            "tail": {"vec": []},
                        },
                        "pending_withdraws": {
                            "contents": {"id": "0x3c2b307c3239f61643af5e9a09d7d0c95bfe14dc", "size": 0}
                        },
                    },
                    "commission_rate": 0,
                },
            ],
            "pending_validators": [],
            "pending_removals": [],
            "next_epoch_validators": [
                {
                    "sui_address": "0x0576bb66d007548916a238cd87691483f8deb41d",
                    "pubkey_bytes": [
                        168,
                        30,
                        174,
                        43,
                        96,
                        45,
                        101,
                        105,
                        40,
                        240,
                        51,
                        208,
                        138,
                        169,
                        218,
                        9,
                        0,
                        212,
                        11,
                        20,
                        26,
                        117,
                        244,
                        68,
                        66,
                        99,
                        234,
                        92,
                        121,
                        62,
                        29,
                        203,
                        126,
                        217,
                        148,
                        116,
                        226,
                        207,
                        33,
                        209,
                        231,
                        195,
                        53,
                        187,
                        132,
                        98,
                        197,
                        186,
                        11,
                        167,
                        40,
                        92,
                        76,
                        54,
                        210,
                        202,
                        12,
                        190,
                        109,
                        165,
                        218,
                        238,
                        172,
                        155,
                        189,
                        98,
                        76,
                        71,
                        222,
                        236,
                        58,
                        154,
                        24,
                        94,
                        155,
                        137,
                        57,
                        112,
                        170,
                        75,
                        93,
                        47,
                        252,
                        112,
                        135,
                        65,
                        77,
                        114,
                        252,
                        65,
                        148,
                        75,
                        163,
                        104,
                        150,
                        237,
                    ],
                    "network_pubkey_bytes": [
                        107,
                        41,
                        113,
                        235,
                        230,
                        243,
                        7,
                        97,
                        5,
                        148,
                        70,
                        66,
                        255,
                        160,
                        254,
                        53,
                        136,
                        182,
                        185,
                        235,
                        99,
                        40,
                        7,
                        182,
                        68,
                        218,
                        39,
                        8,
                        5,
                        143,
                        49,
                        210,
                    ],
                    "worker_pubkey_bytes": [
                        164,
                        198,
                        102,
                        5,
                        206,
                        106,
                        185,
                        126,
                        46,
                        178,
                        19,
                        128,
                        167,
                        124,
                        184,
                        255,
                        216,
                        222,
                        38,
                        186,
                        72,
                        228,
                        64,
                        238,
                        195,
                        234,
                        204,
                        3,
                        97,
                        95,
                        225,
                        117,
                    ],
                    "proof_of_possession_bytes": [
                        178,
                        233,
                        46,
                        117,
                        150,
                        65,
                        0,
                        238,
                        119,
                        176,
                        20,
                        88,
                        179,
                        6,
                        175,
                        193,
                        17,
                        144,
                        55,
                        218,
                        67,
                        251,
                        82,
                        122,
                        48,
                        223,
                        72,
                        193,
                        49,
                        213,
                        93,
                        20,
                        105,
                        240,
                        231,
                        89,
                        30,
                        32,
                        121,
                        35,
                        155,
                        4,
                        108,
                        249,
                        37,
                        220,
                        191,
                        165,
                    ],
                    "name": [118, 97, 108, 105, 100, 97, 116, 111, 114, 45, 51],
                    "description": [],
                    "image_url": [],
                    "project_url": [],
                    "net_address": [
                        53,
                        30,
                        101,
                        119,
                        114,
                        45,
                        115,
                        117,
                        105,
                        118,
                        97,
                        108,
                        45,
                        100,
                        98,
                        56,
                        51,
                        103,
                        46,
                        100,
                        101,
                        118,
                        110,
                        101,
                        116,
                        46,
                        115,
                        117,
                        105,
                        46,
                        105,
                        111,
                        6,
                        31,
                        144,
                        224,
                        3,
                    ],
                    "consensus_address": [
                        53,
                        30,
                        101,
                        119,
                        114,
                        45,
                        115,
                        117,
                        105,
                        118,
                        97,
                        108,
                        45,
                        100,
                        98,
                        56,
                        51,
                        103,
                        46,
                        100,
                        101,
                        118,
                        110,
                        101,
                        116,
                        46,
                        115,
                        117,
                        105,
                        46,
                        105,
                        111,
                        145,
                        2,
                        31,
                        145,
                    ],
                    "worker_address": [
                        53,
                        30,
                        101,
                        119,
                        114,
                        45,
                        115,
                        117,
                        105,
                        118,
                        97,
                        108,
                        45,
                        100,
                        98,
                        56,
                        51,
                        103,
                        46,
                        100,
                        101,
                        118,
                        110,
                        101,
                        116,
                        46,
                        115,
                        117,
                        105,
                        46,
                        105,
                        111,
                        145,
                        2,
                        31,
                        146,
                    ],
                    "next_epoch_stake": 10222176,
                    "next_epoch_delegation": 0,
                    "next_epoch_gas_price": 1,
                    "next_epoch_commission_rate": 0,
                },
                {
                    "sui_address": "0x59c2018fde98241d15763149955f22953f8d85c2",
                    "pubkey_bytes": [
                        151,
                        242,
                        79,
                        22,
                        74,
                        174,
                        238,
                        178,
                        85,
                        55,
                        28,
                        230,
                        109,
                        165,
                        217,
                        20,
                        25,
                        145,
                        163,
                        254,
                        144,
                        12,
                        14,
                        151,
                        128,
                        99,
                        96,
                        194,
                        158,
                        250,
                        64,
                        112,
                        30,
                        13,
                        241,
                        105,
                        31,
                        124,
                        112,
                        140,
                        3,
                        189,
                        192,
                        236,
                        25,
                        219,
                        140,
                        195,
                        22,
                        99,
                        22,
                        37,
                        83,
                        82,
                        166,
                        62,
                        251,
                        213,
                        29,
                        248,
                        30,
                        233,
                        161,
                        124,
                        87,
                        59,
                        246,
                        118,
                        114,
                        26,
                        142,
                        45,
                        185,
                        163,
                        67,
                        205,
                        182,
                        242,
                        166,
                        115,
                        107,
                        176,
                        13,
                        143,
                        134,
                        90,
                        232,
                        31,
                        58,
                        215,
                        169,
                        196,
                        96,
                        109,
                        241,
                        104,
                    ],
                    "network_pubkey_bytes": [
                        20,
                        175,
                        77,
                        177,
                        105,
                        52,
                        250,
                        74,
                        66,
                        173,
                        175,
                        201,
                        220,
                        90,
                        87,
                        50,
                        185,
                        220,
                        82,
                        206,
                        156,
                        166,
                        40,
                        184,
                        56,
                        202,
                        243,
                        187,
                        249,
                        79,
                        252,
                        223,
                    ],
                    "worker_pubkey_bytes": [
                        85,
                        28,
                        194,
                        197,
                        182,
                        137,
                        21,
                        211,
                        53,
                        50,
                        56,
                        83,
                        253,
                        246,
                        115,
                        49,
                        25,
                        229,
                        154,
                        203,
                        82,
                        175,
                        243,
                        131,
                        27,
                        254,
                        110,
                        35,
                        148,
                        223,
                        2,
                        16,
                    ],
                    "proof_of_possession_bytes": [
                        148,
                        199,
                        0,
                        160,
                        39,
                        38,
                        161,
                        146,
                        255,
                        172,
                        156,
                        162,
                        26,
                        217,
                        228,
                        90,
                        110,
                        183,
                        176,
                        156,
                        245,
                        29,
                        0,
                        255,
                        132,
                        249,
                        151,
                        12,
                        229,
                        251,
                        60,
                        12,
                        2,
                        58,
                        97,
                        71,
                        161,
                        91,
                        134,
                        22,
                        45,
                        189,
                        117,
                        131,
                        193,
                        212,
                        190,
                        4,
                    ],
                    "name": [118, 97, 108, 105, 100, 97, 116, 111, 114, 45, 49],
                    "description": [],
                    "image_url": [],
                    "project_url": [],
                    "net_address": [
                        53,
                        30,
                        101,
                        119,
                        114,
                        45,
                        115,
                        117,
                        105,
                        118,
                        97,
                        108,
                        45,
                        51,
                        54,
                        49,
                        54,
                        51,
                        46,
                        100,
                        101,
                        118,
                        110,
                        101,
                        116,
                        46,
                        115,
                        117,
                        105,
                        46,
                        105,
                        111,
                        6,
                        31,
                        144,
                        224,
                        3,
                    ],
                    "consensus_address": [
                        53,
                        30,
                        101,
                        119,
                        114,
                        45,
                        115,
                        117,
                        105,
                        118,
                        97,
                        108,
                        45,
                        51,
                        54,
                        49,
                        54,
                        51,
                        46,
                        100,
                        101,
                        118,
                        110,
                        101,
                        116,
                        46,
                        115,
                        117,
                        105,
                        46,
                        105,
                        111,
                        145,
                        2,
                        31,
                        145,
                    ],
                    "worker_address": [
                        53,
                        30,
                        101,
                        119,
                        114,
                        45,
                        115,
                        117,
                        105,
                        118,
                        97,
                        108,
                        45,
                        51,
                        54,
                        49,
                        54,
                        51,
                        46,
                        100,
                        101,
                        118,
                        110,
                        101,
                        116,
                        46,
                        115,
                        117,
                        105,
                        46,
                        105,
                        111,
                        145,
                        2,
                        31,
                        146,
                    ],
                    "next_epoch_stake": 10222176,
                    "next_epoch_delegation": 0,
                    "next_epoch_gas_price": 1,
                    "next_epoch_commission_rate": 0,
                },
                {
                    "sui_address": "0x03a3d77a605ff1de68906262f3ca2944cf9d9306",
                    "pubkey_bytes": [
                        135,
                        189,
                        108,
                        80,
                        113,
                        120,
                        132,
                        48,
                        163,
                        202,
                        178,
                        160,
                        205,
                        67,
                        42,
                        142,
                        50,
                        90,
                        191,
                        126,
                        104,
                        242,
                        111,
                        156,
                        72,
                        109,
                        105,
                        112,
                        6,
                        129,
                        45,
                        252,
                        192,
                        158,
                        180,
                        169,
                        80,
                        230,
                        31,
                        31,
                        183,
                        40,
                        52,
                        89,
                        164,
                        122,
                        164,
                        209,
                        5,
                        225,
                        253,
                        65,
                        186,
                        207,
                        123,
                        7,
                        130,
                        20,
                        233,
                        194,
                        97,
                        181,
                        44,
                        36,
                        148,
                        245,
                        51,
                        232,
                        213,
                        190,
                        128,
                        137,
                        151,
                        220,
                        16,
                        55,
                        51,
                        108,
                        113,
                        203,
                        6,
                        68,
                        31,
                        92,
                        246,
                        139,
                        16,
                        186,
                        65,
                        70,
                        244,
                        135,
                        62,
                        89,
                        217,
                        58,
                    ],
                    "network_pubkey_bytes": [
                        124,
                        240,
                        215,
                        244,
                        25,
                        197,
                        85,
                        26,
                        245,
                        155,
                        102,
                        149,
                        240,
                        131,
                        58,
                        223,
                        252,
                        135,
                        39,
                        246,
                        169,
                        200,
                        165,
                        91,
                        177,
                        103,
                        62,
                        188,
                        12,
                        45,
                        228,
                        40,
                    ],
                    "worker_pubkey_bytes": [
                        16,
                        107,
                        83,
                        4,
                        228,
                        224,
                        137,
                        21,
                        202,
                        251,
                        187,
                        35,
                        23,
                        248,
                        138,
                        138,
                        222,
                        86,
                        226,
                        251,
                        171,
                        125,
                        211,
                        165,
                        2,
                        97,
                        19,
                        198,
                        205,
                        225,
                        69,
                        200,
                    ],
                    "proof_of_possession_bytes": [
                        136,
                        48,
                        220,
                        177,
                        58,
                        119,
                        225,
                        254,
                        138,
                        218,
                        229,
                        15,
                        25,
                        198,
                        136,
                        153,
                        183,
                        94,
                        157,
                        195,
                        45,
                        234,
                        178,
                        245,
                        199,
                        136,
                        107,
                        56,
                        193,
                        12,
                        157,
                        248,
                        22,
                        94,
                        96,
                        34,
                        165,
                        132,
                        113,
                        105,
                        207,
                        105,
                        228,
                        165,
                        194,
                        1,
                        151,
                        130,
                    ],
                    "name": [118, 97, 108, 105, 100, 97, 116, 111, 114, 45, 48],
                    "description": [],
                    "image_url": [],
                    "project_url": [],
                    "net_address": [
                        53,
                        30,
                        101,
                        119,
                        114,
                        45,
                        115,
                        117,
                        105,
                        118,
                        97,
                        108,
                        45,
                        102,
                        100,
                        99,
                        51,
                        51,
                        46,
                        100,
                        101,
                        118,
                        110,
                        101,
                        116,
                        46,
                        115,
                        117,
                        105,
                        46,
                        105,
                        111,
                        6,
                        31,
                        144,
                        224,
                        3,
                    ],
                    "consensus_address": [
                        53,
                        30,
                        101,
                        119,
                        114,
                        45,
                        115,
                        117,
                        105,
                        118,
                        97,
                        108,
                        45,
                        102,
                        100,
                        99,
                        51,
                        51,
                        46,
                        100,
                        101,
                        118,
                        110,
                        101,
                        116,
                        46,
                        115,
                        117,
                        105,
                        46,
                        105,
                        111,
                        145,
                        2,
                        31,
                        145,
                    ],
                    "worker_address": [
                        53,
                        30,
                        101,
                        119,
                        114,
                        45,
                        115,
                        117,
                        105,
                        118,
                        97,
                        108,
                        45,
                        102,
                        100,
                        99,
                        51,
                        51,
                        46,
                        100,
                        101,
                        118,
                        110,
                        101,
                        116,
                        46,
                        115,
                        117,
                        105,
                        46,
                        105,
                        111,
                        145,
                        2,
                        31,
                        146,
                    ],
                    "next_epoch_stake": 10222176,
                    "next_epoch_delegation": 20003939,
                    "next_epoch_gas_price": 1,
                    "next_epoch_commission_rate": 0,
                },
                {
                    "sui_address": "0x339383679a0412216560c564debefc2eed8d9fb3",
                    "pubkey_bytes": [
                        129,
                        59,
                        150,
                        147,
                        19,
                        134,
                        151,
                        242,
                        174,
                        81,
                        217,
                        181,
                        239,
                        102,
                        78,
                        93,
                        157,
                        104,
                        165,
                        41,
                        99,
                        247,
                        63,
                        114,
                        164,
                        227,
                        222,
                        13,
                        67,
                        22,
                        193,
                        56,
                        185,
                        244,
                        55,
                        237,
                        71,
                        156,
                        216,
                        160,
                        164,
                        81,
                        220,
                        17,
                        238,
                        25,
                        226,
                        48,
                        11,
                        113,
                        40,
                        126,
                        243,
                        98,
                        37,
                        221,
                        221,
                        232,
                        88,
                        150,
                        104,
                        205,
                        110,
                        208,
                        77,
                        82,
                        79,
                        43,
                        145,
                        210,
                        84,
                        62,
                        158,
                        210,
                        129,
                        1,
                        19,
                        91,
                        13,
                        2,
                        84,
                        111,
                        202,
                        60,
                        225,
                        71,
                        104,
                        118,
                        16,
                        212,
                        44,
                        225,
                        34,
                        218,
                        176,
                        245,
                    ],
                    "network_pubkey_bytes": [
                        222,
                        134,
                        66,
                        194,
                        126,
                        108,
                        36,
                        64,
                        122,
                        168,
                        220,
                        117,
                        151,
                        240,
                        193,
                        83,
                        179,
                        205,
                        91,
                        21,
                        142,
                        182,
                        247,
                        176,
                        193,
                        51,
                        183,
                        7,
                        157,
                        94,
                        150,
                        235,
                    ],
                    "worker_pubkey_bytes": [
                        174,
                        23,
                        52,
                        103,
                        29,
                        68,
                        228,
                        77,
                        42,
                        162,
                        133,
                        58,
                        231,
                        37,
                        223,
                        122,
                        186,
                        231,
                        152,
                        217,
                        251,
                        161,
                        72,
                        31,
                        118,
                        182,
                        10,
                        196,
                        0,
                        41,
                        122,
                        222,
                    ],
                    "proof_of_possession_bytes": [
                        172,
                        148,
                        52,
                        79,
                        76,
                        215,
                        22,
                        131,
                        68,
                        4,
                        59,
                        184,
                        155,
                        72,
                        153,
                        68,
                        147,
                        253,
                        54,
                        155,
                        68,
                        79,
                        243,
                        210,
                        189,
                        90,
                        216,
                        107,
                        157,
                        10,
                        82,
                        157,
                        85,
                        210,
                        40,
                        35,
                        180,
                        48,
                        226,
                        50,
                        137,
                        246,
                        12,
                        193,
                        237,
                        2,
                        148,
                        197,
                    ],
                    "name": [118, 97, 108, 105, 100, 97, 116, 111, 114, 45, 50],
                    "description": [],
                    "image_url": [],
                    "project_url": [],
                    "net_address": [
                        53,
                        30,
                        101,
                        119,
                        114,
                        45,
                        115,
                        117,
                        105,
                        118,
                        97,
                        108,
                        45,
                        97,
                        52,
                        98,
                        100,
                        100,
                        46,
                        100,
                        101,
                        118,
                        110,
                        101,
                        116,
                        46,
                        115,
                        117,
                        105,
                        46,
                        105,
                        111,
                        6,
                        31,
                        144,
                        224,
                        3,
                    ],
                    "consensus_address": [
                        53,
                        30,
                        101,
                        119,
                        114,
                        45,
                        115,
                        117,
                        105,
                        118,
                        97,
                        108,
                        45,
                        97,
                        52,
                        98,
                        100,
                        100,
                        46,
                        100,
                        101,
                        118,
                        110,
                        101,
                        116,
                        46,
                        115,
                        117,
                        105,
                        46,
                        105,
                        111,
                        145,
                        2,
                        31,
                        145,
                    ],
                    "worker_address": [
                        53,
                        30,
                        101,
                        119,
                        114,
                        45,
                        115,
                        117,
                        105,
                        118,
                        97,
                        108,
                        45,
                        97,
                        52,
                        98,
                        100,
                        100,
                        46,
                        100,
                        101,
                        118,
                        110,
                        101,
                        116,
                        46,
                        115,
                        117,
                        105,
                        46,
                        105,
                        111,
                        145,
                        2,
                        31,
                        146,
                    ],
                    "next_epoch_stake": 10222176,
                    "next_epoch_delegation": 30019853,
                    "next_epoch_gas_price": 1,
                    "next_epoch_commission_rate": 0,
                },
            ],
            "pending_delegation_switches": {"contents": []},
        },
        "treasury_cap": {"value": 5},
        "storage_fund": {"value": 2145656},
        "parameters": {"min_validator_stake": 1, "max_validator_candidate_count": 100},
        "reference_gas_price": 1,
        "validator_report_records": {"contents": []},
        "stake_subsidy": {"epoch_counter": 0, "balance": {"value": 0}, "current_epoch_amount": 1000000},
        "safe_mode": False,
        "epoch_start_timestamp_ms": 1674679402908,
    }
