from pancake import Pancake
from config import (
    BASE_RPC,
    WETH_BASE_ADDRESS,
    USDC_BASE_ADDRESS,
    PRIVATE_KEY,
)


if __name__ == "__main__":
    panc = Pancake(PRIVATE_KEY, BASE_RPC)
    panc.swap(token_in=WETH_BASE_ADDRESS, token_out=USDC_BASE_ADDRESS, qty=0.00008)
