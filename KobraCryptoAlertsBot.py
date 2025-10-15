import requests
import pandas as pd
from datetime import datetime

TOKEN = "8005371069:AAE4exHBS-poluP5UBwClJh-_SOKrJgImIs"
CHAT_ID = "946090948"

# العملات للتحديث اليومي
coins = {
    "litecoin": "LTC",
    "near": "NEAR",
    "dogecoin": "DOGE",
    "shiba-inu": "SHIB",
    "zeal": "ZEAL"
}

# العملات للتنبيه اللحظي
alert_coins = ["dogecoin", "zeal"]

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

def send_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": message}
    requests.get(url, params=params)

def daily_update():
    message_lines = [f"📊 تحديث العملات الرقمية – {datetime.now().strftime('%Y-%m-%d')}:"]
    for coin_id, symbol in coins.items():
        try:
            price, support, resistance = get_prices_and_levels(coin_id)
            message_lines.append(f"- {symbol}: ${price:.6f} | دعم: ${support:.6f}, مقاومة: ${resistance:.6f}")
        except:
            message_lines.append(f"- {symbol}: خطأ في جلب البيانات")
    message_lines.append("\n⚡ تنبيهات DOGE و ZEAL سيتم التحقق منها كل ساعة.")
    send_message("\n".join(message_lines))

def check_alerts():
    for coin_id in alert_coins:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": coin_id, "vs_currencies": "usd", "include_24hr_change": "true"}
        data = requests.get(url, params=params).json()
        current_price = data[coin_id]['usd']
        change_24h = data[coin_id]['usd_24h_change']
        if abs(change_24h) >= 5:  # تنبيه إذا التغير ≥ 5%
            trend = "صعود" if change_24h > 0 else "هبوط"
            message = f"⚡ تنبيه {coin_id.upper()} {trend} قوي: {change_24h:.2f}% خلال 24 ساعة.\nالسعر الحالي: ${current_price:.6f}\nوقت التحديث: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            send_message(message)

if __name__ == "__main__":
    daily_update()
    check_alerts()