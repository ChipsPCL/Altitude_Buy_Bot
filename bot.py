import os
import asyncio
from web3 import Web3
from telegram import Bot
import aiohttp

# --- Configuration ---
BOT_TOKEN  = os.getenv("BOT_TOKEN")
CHAT_ID    = os.getenv("CHAT_ID")
RPC_URL    = os.getenv("RPC_URL")  # e.g. wss://rpc.ankr.com/base/ws

# Pools to monitor
POOL_DATA = [
    {"name": "Altitude – BaseSwap V2", "address": "0xd57f6e7D7eC911bA8deFCf93d3682BB76959e950", "type": "v2"},
    {"name": "Altitude – Aerodrome V2", "address": "0xbf09C7F883F045fEeA7a59b50BA2E5dF080fb4B8", "type": "v2"},
    {"name": "Altitude – PancakeSwap V3", "address": "0xd93846f45180a7e99d5bCBc67cefC4538bb02214", "type": "v3"},
]

# Simplified ABIs for Swap events
V2_ABI = [{
    "anonymous": False,
    "inputs": [
        {"indexed": False, "name": "sender", "type": "address"},
        {"indexed": False, "name": "amount0In", "type": "uint256"},
        {"indexed": False, "name": "amount1In", "type": "uint256"},
        {"indexed": False, "name": "amount0Out", "type": "uint256"},
        {"indexed": False, "name": "amount1Out", "type": "uint256"},
        {"indexed": True, "name": "to", "type": "address"},
    ],
    "name": "Swap",
    "type": "event"
}]
V3_ABI = V2_ABI  # For simplicity use same event decoding

bot = Bot(token=BOT_TOKEN)
w3 = Web3(Web3.WebsocketProvider(RPC_URL))

seen = set()

async def fetch_price_usd(symbol):
    async with aiohttp.ClientSession() as session:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd"
        async with session.get(url, timeout=5) as r:
            j = await r.json()
            return j.get(symbol, {}).get("usd", 0)

async def handle_event(event, pair):
    tx = event["transactionHash"].hex()
    if tx in seen:
        return
    seen.add(tx)

    # For V2: amount0In/out and amount1In/out. Identify which token is Altitude
    amt_in = int(event["args"]["amount1In"] or 0)
    amt_out = int(event["args"]["amount1Out"] or 0)
    # Simplify: assume one side is Altitude and other is ETH/cbBTC/USDC
    usd_val = amt_out * await fetch_price_usd("ethereum") / 1e18 if amt_out else amt_in * await fetch_price_usd("ethereum") / 1e18

    if usd_val >= 1:
        msg = f"🚀 Buy Alert (${usd_val:.2f}) on {pair['name']}\n🔗 Tx: {tx[:10]}..."
        await bot.send_message(chat_id=CHAT_ID, text=msg)

async def monitor_pool(pair):
    contract = w3.eth.contract(address=pair["address"], abi=V2_ABI)
    event_filter = contract.events.Swap.create_filter(fromBlock="latest")
    while True:
        for ev in event_filter.get_new_entries():
            await handle_event(ev, pair)
        await asyncio.sleep(2)

async def main():
    await asyncio.gather(*(monitor_pool(p) for p in POOL_DATA))

if __name__ == "__main__":
    asyncio.run(main())
