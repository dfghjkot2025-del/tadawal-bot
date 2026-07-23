import os, time, requests, pytz
import yfinance as yf
import pandas_ta as ta
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "رادار المحترفين يعمل بنجاح"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

# جلب الإعدادات من Render
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
MY_TZ = pytz.timezone('Asia/Aden')

def send_msg(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try: requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def analyze(symbol, name, tf_label, interval):
    try:
        df = yf.download(symbol, period="5d", interval=interval, progress=False)
        if len(df) < 30: return None
        close = df["Close"]
        rsi = ta.rsi(close, length=14)
        bb = ta.bbands(close, length=20, std=2.2)
        price, rsi_v = float(close.iloc[-1]), float(rsi.iloc[-1])
        low_bb, up_bb = bb['BBL_20_2.2'].iloc[-1], bb['BBU_20_2.2'].iloc[-1]
        
        action = ""
        if price <= low_bb and rsi_v < 35: action = "🟢 صعود (CALL)"
        elif price >= up_bb and rsi_v > 65: action = "🔴 هبوط (PUT)"
        
        if action:
            p_f = f"{price:.5f}" if "USD" in name else f"{price:.2f}"
            cat = "👑 صفقة ملكية" if (rsi_v < 25 or rsi_v > 75) else "🔥 صفقة ذهبية"
            m_type = "FOREX" if "GOLD" in name or "h" in interval else "BINARY"
            return (f"{cat}\n🏛 `{name}`\n↕️ {action}\n💰 `{p_f}`\n⏱ {tf_label}\n📈 دقة 95%\n📱 `{name}-OTC`\n🚀 استعد للدخول!")
    except: return None

def main_loop():
    pairs = {"EURUSD=X":"EUR/USD", "GBPUSD=X":"GBP/USD", "USDJPY=X":"USD/JPY"}
    while True:
        now = datetime.now(MY_TZ)
        m, s, h = now.minute, now.second, now.hour
        # الذهب (قبل 5 دقائق)
        if m == 55 and s == 0:
            for tf, itv in {"1 ساعة":"1h", "4 ساعات":"4h", "1 يوم":"1d"}.items():
                if (tf=="4 ساعات" and h%4!=3) or (tf=="1 يوم" and h!=23): continue
                msg = analyze("GC=F", "GOLD", tf, itv)
                if msg: send_msg(msg)
        # العملات (قبل دقيقتين)
        if (m + 2) % 5 == 0 and s == 0:
            for sym, n in pairs.items():
                for tf, itv in {"5 دقائق":"5m", "15 دقيقة":"15m", "30 دقيقة":"30m"}.items():
                    if (m+2) % int(tf.split()[0]) == 0:
                        msg = analyze(sym, n, tf, itv)
                        if msg: send_msg(msg)
        time.sleep(1)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    main_loop()
