import asyncio
import json
import time
from web3 import Web3
from telegram import Bot
from eth_abi import decode_abi

# Environment variables (set in Railway)
BOT_TOKEN = "your-bot-token"
CHAT_ID = "your-chat-id"
RPC_URL = "https://rpc.ankr.com/base"  # <-- use HTTP

bot = Bot(token=BOT_TOKEN)
w3 = Web3(Web3.HTTPProvider(RPC_URL))
seen_tx = set()

# Load ABIs
with open("uniswap_v2.json") as f:
    uniswap_abi = json.load(f)

with open("pancake_v3.json") as f:
    pancake_abi = json.load(f)

# Pool configurations
POOLS = [
    {
        "name": "Altitude/WETH",
        "address": "0xD57f6e7D7eC911bA8deFCf93d3682BB76959e950",
        "abi": uniswap_abi,
        "type": "v2"
    },
    {
        "name": "Altitude/USDC",
        "address": "0xbf09C7F883F045fEeA7a59b50BA2E5dF080fb4B8",
        "abi": uniswap_abi,
        "type": "v2"
    },
    {
        "name": "Altitude/cbBTC",
        "address": "0xd93846f45180A7e99d5bCBc67cefC4538bb02214",
        "abi": pancake_abi,
        "type": "v3"  # Not yet implemented fully
    }
]

def decode_v2_swap(log):
    topics = log['topics']
    data = log['data']
    values = decode_abi(['uint256','uint256','uint256','uint256'], bytes.fromhex(data[2:]))
    return {
        "amount0In": values[0],
        "amount1In": values[1],
        "amount0Out": values[2],
        "amount1Out": values[3],
        "tx_hash": log['transactionHash'].hex()
    }

async def monitor_v2(pool):
    contract = w3.eth.contract(address=Web3.to_checksum_address(pool['address']), abi=pool['abi'])
    swap_event = contract.events.Swap()._get_event_abi()

    last_block = w3.eth.block_number

    while True:
        try:
            latest = w3.eth.block_number
            logs = w3.eth.get_logs({
                "fromBlock": last_block + 1,
                "toBlock": latest,
                "address": pool['address'],
                "topics": [Web3.keccak(text="Swap(address,uint256,uint256,uint256,uint256,address)").hex()]
            })

            for log in logs:
                data = decode_v2_swap(log)
                tx_hash = data["tx_hash"]
                if tx_hash in seen_tx:
                    continue
                seen_tx.add(tx_hash)

                msg = f"🚀 Buy/Sell Alert on {pool['name']}\nTX: https://basescan.org/tx/{tx_hash}"
                await bot.send_message(chat_id=CHAT_ID, text=msg)
                print(f"✅ Sent alert for {tx_hash}")

            last_block = latest
        except Exception as e:
            print(f"❌ Error polling {pool['name']}: {e}")
        await asyncio.sleep(30)

async def main():
    print("📡 Altitude BuyBot started using on-chain RPC")
    tasks = []
    for pool in POOLS:
        if pool['type'] == 'v2':
            tasks.append(asyncio.create_task(monitor_v2(pool)))
        else:
            print(f"⏳ Skipping {pool['name']} (Pancake V3 not yet integrated)")
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
