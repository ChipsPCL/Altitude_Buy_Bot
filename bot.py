import requests
import time
from telegram import Bot

# Telegram Bot Token
BOT_TOKEN = "8454008954:AAE9NwtBPPmbVggVCSsk1N3oNAiRRC3fhhE"
CHAT_ID = "-1001957125015"

# Dexscreener API pairs
PAIRS = [
    "https://api.dexscreener.com/latest/dex/pairs/base/0xd57f6e7d7ec911ba8defcf93d3682bb76959e950",  # WETH
    "https://api.dexscreener.com/latest/dex/pairs/base/0xbf09c7f883f045feea7a59b50ba2e5df080fb4b8",  # USDC
    "https://api.dexscreener.com/latest/dex/pairs/base/0xd93846f45180a7e99d5bcbc67cefc4538bb02214"   # cbBTC
]

bot = Bot(token=BOT_TOKEN)

def get_trades(pair_url):
    try:
        r = requests.get(pair_url, timeout=10)
        data = r.json()
        trades = data.get("pair", {}).get("recentTxns", [])
        print(f"✅ Fetched {len(trades)} trades from {pair_url.split('/')[-1]}")
        return trades
    except Exception as e:
        print("❌ Error fetching data:", e)
        return []

def main():
    print("🚀 Altitude Buy Bot started...")
    last_hashes = set()

    while True:
        for pair in PAIRS:
            trades = get_trades(pair)
            for t in trades:
                if isinstance(t, dict):
                    txn_hash = t.get("hash")
                    trade_type = t.get("type")
                    price_usd = t.get("priceUsd")
                    print(f"🔍 Checking trade {txn_hash} — Type: {trade_type} — Price: {price_usd}")

                    # Only send alerts for buys, price >= 1 USD, and unseen txns
                    if (
                        trade_type == "buy" and
                        price_usd and
                        float(price_usd) >= 1 and
                        txn_hash not in last_hashes
                    ):
                        msg = f"🚀 Buy Alert: ${price_usd} | Pair: {pair.split('/')[-1]}"
                        print(f"📣 Sending message: {msg}")

                        try:
                            bot.send_message(chat_id=CHAT_ID, text=msg)
                            print("✅ Message sent to Telegram!")
                        except Exception as e:
                            print(f"❌ Error sending message: {e}")

                        last_hashes.add(txn_hash)

        time.sleep(60)

if __name__ == "__main__":
    main()
