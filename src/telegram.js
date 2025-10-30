const { Telegraf } = require('telegraf');
const config = require('./config');


let bot = null;
function initTelegram() {
if (!config.telegramToken) return null;
bot = new Telegraf(config.telegramToken);
// start bot silently (we will only use bot.telegram.sendMessage)
bot.launch().catch((e) => console.warn('telegram launch failed', e.message));
return bot;
}


async function send(msg) {
if (!bot || !config.telegramChatId) {
console.log('[TELEGRAM]', msg);
return;
}
try {
await bot.telegram.sendMessage(config.telegramChatId, msg, { parse_mode: 'Markdown' });
} catch (e) {
console.warn('telegram send error', e.message);
}
}


module.exports = { initTelegram, send };
