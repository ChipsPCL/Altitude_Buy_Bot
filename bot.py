import asyncio
import os
from web3 import Web3
from telegram import Bot
from telegram.error import TelegramError

# Env vars
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
RPC_URL = os.getenv("RPC_URL")

bot = Bot(token=BOT_TOKEN)
w3 = Web3(Web3.WebsocketProvider(RPC_URL))

# Pool data
POOLS = [
    {
        "name": "Altitude/WETH",
        "address": Web3.to_checksum_address("0xd57f6e7d7ec911ba8defcf93d3682bb76959e950"),
        "altitude_is_token0": False,
    },
    {
        "name": "Altitude/USDC",
        "address": Web3.to_checksum_address("0xbf09C7F883F045fEeA7a59b50BA2E5dF080fb4B8"),
        "altitude_is_token0": True,
    },
]

# Swap event signature
SWAP_TOPIC = w3.keccak(text="Swap(address,uint256,uint256,uint256,uint256,address)").hex()
seen_txns = set()

async def listen_to_pool(pool):
    print(f"👂 Listening to {pool['name']} at {pool['address']}")

    while True:
        try:
            logs = w3.eth.get_logs({
                "address": pool["address"],
                "topics": [SWAP_TOPIC],
                "fromBlock": "latest"
            })

            for log in logs:
                if log["transactionHash"].hex() in seen_txns:
                    continue

                seen_txns.add(log["transactionHash"].hex())

                data = log["data"][2:]  # Strip 0x
                amounts = [int(data[i:i+64], 16) for i in range(0, 64 * 4, 64)]
                amount0_in, amount1_in, amount0_out, amount1_out = amounts

                # Determine if it's a buy based on Altitude direction
                is_buy = False
                if pool["altitude_is_token0"]:
                    is_buy = amount1_in > 0 and amount0_out > 0
                else:
                    is_buy = amount0_in > 0 and amount1_out > 0

                if is_buy:
                    msg = f"🚀 Buy Alert on {pool['name']}\nTx: {log['transactionHash'].hex()}"
                    try:
                        await bot.send_message(chat_id=CHAT_ID, text=msg)
                        print(f"✅ Sent: {msg}")
                    except TelegramError as e:
                        print(f"❌ Telegram error: {e}")
                else:
                    print(f"ℹ️ Non-buy txn on {pool['name']}")

        except Exception as e:
            print(f"❌ Error fetching logs for {pool['name']}: {e}")

        await asyncio.sleep(10)

async def main():
    print("📡 Altitude BuyBot started with Ankr RPC...")
    tasks = [listen_to_pool(pool) for pool in POOLS]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
