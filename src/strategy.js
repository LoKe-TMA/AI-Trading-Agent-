const { computeRSI } = require('./indicators');
const { computeNewsScore } = require('./news');
const { getState, placeOrder } = require('./executor');
const config = require('./config');


async function evaluate(priceHistory, currentPrice) {
// priceHistory: array of close prices (old..new)
const rsi = computeRSI(priceHistory);
const { newsScore, impact } = await computeNewsScore('bitcoin');


// weights
const wIndicator = 0.4;
const wNews = 0.6 * (impact > 0.7 ? 1.5 : 1.0);


// indicator score: RSI <30 => +1, RSI>70 => -1, else mapped
let indicatorScore = 0;
if (rsi === null) indicatorScore = 0;
else if (rsi < 30) indicatorScore = 1;
else if (rsi > 70) indicatorScore = -1;
else indicatorScore = (50 - rsi) / 25; // maps ~[-1..1]


const final = (wIndicator * indicatorScore) + (wNews * newsScore);


// thresholds
if (final > 0.6) return { action: 'BUY', score: final };
if (final < -0.6) return { action: 'SELL', score: final };
return { action: 'HOLD', score: final };
}


module.exports = { evaluate };
