// lightweight headline sentiment. Optional: will call NewsAPI if key provided.
const axios = require('axios');
const Sentiment = require('sentiment');
const sentiment = new Sentiment();
const config = require('./config');


async function fetchHeadlines(q = 'bitcoin', limit = 5) {
if (!config.newsApiKey) return [];
try {
const url = `https://newsapi.org/v2/everything?q=${encodeURIComponent(q)}&pageSize=${limit}&sortBy=publishedAt&apiKey=${config.newsApiKey}`;
const res = await axios.get(url);
return (res.data.articles || []).map(a => ({ title: a.title, desc: a.description || '', publishedAt: a.publishedAt }));
} catch (e) {
console.warn('news fetch error', e.message);
return [];
}
}


function analyzeTextScore(text) {
const r = sentiment.analyze(text || '');
// map score to -1..1 roughly
const norm = Math.tanh((r.score || 0) / 5);
return norm;
}


async function computeNewsScore(symbol = 'BTC') {
const q = symbol;
const articles = await fetchHeadlines(q, 5);
if (!articles || articles.length === 0) return { newsScore: 0, impact: 0 };
let sum = 0, w = 0;
for (const a of articles) {
const s = analyzeTextScore(a.title + ' ' + a.desc);
const ageHours = Math.max(0.001, (Date.now() - new Date(a.publishedAt).getTime()) / (1000 * 60 * 60));
const weight = 1 / ageHours; // fresher weight
sum += s * weight;
w += weight;
}
return { newsScore: w ? sum / w : 0, impact: Math.min(1, w / 3) };
}


module.exports = { computeNewsScore };
