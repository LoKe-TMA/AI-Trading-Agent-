const config = require('./config');
const { initTelegram } = require('./telegram');
const { getTicker } = require('./bitget');
const { evaluate } = require('./strategy');
const { placeOrder, getState } = require('./executor');

const schedule = require('node-schedule');

// simple in-memory price history
const prices = [];

async function tick() {
  try {
    const price = await getTicker(config.symbol);
    prices.push(price);
    if (prices.length > 500) prices.shift();

    // run strategy only if enough history
    const decision = await evaluate(prices, price);
    console.log(new Date().toISOString(), `Price=${price}`, decision);

    const state = getState();
    const hasPos = state.positions.some(p => p.symbol === config.symbol);

    if (decision.action === 'BUY' && !hasPos) {
      const allocation = Math.max(config.minOrderUsdt, state.balance * 0.3);
      const qty = +(allocation / price).toFixed(8);
      if (qty * price >= config.minOrderUsdt) {
        await placeOrder('BUY', config.symbol, qty, price);
      }
    } else if (decision.action === 'SELL' && hasPos) {
      const pos = state.positions.find(p => p.symbol === config.symbol);
      await placeOrder('SELL', config.symbol, pos.qty, price);
    }
  } catch (e) {
    console.warn('tick error', e.message || e);
  }
}

async function main() {
  initTelegram();
  console.log('Starting Bitget Demo AI Trader — paper mode:', config.paperMode);
  // run immediately then schedule
  await tick();
  schedule.scheduleJob(`*/${config.intervalMinutes} * * * *`, tick);
}

main();
