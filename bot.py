import asyncio
import json
from web3 import Web3
from telegram import Bot

# --- Hardcoded Config ---
BOT_TOKEN = "8454008954:AAE9NwtBPPmbVggVCSsk1N3oNAiRRC3fhhE"
CHAT_ID = "-1001957125015"
RPC_URL = "wss://rpc.ankr.com/base/ws"

# --- Altitude Pools ---
POOLS = {
    "Altitude/WETH": {
        "address": "0xD57f6e7D7eC911bA8deFCf93d3682BB76959e950",
        "abi": "uniswap_v2.json"
    },
    "Altitude/USDC": {
        "address": "0xbf09C7F883F045fEeA7a59b50BA2E5dF080fb4B8",
        "abi": "uniswap_v2.json"
    },
    "Altitude/cbBTC": {
        "address": "0xd93846f45180A7e99d5bCBc67cefC4538bb02214",
        "abi": "pancake_v3.json"
    }
}

# --- Load ABIs ---
with open("uniswap_v2.json") as f:
    UNIV2_ABI = json.load(f)
with open("pancake_v3.json") as f:
    V3_ABI = json.load(f)

# --- Telegram Bot Setup ---
bot = Bot(token=BOT_TOKEN)

# --- Web3 Setup ---
w3 = Web3(Web3.WebsocketProvider(RPC_URL))

# --- Track Seen Transactions ---
seen_txns = set()

# --- Event Listener ---
async def monitor_v2(pair_name, pool_addr):
    contract = w3.eth.contract(address=Web3.to_checksum_address(pool_addr), abi=UNIV2_ABI)
    event_filter = contract.events.Swap.createFilter(fromBlock="latest")

    while True:
        for event in event_filter.get_new_entries():
            tx_hash = event.transactionHash.hex()
            if tx_hash in seen_txns:
                continue
            seen_txns.add(tx_hash)

            amount0In = event.args.amount0In
            amount1In = event.args.amount1In
            amount = max(amount0In, amount1In) / 1e18

            if amount >= 1:
                msg = f"🚀 Buy Alert (${amount:.2f}) on {pair_name}\n🔗 Tx: {tx_hash[:10]}..."
                try:
                    await bot.send_message(chat_id=CHAT_ID, text=msg)
                    print(f"✅ Sent alert for {pair_name}: {msg}")
                except Exception as e:
                    print(f"❌ Telegram error: {e}")
        await asyncio.sleep(5)

# (Optional) Placeholder for Pancake V3 monitoring
async def monitor_v3(pair_name, pool_addr):
    print(f"⏳ Skipping {pair_name} (Pancake V3 not yet integrated)")
    await asyncio.sleep(99999)

# --- Main ---
async def main():
    print("📡 Altitude BuyBot started using on-chain RPC")

    tasks = []
    for name, info in POOLS.items():
        if info["abi"] == "uniswap_v2.json":
            tasks.append(asyncio.create_task(monitor_v2(name, info["address"])))
        else:
            tasks.append(asyncio.create_task(monitor_v3(name, info["address"])))
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
