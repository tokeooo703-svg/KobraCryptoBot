import requests
from datetime import datetime

# توكن البوت الخاص بك
TOKEN = "8005371069:AAE4exHBS-poluP5UBwClJh-_SOKrJgImIs"

# Chat ID الخاص بك (رقم محادثتك مع البوت)
CHAT_ID = "946090948"

def send_update():
    MESSAGE = f"""
📊 تحديث العملات الرقمية – {datetime.now().strftime('%Y-%m-%d')}:

- LTC: $60 | تحليل: مستقر، دعم 58$, مقاومة 62$
- NEAR: $1.20 | تحليل: صعودي متوسط، دعم 1.15$, مقاومة 1.25$
- DOGE: $0.065 | تحليل: تذبذب جانبي، دعم 0.062$, مقاومة 0.068$
- SHIB: $0.000008 | تحليل: ارتفاع طفيف، دعم 0.0000075$, مقاومة 0.0000085$
- ZEAL: $0.0035 | تحليل: كسر مقاومة قوي، متابعة لحركة السعر القادمة

⚡ تنبيهات فورية لأي حركة قوية أو كسر مستويات دعم/مقاومة.
"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": MESSAGE}
    requests.get(url, params=params)

if __name__ == "__main__":
    send_update()