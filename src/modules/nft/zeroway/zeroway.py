import random

from eth_typing import HexStr
from web3.contract import Contract
from web3.types import TxParams

from src.utils.abc.abstract_mint_and_bridge import ABCMintBridge

from src.utils.data.contracts import contracts


class ZeroWay(ABCMintBridge):
    def __init__(
            self,
            private_key: str,
            from_chain: str | list[str],
            to_chain: str | list[str],
    ):
        while True:
            if isinstance(from_chain, list):
                self.from_chain = random.choice(from_chain)
            elif isinstance(from_chain, str):
                self.from_chain = from_chain
            else:
                raise ValueError(f'from_chain must be str or list[str]. Got {type(from_chain)}')

            if isinstance(to_chain, list):
                self.to_chain = random.choice(to_chain)
            elif isinstance(to_chain, str):
                self.to_chain = to_chain
            else:
                raise ValueError(f'to_chain must be str or list[str]. Got {type(to_chain)}')

            if self.from_chain == self.to_chain:
                continue
            break

        contract_address = contracts['zeroway'][self.from_chain.lower()]

        super().__init__(
            private_key=private_key,
            from_chain=from_chain,
            to_chain=to_chain,
            contract_address=contract_address,
            name='zeroway'
        )

    def __str__(self) -> None:
        return f'{self.__class__.__name__} | {self.from_chain.upper()} => {self.to_chain.upper()} | [{self.wallet_address}]'

    async def create_mint_transaction(self, contract: Contract) -> TxParams:
        fee = await contract.functions.mintFee().call()

        tx = await contract.functions.mint(
            self.wallet_address
        ).build_transaction({
            "chainId": await self.web3.eth.chain_id,
            "from": self.wallet_address,
            "nonce": await self.web3.eth.get_transaction_count(self.wallet_address),
            'gasPrice': await self.web3.eth.gas_price,
            "value": fee
        })
        return tx

    async def get_nft_id(self, tx_hash: HexStr) -> int:
        receipt = await self.web3.eth.get_transaction_receipt(tx_hash)
        logs = receipt.get('logs')
        mint_id_hex = (logs[0]['topics'][3]).hex()
        mint_id = int(mint_id_hex, 16)
        return mint_id

    async def create_bridge_transaction(self, contract: Contract, nft_id: int) -> TxParams:
        fee = await contract.functions.calculateBridgeFee(
            nft_id,
            self.domains_mapping[self.to_chain.lower()]
        ).call()

        tx = await contract.functions.bridge(
            nft_id,
            self.domains_mapping[self.to_chain.lower()],
        ).build_transaction({
            "chainId": await self.web3.eth.chain_id,
            "from": self.wallet_address,
            "nonce": await self.web3.eth.get_transaction_count(self.wallet_address),
            'gasPrice': await self.web3.eth.gas_price,
            "value": fee
        })
        return tx
