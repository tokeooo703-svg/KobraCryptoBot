import requests
import pandas as pd
from datetime import datetime

TOKEN = "8005371069:AAE4exHBS-poluP5UBwClJh-_SOKrJgImIs"
CHAT_ID = "946090948"

coins = {
    "litecoin": "LTC",
    "near": "NEAR",
    "dogecoin": "DOGE",
    "shiba-inu": "SHIB",
    "zeal": "ZEAL"
}

def get_prices_and_levels(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": 7}
    data = requests.get(url, params=params).json()
    
    prices = [p[1] for p in data['prices']]
    df = pd.DataFrame(prices, columns=['close'])
    
    current_price = df['close'].iloc[-1]
    support = df['close'].min()
    resistance = df['close'].max()
    
    return current_price, support, resistance

def send_update():
    message_lines = [f"📊 تحديث العملات الرقمية – {datetime.now().strftime('%Y-%m-%d')}:"]
    
    for coin_id, symbol in coins.items():
        try:
            price, support, resistance = get_prices_and_levels(coin_id)
            message_lines.append(f"- {symbol}: ${price:.6f} | دعم: ${support:.6f}, مقاومة: ${resistance:.6f}")
        except Exception as e:
            message_lines.append(f"- {symbol}: خطأ في جلب البيانات")
    
    message_lines.append("\n⚡ تنبيهات فورية لأي حركة قوية أو كسر دعم/مقاومة.")
    MESSAGE = "\n".join(message_lines)
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": MESSAGE}
    requests.get(url, params=params)

if __name__ == "__main__":
    send_update()