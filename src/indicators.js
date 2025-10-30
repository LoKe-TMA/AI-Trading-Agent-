const ti = require('technicalindicators');


function computeRSI(values, period = 14) {
if (!values || values.length < period + 1) return null;
const rsi = ti.RSI.calculate({ values, period });
return rsi[rsi.length - 1];
}


module.exports = { computeRSI };
