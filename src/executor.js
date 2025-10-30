const config = require('./config');
const { send } = require('./telegram');


let state = {
balance: config.startBalance,
positions: [] // { symbol, qty, entryPrice }
};


function getState() { return state; }


async function placeOrder(side, symbol, qty, price) {
// simple immediate-fill simulation
if (side === 'BUY') {
const cost = qty * price;
if (cost > state.balance + 1e-8) {
return { success: false, reason: 'insufficient_balance' };
}
state.balance -= cost;
state.positions.push({ symbol, qty, entryPrice: price });
const msg = `📈 *BUY EXECUTED*\nSymbol: ${symbol}\nPrice: ${price.toFixed(2)}\nQty: ${qty.toFixed(8)}\nBalance: $${state.balance.toFixed(4)}`;
await send(msg);
return { success: true };
} else if (side === 'SELL') {
const idx = state.positions.findIndex(p => p.symbol === symbol);
if (idx === -1) return { success: false, reason: 'no_position' };
const pos = state.positions[idx];
const proceeds = pos.qty * price;
const entry = pos.entryPrice * pos.qty;
const profitPct = ((proceeds - entry) / entry) * 100;
state.balance += proceeds;
state.positions.splice(idx, 1);
const msg = `💰 *SELL EXECUTED*\nSymbol: ${symbol}\nPrice: ${price.toFixed(2)}\nProfit: ${profitPct.toFixed(2)}%\nBalance: $${state.balance.toFixed(4)}`;
await send(msg);
return { success: true, profitPct };
}
return { success: false, reason: 'unknown_side' };
}


module.exports = { placeOrder, getState };
