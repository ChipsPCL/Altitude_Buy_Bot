const axios = require("axios");
const TelegramBot = require("node-telegram-bot-api");
const { BOT_TOKEN, CHAT_ID, POOL_ID, MIN_USD, POLL_INTERVAL_MS } = require("./config");

const bot = new TelegramBot(BOT_TOKEN, { polling: false });
let lastSwapId = null;

async function checkSwaps() {
  try {
    const url = `https://api.geckoterminal.com/api/v2/networks/base/pools/${POOL_ID}/swaps`;
    const res = await axios.get(url);
    const swaps = res.data.data;

    for (let i = swaps.length - 1; i >= 0; i--) {
      const s = swaps[i];
      const a = s.attributes;
      if (s.id === lastSwapId) break;
      if (a.trade_type === "buy" && parseFloat(a.amount_usd) >= MIN_USD) {
        const msg = `🚀 *Buy Alert*\n${a.amount} tokens (~$${a.amount_usd})\n⛽️ At: ${new Date(a.block_signed_at).toUTCString()}`;
        await bot.sendMessage(CHAT_ID, msg, { parse_mode: "Markdown" });
      }
    }
    lastSwapId = swaps[0]?.id;
  } catch (e) {
    console.error("Error fetching swaps:", e.message);
  }
}

async function start() {
  await checkSwaps();
  setInterval(checkSwaps, POLL_INTERVAL_MS);
}

start();