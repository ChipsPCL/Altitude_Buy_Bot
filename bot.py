import requests
import time
from telegram import Bot

# --- Configuration ---
BOT_TOKEN = "8454008954:AAE9NwtBPPmbVggVCSsk1N3oNAiRRC3fhhE"
CHAT_ID = "-1001957125015"
PAIRS = [
    {"name": "Altitude/WETH", "pool": "0xd57f6e7d7ec911ba8defcf93d3682bb76959e950"},
    {"name": "Altitude/USDC", "pool": "0xbf09c7f883f045feea7a59b50ba2e5df080fb4b8"},
    {"name": "Altitude/cbBTC", "pool": "0xd93846f45180a7e99d5bcbc67cefc4538bb02214"},
]
NETWORK = "base"

bot = Bot(token=BOT_TOKEN)
seen_hashes = set()

# --- Functions ---
def fetch_trades(pool_addr):
    url = f"https://api.geckoterminal.com/api/v2/networks/{NETWORK}/pools/{pool_addr}/trades"
    try:
        r = requests.get(url, timeout=10)
        json_data = r.json()
        trades = json_data.get("data", [])
        return trades
    except Exception as e:
        print(f"❌ Error fetching trades from {pool_addr}: {e}")
        return []

def format_message(trade, pair_name):
    attrs = trade.get("attributes", {})
    amount = float(attrs.get("quote_price", 0)) * float(attrs.get("base_amount", 0))
    return (
        f"🚀 Buy Alert (${amount:.2f}) on {pair_name}\n"
        f"📈 Token: {attrs.get('base_symbol')}\n"
        f"💵 Price: ${attrs.get('quote_price')}\n"
        f"🔗 Hash: {attrs.get('transaction_hash')[:10]}..."
    )

# --- Main Loop ---
def main():
    print("📡 Altitude BuyBot started using GeckoTerminal API...")
    while True:
        for pair in PAIRS:
            trades = fetch_trades(pair["pool"])
            print(f"✅ Checked {pair['name']}: {len(trades)} trades")

            for trade in trades:
                attrs = trade.get("attributes", {})
                tx_hash = attrs.get("transaction_hash")
                if attrs.get("trade_type") == "buy" and tx_hash not in seen_hashes:
                    amount = float(attrs.get("quote_price", 0)) * float(attrs.get("base_amount", 0))
                    if amount >= 1:
                        msg = format_message(trade, pair["name"])
                        try:
                            bot.send_message(chat_id=CHAT_ID, text=msg)
                            print(f"📤 Sent alert: {msg}")
                        except Exception as e:
                            print(f"❌ Failed to send alert: {e}")
                    seen_hashes.add(tx_hash)

        time.sleep(30)

if __name__ == "__main__":
    main()
