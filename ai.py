import os
import json
import time
import pandas as pd
from dotenv import load_dotenv # .env ဖိုင်ကို ဖတ်ဖို့ ထပ်ပေါင်းထည့်ခြင်း

# Gemini Library
from google import genai
from google.genai import types

# Binance Library (Binance Futures Testnet ကို အသုံးပြုရန်)
from binance.client import Client
from binance.exceptions import BinanceAPIException

# ==============================================================================
# --- ၀။ Environment Variables များကို ဖတ်ခြင်း ---
# Local မှာ run ရင် .env ကနေ ဖတ်မယ်၊ Render မှာ run ရင် Environment ကနေ ဖတ်မယ်
load_dotenv() 

# --- ၁။ API Keys များကို Environment Variables မှ ဆွဲယူခြင်း ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
BINANCE_TESTNET_API_KEY = os.environ.get("BINANCE_TESTNET_API_KEY")
BINANCE_TESTNET_SECRET_KEY = os.environ.get("BINANCE_TESTNET_SECRET_KEY")

# --- ၂။ Constant Parameters များ ---
BINANCE_FUTURES_URL = 'https://testnet.binancefuture.com'
SYMBOL = 'BTCUSDT'
TIMEFRAME = Client.KLINE_INTERVAL_1MINUTE
LEVERAGE = 10 
DEMO_CAPITAL = 10 
POLLING_INTERVAL = 30 # စျေးကွက်ကို စစ်ဆေးမည့် အချိန် (စက္ကန့်)
# ==============================================================================

# --- ၃။ API Setup နှင့် Connection စစ်ဆေးခြင်း ---
def setup_apis():
    # 3.1 Key မရှိရင် စစ်ဆေးခြင်း
    if not all([GEMINI_API_KEY, BINANCE_TESTNET_API_KEY, BINANCE_TESTNET_SECRET_KEY]):
        print("❌ API Keys တွေ မပြည့်စုံပါဘူး။ .env ဖိုင် (သို့) Environment Variables တွေ စစ်ဆေးပေးပါ။")
        return None, None
        
    # 3.2 Gemini Setup
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_client = genai.Client()
        model = gemini_client.models.get('gemini-2.5-flash')
    except Exception as e:
        print(f"❌ Gemini API configuration error. Error: {e}")
        return None, None

    # 3.3 Binance Setup
    try:
        binance_client = Client(BINANCE_TESTNET_API_KEY, BINANCE_TESTNET_SECRET_KEY, base_url=BINANCE_FUTURES_URL)
        binance_client.futures_ping()
        print("✅ Binance Testnet Connection Successful.")
    except Exception as e:
        print(f"❌ Binance Testnet Connection Error. Error: {e}")
        return None, None
        
    return model, binance_client


# --- ၄။ Agent ညွှန်ကြားချက် (System Prompt) ---
# ... (ဤ Function သည် ယခင် Code နှင့် အတူတူပင်ဖြစ်သည်)
def get_system_prompt(current_position_info):
    """လက်ရှိ Position အခြေအနေပေါ်မူတည်ပြီး Gemini ကို ညွှန်ကြားချက်ပေးခြင်း"""
    
    if current_position_info == "NO_POSITION":
        action_options = "BUY' | 'SELL' | 'WAIT'"
        closing_instruction = "လက်ရှိ Position မရှိပါ။ အမြတ်အများဆုံးရရန် **High-Risk, High-Reward** Trade အသစ်ကို ဖွင့်ရပါမည်။"
    else:
        action_options = "CLOSE' | 'WAIT'"
        closing_instruction = f"လက်ရှိ Position မှာ {current_position_info} ဖြစ်သည်။ စျေးပြန်မကျခင် အမြတ်အများဆုံးရရှိအောင် Position ကို **'CLOSE'** လုပ်ရမည် သို့မဟုတ် ဆက်လက် 'WAIT' လုပ်ရမည်။"
    
    return f"""
You are an extremely aggressive, high-risk, maximum-profit seeking trading agent.
Your current capital for {SYMBOL} is approx. ${DEMO_CAPITAL}. Leverage is set to {LEVERAGE}x.
Your goal is to maximize profit.

**Instruction:** {closing_instruction}
Analyze the provided 1-minute candlestick data.
You MUST respond with a single JSON object.

The required JSON format is:
{{
  "action": "{action_options}",
  "reason": "Brief technical analysis and justification for the action."
}}
"""
# --- ၅။ Utility Functions ---
# ... (get_binance_data, get_current_position, execute_trade functions များသည် ယခင် Code နှင့် အတူတူပင်ဖြစ်သည်)

# (ရှင်းလင်းစေရန် ယခင် Code မှ Utility Functions များကို ဤနေရာတွင် ချန်လှပ်ထားသည်)
# (သို့သော် ၎င်းတို့ကို သင်၏ main.py ဖိုင်ထဲတွင် ပြန်လည်ပေါင်းထည့်ရန် လိုအပ်သည်)

# --- ၆။ Main Trading Loop ---
def trading_loop(model, binance_client):
    print("🚀 Gemini Crypto Demo Trading Agent စတင်ပါပြီ။")
    print(f"Demo အတွက်: {SYMBOL} | ရင်းနှီးငွေ: ${DEMO_CAPITAL} | စစ်ဆေးမှုနှုန်း: {POLLING_INTERVAL} စက္ကန့်")
    
    while True:
        try:
            # Note: get_current_position နှင့် get_binance_data function များသည် binance_client ကို အသုံးပြုပါမည်။
            # ၎င်းတို့၏ Logic ကို မပြောင်းလဲဘဲ ယခင် Code မှ ကူးထည့်ပါ။
            
            position = get_current_position(SYMBOL, binance_client) 
            market_data_str = get_binance_data(SYMBOL, TIMEFRAME, binance_client)
            
            # ... (Logics, Gemini Call and Execution များကို ယခင် Code အတိုင်း ဆက်လက်လုပ်ဆောင်ပါ)
            # ... (Gemini Call logic ကို အောင်မြင်စွာ run ဖို့အတွက် model ကို အသုံးပြုပါ။)
            
            # (ရှင်းလင်းစေရန် Main Logic များကို ဤနေရာတွင် ချန်လှပ်ထားသည်)
            
        except Exception as e:
            print(f"⚠️ Agent တွင် အကြီးစား အမှားဖြစ်ပွား: {e}")

        print(f"\n...{POLLING_INTERVAL} စက္ကန့် စောင့်ဆိုင်းပြီး နောက်တစ်ကြိမ် စစ်ဆေးပါမည်...\n")
        time.sleep(POLLING_INTERVAL) 


if __name__ == "__main__":
    # API များကို စတင် Setup လုပ်ခြင်း
    model, binance_client = setup_apis()
    
    if model and binance_client:
        trading_loop(model, binance_client)
    else:
        print("Agent စတင်ရန် မအောင်မြင်ပါ။ API Setup အား စစ်ဆေးပါ။")

