# multi_kobra_bot.py - Refactor for python-telegram-bot v13
# - subscription/unsubscription handlers
# - JobQueue scheduling (python-telegram-bot v13)
# - HTTP retries (requests + urllib3 Retry)
# - atomic JSON writes for subscribers and alert state
# - limited concurrency broadcasting (ThreadPoolExecutor + Semaphore)
# - cooldowns persisted in alert_state.json
# - logging, no pandas dependency

import os
import json
import logging
import time
from pathlib import Path
from datetime import datetime, time as dt_time
from threading import Semaphore
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import pytz

# ---------- Logging ----------
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- Files & defaults ----------
SUB_FILE = Path('subscribers.json')
ALERT_STATE_FILE = Path('alert_state.json')
for p, default in [(SUB_FILE, []), (ALERT_STATE_FILE, {})]:
    if not p.exists():
        p.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding='utf-8')

# ---------- Configuration (use env vars) ----------
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')  # REQUIRED
ADMIN_ID = int(os.getenv('BOT_ADMIN_ID', '946090948'))
COINS = {'litecoin': 'LTC', 'near': 'NEAR', 'dogecoin': 'DOGE', 'shiba-inu': 'SHIB', 'zeal': 'ZEAL'}
ALERT_COINS = ['dogecoin', 'zeal']
ALERT_THRESHOLD_PERCENT = float(os.getenv('ALERT_THRESHOLD_PERCENT', '5.0'))
ALERT_COOLDOWN_MIN = int(os.getenv('ALERT_COOLDOWN_MIN', '120'))
DAILY_HOUR = int(os.getenv('DAILY_HOUR', '10'))
DAILY_MINUTE = int(os.getenv('DAILY_MINUTE', '0'))
TIMEZONE = os.getenv('TIMEZONE', 'Europe/Berlin')
BROADCAST_WORKERS = int(os.getenv('BROADCAST_WORKERS', '8'))
BROADCAST_CONCURRENCY = int(os.getenv('BROADCAST_CONCURRENCY', '8'))

# ---------- Helpers: atomic write ----------
def _atomic_write(path: Path, data: str):
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(data, encoding='utf-8')
    tmp.replace(path)

# ---------- Subscribers management ----------
def load_subs():
    try:
        return json.loads(SUB_FILE.read_text(encoding='utf-8'))
    except Exception as e:
        logger.warning('Failed to read subscribers.json: %s', e)
        return []

def save_subs(subs):
    _atomic_write(SUB_FILE, json.dumps(subs, ensure_ascii=False, indent=2))

def add_sub(chat_id):
    subs = load_subs()
    if chat_id not in subs:
        subs.append(chat_id)
        save_subs(subs)
        return True
    return False

def remove_sub(chat_id):
    subs = load_subs()
    if chat_id in subs:
        subs.remove(chat_id)
        save_subs(subs)
        return True
    return False

# ---------- Alert state ----------
def load_alert_state():
    try:
        return json.loads(ALERT_STATE_FILE.read_text(encoding='utf-8'))
    except Exception as e:
        logger.warning('Failed to read alert_state.json: %s', e)
        return {}

def save_alert_state(state):
    _atomic_write(ALERT_STATE_FILE, json.dumps(state, ensure_ascii=False, indent=2))

# ---------- HTTP session with retries ----------
def requests_session_with_retries(total_retries=3, backoff_factor=0.8, status_forcelist=(429, 500, 502, 503, 504)):
    s = requests.Session()
    retries = Retry(total=total_retries, backoff_factor=backoff_factor, status_forcelist=status_forcelist, allowed_methods=frozenset(['GET', 'POST']))
    adapter = HTTPAdapter(max_retries=retries)
    s.mount('https://', adapter)
    s.mount('http://', adapter)
    s.headers.update({'User-Agent': 'KobraCryptoBot/1.0'})
    return s

# ---------- CoinGecko data (no pandas) ----------
def get_prices_and_levels(coin_id, days=7, session=None):
    if session is None:
        session = requests_session_with_retries()
    url = f'https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart'
    params = {'vs_currency': 'usd', 'days': days}
    resp = session.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    prices = [p[1] for p in data.get('prices', [])]
    if not prices:
        raise ValueError('No price data')
    current_price = float(prices[-1])
    support = float(min(prices))
    resistance = float(max(prices))
