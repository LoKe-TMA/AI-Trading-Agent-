import os
import json
import time
import pandas as pd
from dotenv import load_dotenv # Local အတွက် .env ကို ဖတ်ဖို့

# Gemini Library
from google import genai
from google.genai import types

# Binance Library (Binance Futures Testnet ကို အသုံးပြုရန်)
from binance.client import Client
from binance.exceptions import BinanceAPIException

# ==============================================================================
# --- ၀။ Environment Variables များကို ဖတ်ခြင်း ---
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
    """Gemini Client နှင့် Binance Testnet Client ကို စတင်ချိတ်ဆက်ခြင်း"""
    
    # 3.1 Key မရှိရင် စစ်ဆေးခြင်း
    if not all([GEMINI_API_KEY, BINANCE_TESTNET_API_KEY, BINANCE_TESTNET_SECRET_KEY]):
        print("❌ API Keys တွေ မပြည့်စုံပါဘူး။ Environment Variables (သို့မဟုတ် .env) တွေ စစ်ဆေးပေးပါ။")
        return None, None
        
    # 3.2 Gemini Setup (Error ပြင်ဆင်ပြီး)
    try:
        # API Key ကို genai.Client() ထဲ တိုက်ရိုက်ပေးပို့ခြင်း
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        model = gemini_client.models.get('gemini-2.5-flash')
        print("✅ Gemini Client Connection Successful.")
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
def get_binance_data(symbol, timeframe, client, limit=30):
    """Binance Futures Testnet မှ Market Data ရယူခြင်း"""
    try:
        klines = client.futures_klines(symbol=symbol, interval=timeframe, limit=limit)
        df = pd.DataFrame(klines, columns=['Open time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close time', 'Quote asset volume', 'Number of trades', 'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore'])
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            df[col] = pd.to_numeric(df[col])
        return df[['Open time', 'Open', 'High', 'Low', 'Close', 'Volume']].tail(15).to_string()
    except Exception as e:
        print(f"❌ Data Fetching Error: {e}")
        return "Market data unavailable."


def get_current_position(symbol, client):
    """လက်ရှိ ဖွင့်ထားသော Position ကို စစ်ဆေးခြင်း"""
    try:
        positions = client.futures_get_position_risk(symbol=symbol)
        
        for pos in positions:
            quantity = float(pos['positionAmt'])
            if quantity != 0:
                entry_price = float(pos['entryPrice'])
                unrealized_pnl = float(pos['unRealizedProfit'])
                
                side = 'LONG' if quantity > 0 else 'SHORT'
                
                return {
                    'side': side,
                    'quantity': abs(quantity),
                    'entry_price': entry_price,
                    'unrealized_pnl': unrealized_pnl,
                    'info': f"{side}, Qty: {abs(quantity):.4f}, Entry: {entry_price:.2f}, PnL: {unrealized_pnl:.2f} USD"
                }
        return None
    except Exception as e:
        print(f"❌ Position Checking Error: {e}")
        return None

