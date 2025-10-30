require('dotenv').config();


module.exports = {
symbol: process.env.SYMBOL || 'BTCUSDT',
intervalMinutes: parseInt(process.env.INTERVAL_MINUTES || '1', 10),
startBalance: parseFloat(process.env.START_BALANCE || '10'),
minOrderUsdt: parseFloat(process.env.MIN_ORDER_USDT || '5'),
paperMode: (process.env.PAPER_MODE || 'true') === 'true',
baseUrl: process.env.BITGET_BASE_URL || 'https://api.bitget.com',
telegramToken: process.env.TELEGRAM_BOT_TOKEN,
telegramChatId: process.env.TELEGRAM_CHAT_ID,
newsApiKey: process.env.NEWSAPI_KEY || null
};
