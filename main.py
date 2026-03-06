import os, json, urllib.request

TOKEN = os.environ["TELEGRAM_TOKEN"]
GEMINI_KEY = os.environ["GEMINI_API_KEY"]
TG = f"https://api.telegram.org/bot{TOKEN}"
contexts = {}

def tg(method, data=None):
    url = f"{TG}/{method}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers={"Content-Type":"application/json"} if body else {})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
    except: return None

def send(chat_id, text):
    for i in range(0, len(text), 4000):
        tg("sendMessage", {"chat_id": chat_id, "text": text[i:i+4000]})

def typing(chat_id):
    tg("sendChatAction", {"chat_id": chat_id, "action": "typing"})

def gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    data = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=60).read().decode())
        return resp["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"Error: {e}"

def analyze(stock, mode="full"):
    if mode == "full":
        prompt = f"Tu StockSensei hai India ka best swing trading expert. Hinglish mein baat kar.\n\n{stock} ka full analysis karo NSE par:\n\nSIGNAL: [STRONG BUY/BUY/NEUTRAL/SELL]\nTechnical Score: [0-100]\nFundamental Score: [0-100]\nRisk: [LOW/MEDIUM/HIGH]\n\nTECHNICAL:\n- Trend aur price action\n- Support/Resistance (rupees)\n- RSI, MACD\n- Chart pattern\n\nFUNDAMENTAL:\n- Business strength\n- Valuation P/E\n- Promoter holding\n- Growth outlook\n\nTRADE SETUP:\n- Entry zone (rupees)\n- Target 1 aur Target 2 (rupees)\n- Stop Loss (rupees)\n- Risk:Reward\n- Timeframe\n\nVERDICT: 3 lines direct call."
    elif mode == "technical":
        prompt = f"Tu StockSensei hai. {stock} ka technical analysis karo. Hinglish mein. Score, Signal, Trend, Support, Resistance, RSI, MACD, Pattern, Entry, Targets, SL, R:R."
    elif mode == "swing":
        prompt = f"Tu StockSensei hai. {stock} ka best swing trade setup do. Hinglish mein. Signal, Confidence, Risk, Entry, T1, T2, SL, R:R, Timeframe, Why NOW?"
    return gemini(prompt)

def handle(msg):
    cid = msg["chat"]["id"]
    txt = msg.get("text", "").strip()
    if not txt: return

    if txt == "/start":
        send(cid, "Namaste! StockSensei Bot mein swagat!\n\nUse karo:\n- RELIANCE seedha likho\n- /analyze TCS\n- /technical WIPRO\n- /swing HDFC BANK\n- /scan aaj ke top trades")
        return

    if txt == "/help":
        send(cid, "Commands:\nRELIANCE - full analysis\n/analyze STOCK\n/technical STOCK\n/swing STOCK\n/scan - top 5 trades")
        return

    if txt == "/scan":
        typing(cid)
        result = gemini("Tu StockSensei hai. NSE par aaj ke TOP 5 swing trades batao. March 2026. Har ek: naam, signal, entry rupees, target, SL, 2-line reason. Hinglish mein.")
        send(cid, "Top Opportunities:\n\n" + result)
        return

    if txt.startswith("/analyze "):
        stock = txt[9:].strip().upper()
        typing(cid); send(cid, f"{stock} analyze ho raha hai..."); typing(cid)
        r = analyze(stock, "full")
        contexts[cid] = {"stock": stock, "analysis": r}
        send(cid, f"{stock} Analysis:\n\n{r}")
        return

    if txt.startswith("/technical "):
        stock = txt[11:].strip().upper()
        typing(cid)
        r = analyze(stock, "technical")
        contexts[cid] = {"stock": stock, "analysis": r}
        send(cid, f"{stock} Technical:\n\n{r}")
        return

    if txt.startswith("/swing "):
        stock = txt[7:].strip().upper()
        typing(cid)
        r = analyze(stock, "swing")
        contexts[cid] = {"stock": stock, "analysis": r}
        send(cid, f"{stock} Swing Setup:\n\n{r}")
        return

    words = txt.split()
    is_stock = (not txt.startswith("/")) and (
        (len(words)==1 and len(txt)<=20 and txt.replace(" ","").isalpha()) or
        (len(words)<=3 and any(w.upper() in ["BANK","LTD","MOTORS","INDUSTRIES","TECH","FINANCE"] for w in words))
    )
    if is_stock:
        s = txt.upper()
        typing(cid); send(cid, f"{s} analyze ho raha hai..."); typing(cid)
        r = analyze(s, "full")
        contexts[cid] = {"stock": s, "analysis": r}
        send(cid, f"{s} Analysis:\n\n{r}")
        return

    if cid in contexts:
        ctx = contexts[cid]
        typing(cid)
        r = gemini(f"Tu StockSensei hai. {ctx['stock']} analysis:\n{ctx['analysis']}\n\nSawaal: {txt}\n\nHinglish mein 150 words jawab do.")
        send(cid, r)
        return

    typing(cid); send(cid, f"{txt.upper()} analyze ho raha hai..."); typing(cid)
    r = analyze(txt.upper(), "full")
    contexts[cid] = {"stock": txt.upper(), "analysis": r}
    send(cid, f"{txt.upper()} Analysis:\n\n{r}")

def main():
    print("StockSensei starting...")
    me = tg("getMe")
    if me and me.get("ok"):
        print(f"Connected: @{me['result']['username']}")
    else:
        print("Token error!"); return
    offset = 0
    while True:
        try:
            updates = tg("getUpdates", {"offset":offset,"timeout":30,"allowed_updates":["message"]})
            if not updates or not updates.get("ok"): continue
            for u in updates.get("result",[]):
                offset = u["update_id"] + 1
                if "message" in u:
                    try: handle(u["message"])
                    except Exception as e: print(f"Error: {e}")
        except KeyboardInterrupt: break
        except Exception as e: print(f"Error: {e}")

if __name__ == "__main__":
    main()
