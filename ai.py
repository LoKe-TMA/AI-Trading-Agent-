import os
import json
import time
import pandas as pd

# Gemini Library
from google import genai
from google.genai import types

# Binance Library (Binance Futures Testnet ကို အသုံးပြုရန်)
from binance.client import Client
from binance.exceptions import BinanceAPIException

# ==============================================================================
# --- ၁။ API Keys များကို သတ်မှတ်ခြင်း ---
# ဤနေရာတွင် သင့်ရဲ့ တကယ့် Key များကို ထည့်သွင်းရပါမည်။ (Demo Trade အတွက်သာ အသုံးပြုပါ)
GEMINI_API_KEY = "AIzaSyAlZYTLNEOuw0mbzmeWJay1vqfGJ8OTPUE"
BINANCE_TESTNET_API_KEY = "28EtgwUMmOUcRzstevLozo9EnplHr4tJux3FHawB1a6eymcoMDur8MdDus9NRc0V"
BINANCE_TESTNET_SECRET_KEY = "0gB9ThVMVhIz3QhUx2OK3xuOC7p9v7ldS6JHWjlj3DDL3jSPiqhFN7pVc3t7M1zZ"
BINANCE_FUTURES_URL = 'https://testnet.binancefuture.com'

SYMBOL = 'BTCUSDT'
TIMEFRAME = Client.KLINE_INTERVAL_1MINUTE
LEVERAGE = 100
DEMO_CAPITAL = 50 
POLLING_INTERVAL = 30 # စျေးကွက်ကို စစ်ဆေးမည့် အချိန် (စက္ကန့်)
# ==============================================================================

# --- ၂။ API Setup နှင့် Connection စစ်ဆေးခြင်း ---
try:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_client = genai.Client()
    model = gemini_client.models.get('gemini-2.5-flash')
except Exception as e:
    print(f"❌ Gemini API configuration error. Check your GEMINI_API_KEY. Error: {e}")
    exit()

try:
    binance_client = Client(BINANCE_TESTNET_API_KEY, BINANCE_TESTNET_SECRET_KEY, base_url=BINANCE_FUTURES_URL)
    binance_client.futures_ping()
    print("✅ Binance Testnet Connection Successful.")
except Exception as e:
    print(f"❌ Binance Testnet Connection Error. Check your Keys and URL. Error: {e}")
    exit()


# --- ၃။ Agent ညွှန်ကြားချက် (System Prompt) ---
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

# --- ၄။ Utility Functions ---
def get_binance_data(symbol, timeframe, limit=30):
    """Binance Futures Testnet မှ Market Data ရယူခြင်း"""
    try:
        klines = binance_client.futures_klines(symbol=symbol, interval=timeframe, limit=limit)
        df = pd.DataFrame(klines, columns=['Open time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close time', 'Quote asset volume', 'Number of trades', 'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore'])
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            df[col] = pd.to_numeric(df[col])
        # နောက်ဆုံး 15 မိနစ် data ကိုသာ string အဖြစ် ပြောင်းပြီး Gemini ကို ပို့မည်။
        return df[['Open time', 'Open', 'High', 'Low', 'Close', 'Volume']].tail(15).to_string()
    except Exception as e:
        print(f"❌ Data Fetching Error: {e}")
        return "Market data unavailable."


def get_current_position(symbol):
    """လက်ရှိ ဖွင့်ထားသော Position ကို စစ်ဆေးခြင်း"""
    try:
        positions = binance_client.futures_get_position_risk(symbol=symbol)
        
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

def execute_trade(action, symbol, amount_usd, leverage, current_position=None):
    """Trade ဖွင့်ခြင်း သို့မဟုတ် ပိတ်ခြင်း"""
    
    if action in ['BUY', 'SELL']:
        # TRADE အသစ် ဖွင့်ခြင်း
        side = Client.SIDE_BUY if action == 'BUY' else Client.SIDE_SELL
        
        try:
            ticker = binance_client.futures_symbol_ticker(symbol=symbol)
            current_price = float(ticker['price'])
            quantity = (amount_usd * leverage) / current_price
            quantity = round(quantity, 3) 
            
            print(f"🚨 ORDER: {side} {quantity} {symbol} @ {current_price} (Leverage {leverage}x)")
            
            binance_client.futures_create_order(
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
        # TRADE ပိတ်ခြင်း
        close_side = Client.SIDE_SELL if current_position['side'] == 'LONG' else Client.SIDE_BUY
        
        try:
            print(f"🔴 CLOSING: {current_position['side']} Position. PnL: {current_position['unrealized_pnl']:.2f} USD")
            
            binance_client.futures_create_order(
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


# --- ၅။ Main Trading Loop ---
def trading_loop():
    print("🚀 Gemini Crypto Demo Trading Agent စတင်ပါပြီ။")
    print(f"Demo အတွက်: {SYMBOL} | ရင်းနှီးငွေ: ${DEMO_CAPITAL} | စစ်ဆေးမှုနှုန်း: {POLLING_INTERVAL} စက္ကန့်")
    
    while True:
        try:
            position = get_current_position(SYMBOL)
            market_data_str = get_binance_data(SYMBOL, TIMEFRAME)
            
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
                execute_trade(action, SYMBOL, DEMO_CAPITAL * 0.99, LEVERAGE)
            
            elif position is not None and action == 'CLOSE':
                execute_trade('CLOSE', SYMBOL, None, None, current_position=position)
            
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
    # Key များကို အစစ်အမှန်ဖြင့် အစားထိုးပြီးမှသာ Run ပါ။
    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY" or BINANCE_TESTNET_API_KEY == "YOUR_BINANCE_TESTNET_KEY":
        print("\n\n--- ⚠️ အရေးကြီး သတိပေးချက် ⚠️ ---\nCode ကို အမှန်တကယ် မ run ခင် API Keys များကို ထည့်သွင်းပြီး စမ်းသပ်ပါရန်။")
    else:
        trading_loop()
        
