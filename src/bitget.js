// simple Bitget market fetcher (public endpoints)
const axios = require('axios');
const config = require('./config');


const BASE = config.baseUrl || 'https://api.bitget.com';


async function getTicker(symbol = config.symbol) {
try {
const url = `${BASE}/api/spot/v1/market/ticker?symbol=${symbol}`;
const res = await axios.get(url, { timeout: 5000 });
// response: { code, msg, data: { ... } }
if (res.data && res.data.data && res.data.data.close) {
return parseFloat(res.data.data.close);
}
// fallback — try different shape
if (res.data && res.data.ticker && res.data.ticker.last) {
return parseFloat(res.data.ticker.last);
}
throw new Error('unexpected ticker format');
} catch (e) {
throw new Error('bitget getTicker error: ' + (e.message || e));
}
}


module.exports = { getTicker };
