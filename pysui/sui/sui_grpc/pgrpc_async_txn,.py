#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Pysui Transaction builder that leverages Sui gRPC."""

from typing import Optional, Union
from pysui.sui.sui_common.trxn_base import _SuiTransactionBase as txbase
import pysui.sui.sui_pgql.pgql_types as pgql_type
from pysui.sui.sui_bcs import bcs
import pysui.sui.sui_pgql.pgql_validators as tv
import pysui.sui.sui_grpc.pgrpc_requests as rn
from pysui.sui.sui_common.async_funcs import AsyncLRU

# TODO: gRPC argbase implementation
import pysui.sui.sui_grpc.pgrpc_txn_async_argb as argbase

# TODO: gRPC gas implementation
import pysui.sui.sui_grpc.pgrpc_txb_gas as gd
import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2beta as v2base


class AsyncSuiTransaction(txbase):
    """."""

    _BUILD_BYTE_STR: str = "tx_bytestr"
    _SIG_ARRAY: str = "sig_array"

    def __init__(
        self,
        **kwargs,
    ) -> None:
        """__init__ Initialize the asynchronous SuiTransaction.

        :param client: The asynchronous SuiGQLClient
        :type client: AsyncSuiGQLClient
        :param initial_sender: The address of the sender of the transaction, defaults to None
        :type initial_sender: Union[str, SigningMultiSig], optional
        :param compress_inputs: Reuse identical inputs, defaults to False
        :type compress_inputs: bool,optional
        :param merge_gas_budget: If True will take available gas not in use for paying for transaction, defaults to False
        :type merge_gas_budget: bool, optional
        """
        super().__init__(**kwargs)
        self._argparse = argbase.AsyncResolvingArgParser(self.client)

    @AsyncLRU(maxsize=256)
    async def _function_meta_args(
        self, target: str
    ) -> tuple[bcs.Address, str, str, int, pgql_type.MoveArgSummary]:
        """_function_meta_args Returns the argument summary of a target sui move function

        :param target: The triplet target string
        :type target: str
        :return: The meta function argument summary
        :rtype: pgql_type.MoveArgSummary
        """
        package, package_module, package_function = (
            tv.TypeValidator.check_target_triplet(target)
        )

        result = await self.client.execute(
            request=rn.GetFunction(
                package=package,
                module_name=package_module,
                function_name=package_function,
            )
        )
        if result.is_ok() and not isinstance(result.result_data, pgql_type.NoopGQL):
            mfunc: pgql_type.MoveFunctionGQL = result.result_data
            return (
                bcs.Address.from_str(package),
                package_module,
                package_function,
                len(mfunc.returns),
                mfunc.arg_summary(),
            )
        raise ValueError(f"Unresolvable target {target}")

    async def target_function_summary(
        self, target: str
    ) -> tuple[bcs.Address, str, str, int, pgql_type.MoveArgSummary]:
        """Returns the argument summary of a target sui move function."""
        return await self._function_meta_args(target)

    async def _build_txn_data(
        self,
        gas_budget: str = "",
        use_gas_objects: Optional[list[Union[str, v2base.Object]]] = None,
        txn_expires_after: Optional[int] = None,
    ) -> Union[bcs.TransactionData, ValueError]:
        """Generate the TransactionData structure."""
        obj_in_use: set[str] = set(self.builder.objects_registry.keys())
        tx_kind = self.builder.finish_for_inspect()
        gas_data: bcs.GasData = await gd.async_get_gas_data(
            signing=self.signer_block,
            client=self.client,
            budget=gas_budget if not gas_budget else int(gas_budget),
            use_coins=use_gas_objects,
            objects_in_use=obj_in_use,
            active_gas_price=self.gas_price,
            tx_kind=tx_kind,
        )
        return bcs.TransactionData(
            "V1",
            bcs.TransactionDataV1(
                tx_kind,
                bcs.Address.from_str(self.signer_block.sender_str),
                gas_data,
                bcs.TransactionExpiration(
                    "None"
                    if not txn_expires_after
                    else bcs.TransactionExpiration("Epoch", txn_expires_after)
                ),
            ),
        )
