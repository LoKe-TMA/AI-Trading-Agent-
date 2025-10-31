# ============================================================
# 🌍 Forex AI Trading Simulation Bot (Render / Termux Compatible)
# Author: LiKe AI
# ============================================================

from forex_python.converter import CurrencyRates
import pandas as pd
import numpy as np
import ta
import time
import random
import os

# -------------------------
# Configuration
# -------------------------
START_BALANCE = 10.0
PAIR = ("XAU", "USD")
SLEEP_TIME = 30  # seconds between trades
TRADE_RISK = 0.02  # 2% per trade

# -------------------------
# Initialize
# -------------------------
c = CurrencyRates()
balance = START_BALANCE
trade_count = 0

# -------------------------
# Function: Generate Market Data
# -------------------------
def get_market_data():
    try:
        base_rate = c.get_rate(PAIR[0], PAIR[1])
    except Exception as e:
        print(f"⚠️ Error fetching rate: {e}")
        base_rate = 1.08

    prices = [base_rate + random.uniform(-0.002, 0.002) for _ in range(100)]
    df = pd.DataFrame(prices, columns=["close"])
    df["EMA"] = ta.trend.ema_indicator(df["close"], window=20)
    df["RSI"] = ta.momentum.rsi(df["close"], window=14)
    return df

# -------------------------
# Function: AI Trading Logic
# -------------------------
def ai_signal(df):
    ema = df["EMA"].iloc[-1]
    close = df["close"].iloc[-1]
    rsi = df["RSI"].iloc[-1]

    if ema > close and rsi < 30:
        return "BUY"
    elif ema < close and rsi > 70:
        return "SELL"
    else:
        return "HOLD"

# -------------------------
# Function: Simulate Trade
# -------------------------
def simulate_trade(signal, balance):
    profit_loss = 0
    if signal == "BUY":
        profit_loss = balance * TRADE_RISK * random.uniform(0.8, 1.2)
    elif signal == "SELL":
        profit_loss = -balance * TRADE_RISK * random.uniform(0.8, 1.2)
    else:
        profit_loss = 0
    return balance + profit_loss

# -------------------------
# Main Loop
# -------------------------
os.system("clear")
print("🚀 Starting AI Forex Simulation Bot (Render-Compatible)")
print("-------------------------------------------------------\n")

while True:
    trade_count += 1
    data = get_market_data()
    signal = ai_signal(data)

    print(f"🕒 Trade #{trade_count}")
    print(f"📊 Pair: {PAIR[0]}/{PAIR[1]}")
    print(f"🤖 AI Signal: {signal}")

    old_balance = balance
    balance = simulate_trade(signal, balance)

    change = balance - old_balance
    status = "📈 Profit" if change > 0 else "📉 Loss" if change < 0 else "⚪ No Trade"

    print(f"{status}: {change:+.4f} USD")
    print(f"💰 Balance: {balance:.2f} USD\n")
    print("-------------------------------------------------------\n")

    # Sleep before next trade
    time.sleep(SLEEP_TIME)
    
