import requests
import time
from telegram import Bot

BOT_TOKEN = "8454008954:AAE9NwtBPPmbVggVCSsk1N3oNAiRRC3fhhE"
CHAT_ID = "-1001957125015"
NETWORK = "base"

POOL_ADDRESSES = {
    "Altitude/WETH": "0xd57f6e7d7ec911ba8defcf93d3682bb76959e950",
    "Altitude/USDC": "0xbf09c7f883f045feea7a59b50ba2e5df080fb4b8",
    "Altitude/cbBTC": "0xd93846f45180a7e99d5bcbc67cefc4538bb02214"
}

bot = Bot(token=BOT_TOKEN)
seen_hashes = set()

def fetch_trades(pair_name, pool_addr):
    url = f"https://api.geckoterminal.com/api/v2/networks/{NETWORK}/pools/{pool_addr}/trades"
    try:
        r = requests.get(url, timeout=10)
        data = r.json().get("data", [])
        if not data:
            print(f"⚠️ No trades found for {pair_name}")
        for trade in data:
            trade_type = trade.get("type")
            price = trade.get("price_usd")
            tx_hash = trade.get("transaction_hash")

            if trade_type == "buy" and price and float(price) >= 1 and tx_hash not in seen_hashes:
                seen_hashes.add(tx_hash)
                msg = f"🚀 Buy Alert: ${price} | Pair: {pair_name}"
                try:
                    bot.send_message(chat_id=CHAT_ID, text=msg)
                    print(f"✅ Sent alert for {tx_hash}")
                except Exception as e:
                    print(f"❌ Telegram error: {e}")
    except Exception as e:
        print(f"❌ Error fetching trades for {pair_name}: {e}")

def main():
    print("🚀 Altitude Buy Bot (GeckoTerminal) started...")
    while True:
        for name, addr in POOL_ADDRESSES.items():
            fetch_trades(name, addr)
        time.sleep(45)  # Poll every 45 seconds

if __name__ == "__main__":
    main()