def execute_trade(action, symbol, amount_usd, leverage, client, current_position=None):
    """Trade ဖွင့်ခြင်း သို့မဟုတ် ပိတ်ခြင်း"""
    
    if action in ['BUY', 'SELL']:
        # TRADE အသစ် ဖွင့်ခြင်း (Open New Trade)
        side = Client.SIDE_BUY if action == 'BUY' else Client.SIDE_SELL
        
        try:
            ticker = client.futures_symbol_ticker(symbol=symbol)
            current_price = float(ticker['price'])
            quantity = (amount_usd * leverage) / current_price
            quantity = round(quantity, 3) 
            
            print(f"🚨 ORDER: {side} {quantity} {symbol} @ {current_price} (Leverage {leverage}x)")
            
            client.futures_create_order(
                symbol=symbol,
                side=side,
                type=Client.ORDER_TYPE_MARKET,
                quantity=quantity
            )
            print("✅ Order Success.")
        except BinanceAPIException as e:
            print(f"❌ Binance API Error (New Trade): {e}")
        except Exception as e:
            print(f"❌ Error: {e}")

    elif action == 'CLOSE' and current_position:
        # TRADE ပိတ်ခြင်း (Close Existing Trade)
        close_side = Client.SIDE_SELL if current_position['side'] == 'LONG' else Client.SIDE_BUY
        
        try:
            print(f"🔴 CLOSING: {current_position['side']} Position. PnL: {current_position['unrealized_pnl']:.2f} USD")
            
            client.futures_create_order(
                symbol=symbol,
                side=close_side,
                type=Client.ORDER_TYPE_MARKET,
                quantity=current_position['quantity']
            )
            print("✅ Close Order Success.")
        
        except BinanceAPIException as e:
            print(f"❌ Binance API Error (Close Trade): {e}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return None

# --- ၆။ Main Trading Loop ---
def trading_loop(model, binance_client):
    print("🚀 Gemini Crypto Demo Trading Agent စတင်ပါပြီ။")
    print(f"Demo အတွက်: {SYMBOL} | ရင်းနှီးငွေ: ${DEMO_CAPITAL} | စစ်ဆေးမှုနှုန်း: {POLLING_INTERVAL} စက္ကန့်")
    
    while True:
        try:
            # Client ကို Functions များဆီ ပို့ဆောင်ပေးခြင်း
            position = get_current_position(SYMBOL, binance_client)
            market_data_str = get_binance_data(SYMBOL, TIMEFRAME, binance_client)
            
            if position:
                print(f"** လက်ရှိ Position: {position['info']} **")
                position_status = position['info']
            else:
                print("** လက်ရှိ Position မရှိသေးပါ။ **")
                position_status = "NO_POSITION"

            system_prompt = get_system_prompt(position_status)
            full_prompt = f"အောက်ပါ {SYMBOL} ၏ နောက်ဆုံး ၁၅ မိနစ်စာ 1-minute data ဇယားကို ခွဲခြမ်းစိတ်ဖြာပြီး သင့်ရဲ့ အကောင်းဆုံး ဆုံးဖြတ်ချက်ကို JSON ဖြင့် ပြန်ပေးပါ:\n\n{market_data_str}"
            
            print("-> Gemini ကို ခွဲခြမ်းစိတ်ဖြာရန် ပို့နေသည်...")
            
            # Gemini ကို ခေါ်ဆိုခြင်း
            response = model.generate_content(
                full_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_schema={
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "enum": ["BUY", "SELL", "CLOSE", "WAIT"]},
                            "reason": {"type": "string"}
                        },
                        "required": ["action", "reason"]
                    },
                )
            )
            
            # ဆုံးဖြတ်ချက်ကို ထုတ်ယူခြင်း
            agent_decision = json.loads(response.text)
            action = agent_decision.get('action', 'WAIT')
            reason = agent_decision.get('reason', 'No specific reason.')
            
            print(f"🤖 Agent ဆုံးဖြတ်ချက်: {action}")
            print(f"-> အကြောင်းပြချက်: {reason}")
            
            # Trade လုပ်ဆောင်ချက်
            if position is None and action in ['BUY', 'SELL']:
                execute_trade(action, SYMBOL, DEMO_CAPITAL * 0.99, LEVERAGE, binance_client)
            
            elif position is not None and action == 'CLOSE':
                execute_trade('CLOSE', SYMBOL, None, None, binance_client, current_position=position)
            
            elif action == 'WAIT':
                print("⏲️ စျေးကွက်ကို စောင့်ကြည့်နေသည်။")
            
        except json.JSONDecodeError:
            print("❌ Gemini မှ JSON ပုံစံ မှန်ကန်စွာ မပြန်လာပါ၊ စောင့်ဆိုင်းပါမည်။")
        except Exception as e:
            print(f"⚠️ Agent တွင် အကြီးစား အမှားဖြစ်ပွား: {e}")

        # နောက်တစ်ကြိမ် မစခင် 30 စက္ကန့် စောင့်ဆိုင်းခြင်း
        print(f"\n...{POLLING_INTERVAL} စက္ကန့် စောင့်ဆိုင်းပြီး နောက်တစ်ကြိမ် စစ်ဆေးပါမည်...\n")
        time.sleep(POLLING_INTERVAL) 


if __name__ == "__main__":
    # API များကို စတင် Setup လုပ်ခြင်း
    model, binance_client = setup_apis()
    
    if model and binance_client:
        trading_loop(model, binance_client)
    else:
        print("Agent စတင်ရန် မအောင်မြင်ပါ။ API Setup အား စစ်ဆေးပါ။")
