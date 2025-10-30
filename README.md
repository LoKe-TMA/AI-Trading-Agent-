# AI-Trading-Agent-
# Bitget Demo AI Trader — Starter


1. Create project folder and paste files according to filenames above.
2. Copy `.env.example` to `.env` and fill TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.
- To get chat id: message your bot then call https://api.telegram.org/bot<token>/getUpdates
3. Install dependencies:
npm install
4. Run:
npm start


What it does:
- Fetches Bitget public ticker for SYMBOL every INTERVAL_MINUTES
- Keeps a small in-memory price history
- Computes RSI and (optionally) news sentiment
- Combines signals into a final score and executes paper BUY/SELL
- Sends Telegram messages for executed buy/sell


Notes:
- This is a starter demo. DO NOT use with real money before testing.
- Extend with persistent DB, live Bitget order placement, advanced risk rules.
