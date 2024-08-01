import time

from web3 import Web3
from loguru import logger
from config import ERC20_ABI, BASE_ROUTER_ABI, BASE_ROUTER_ADDR, WALLET_ADDRESS


class Pancake:
    def __init__(self, private_key, rpc_url):
        self.sender_address = Web3.to_checksum_address(WALLET_ADDRESS)
        self.router_address = Web3.to_checksum_address(BASE_ROUTER_ADDR)
        self.private_key = private_key
        self.web3 = Web3(Web3.HTTPProvider(rpc_url))

        self.ERC20 = ERC20_ABI

        self.swapRouter = BASE_ROUTER_ABI
        self.router_contract = self.web3.eth.contract(
            address=self.router_address, abi=self.swapRouter)

    def approve_token(self, token_address: str, spender_address: str, amount: int):
        logger.info("Start approve")
        token_contract = self.web3.eth.contract(
            address=token_address, abi=self.ERC20)

        tx_params = {
            "from": self.sender_address,
            "value": 0,
            'nonce': self.web3.eth.get_transaction_count(self.sender_address)
        }

        function = token_contract.functions.approve(spender_address, amount)
        transaction = function.build_transaction(tx_params)
        transaction['gas'] = self.web3.eth.estimate_gas(transaction)
        sign_tr = self.web3.eth.account.sign_transaction(
            transaction, self.private_key)
        sent_tr = self.web3.eth.send_raw_transaction(sign_tr.rawTransaction)
        logger.info("Approve success")

        return sent_tr

    def get_approve(self, token_address: str, spender_address: str):
        logger.info("Start get_approve")
        token_contract = self.web3.eth.contract(
            address=token_address, abi=self.ERC20)

        function = token_contract.functions.allowance(self.sender_address,
                                                      self.web3.to_checksum_address(spender_address)).call()
        logger.info("get_approve success")
        return function

    def get_balance(self, token_address: str):
        logger.info("get_balance start")
        logger.info(f"Token address: {token_address}")
        
        token_contract = self.web3.eth.contract(address=token_address, abi=self.ERC20)
        
        balance = token_contract.functions.balanceOf(self.sender_address).call()
        decimal = token_contract.functions.decimals().call()
        logger.info(f"Get balance:{balance}")
        return balance, decimal

    def swap(self, token_in: str, token_out: str, qty: float):
        logger.info("Start function Swap")
        token_in = self.web3.to_checksum_address(token_in)
        token_out = self.web3.to_checksum_address(token_out)

        balance, decimal_in = self.get_balance(token_in)
        amount = int(qty * 10 ** decimal_in)
        logger.info(f"Amount: {amount}")
        logger.info(f"Balance: {balance}")

        if balance < amount:
            logger.info("Balance is not exist")
            return 0

        allowance = self.get_approve(token_in, self.router_contract.address)
        logger.error(f"{allowance} allowance for {token_in} on Pancake")

        if allowance != amount:
            self.web3.eth.wait_for_transaction_receipt(
                self.approve_token(token_in, self.router_contract.address, amount))

        logger.critical("Make a swap")
        function = self.router_contract.functions.exactInputSingle({
            "tokenIn": token_in,
            "tokenOut": token_out,
            "fee": 500,
            "recipient": self.web3.to_checksum_address(self.sender_address),
            "deadline": int(time.time()) + 10 * 60,
            "amountIn": amount,
            "amountOutMinimum": 0,
            "sqrtPriceLimitX96": 0
        })

        tx_params = {
            "from": self.web3.to_checksum_address(self.sender_address),
            "value": 0,
            "nonce": self.web3.eth.get_transaction_count(self.sender_address),
            "gasPrice": self.web3.eth.gas_price
        }

        transaction = function.build_transaction(tx_params)

        transaction['gas'] = self.web3.eth.estimate_gas(transaction)

        sign_tr = self.web3.eth.account.sign_transaction(
            transaction, self.private_key)
        tx_hash = self.web3.eth.send_raw_transaction(sign_tr.rawTransaction)

        try:
            receipts = self.web3.eth.wait_for_transaction_receipt(
                self.web3.to_hex(tx_hash))

            status = receipts.get("status")
            tx_hash_hex = self.web3.to_hex(tx_hash)
            if status == 1:
                logger.success(f"Transaction was successful: https://basescan.org/tx/{tx_hash_hex}")
        except Exception as error:
            raise Exception(f"Transaction not found: {error}")
