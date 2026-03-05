
import os, json, urllib.request

TOKEN = os.environ["TELEGRAM_TOKEN"]
AKEY = os.environ["ANTHROPIC_API_KEY"]
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
        tg("sendMessage", {"chat_id": chat_id, "text": text[i:i+4000], "parse_mode": "Markdown"})

def typing(chat_id):
    tg("sendChatAction", {"chat_id": chat_id, "action": "typing"})

def claude(messages, system):
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps({"model":"claude-haiku-4-5-20251001","max_tokens":1500,"system":system,"messages":messages}).encode(),
        headers={"Content-Type":"application/json","x-api-key":AKEY,"anthropic-version":"2023-06-01"}
    )
    try:
        return json.loads(urllib.request.urlopen(req, timeout=60).read().decode())["content"][0]["text"]
    except Exception as e:
        return f"Error: {e}"

def analyze(stock, mode="full"):
    prompts = {
        "full": f"{stock} ka full swing trade analysis karo NSE par. Hinglish mein:\n\n🎯 SIGNAL: [STRONG BUY/BUY/NEUTRAL/SELL]\n📊 Technical Score: [0-100]\n💰 Fundamental Score: [0-100]\n⚠️ Risk: [LOW/MEDIUM/HIGH]\n\n📈 TECHNICAL:\n• Trend aur price action\n• Support / Resistance (₹)\n• RSI, MACD\n• Chart pattern\n\n💵 FUNDAMENTAL:\n• Business strength\n• Valuation P/E\n• Promoter holding\n• Growth outlook\n\n🎯 TRADE SETUP:\n• Entry zone (₹)\n• Target 1 aur Target 2 (₹)\n• Stop Loss (₹)\n• Risk:Reward\n• Timeframe\n\n✅ VERDICT: 3 lines direct call.",
        "technical": f"{stock} ka TECHNICAL analysis. Hinglish mein. Score, Signal, Trend, Support, Resistance, RSI, MACD, Pattern, Entry, Targets, SL, R:R.",
        "swing": f"{stock} ka SWING TRADE setup. Hinglish mein. Signal, Confidence, Risk, Entry, T1, T2, SL, R:R, Timeframe, Position size, Why NOW?"
    }
    return claude([{"role":"user","content":prompts.get(mode,prompts["full"])}],
        "Tu StockSensei hai — India ka best swing trading expert. Hinglish mein baat kar. Specific price levels de. Direct aur actionable reh.")

def handle(msg):
    cid = msg["chat"]["id"]
    txt = msg.get("text","").strip()
    if not txt: return

    if txt == "/start":
        send(cid, "🚀 *StockSensei Bot mein swagat!*\n\nMain AI-powered swing trading assistant hun.\n\n*Use karo:*\n• `RELIANCE` — seedha naam likho\n• `/analyze TCS` — full analysis\n• `/technical WIPRO` — technical only\n• `/swing HDFC BANK` — swing setup\n• `/scan` — aaj ke top 5 trades\n• `/help` — sab commands\n\n_Sirf educational. Apni research zaroor karo._")
        return

    if txt == "/help":
        send(cid, "📖 *Commands:*\n\n`RELIANCE` — full analysis\n`/analyze STOCK` — full\n`/technical STOCK` — technical\n`/swing STOCK` — swing setup\n`/scan` — top opportunities\n\nAnalysis ke baad follow-up sawaal poochein!")
        return

    if txt == "/scan":
        typing(cid)
        send(cid, "🔍 Scanning...")
        result = claude([{"role":"user","content":"NSE par aaj ke TOP 5 swing trades batao. March 2026. Har ek: naam, signal, entry, target, SL, 2-line reason. Hinglish mein."}],
            "StockSensei. Expert Indian trader. Hinglish mein.")
        send(cid, f"⚡ *Top Opportunities:*\n\n{result}")
        return

    if txt.startswith("/analyze "):
        stock = txt[9:].strip().upper()
        typing(cid); send(cid, f"_{stock} analyze ho raha hai..._"); typing(cid)
        r = analyze(stock, "full")
        contexts[cid] = {"stock":stock,"analysis":r,"history":[]}
        send(cid, f"📈 *{stock}*\n\n{r}")
        return

    if txt.startswith("/technical "):
        stock = txt[11:].strip().upper()
        typing(cid); send(cid, f"_{stock}..._"); typing(cid)
        r = analyze(stock, "technical")
        contexts[cid] = {"stock":stock,"analysis":r,"history":[]}
        send(cid, f"📉 *{stock} Technical*\n\n{r}")
        return

    if txt.startswith("/swing "):
        stock = txt[7:].strip().upper()
        typing(cid); send(cid, f"_{stock}..._"); typing(cid)
        r = analyze(stock, "swing")
        contexts[cid] = {"stock":stock,"analysis":r,"history":[]}
        send(cid, f"🎯 *{stock} Swing Setup*\n\n{r}")
        return

    words = txt.split()
    is_stock = (not txt.startswith("/")) and (
        (len(words)==1 and len(txt)<=20 and txt.replace(" ","").isalpha()) or
        (len(words)<=3 and any(w.upper() in ["BANK","LTD","MOTORS","INDUSTRIES","TECH","FINANCE"] for w in words))
    )
    if is_stock:
        s = txt.upper()
        typing(cid); send(cid, f"_{s} analyze ho raha hai..._"); typing(cid)
        r = analyze(s, "full")
        contexts[cid] = {"stock":s,"analysis":r,"history":[]}
        send(cid, f"📈 *{s}*\n\n{r}")
        return

    if cid in contexts:
        ctx = contexts[cid]
        typing(cid)
        h = ctx["history"] + [{"role":"user","content":txt}]
        r = claude(h, f"StockSensei. Context:\n{ctx['stock']}\n{ctx['analysis']}\nHinglish, 150 words max.")
        ctx["history"] = (h + [{"role":"assistant","content":r}])[-6:]
        send(cid, r)
        return

    typing(cid); send(cid, f"_{txt.upper()} analyze ho raha hai..._"); typing(cid)
    r = analyze(txt.upper(), "full")
    contexts[cid] = {"stock":txt.upper(),"analysis":r,"history":[]}
    send(cid, f"📈 *{txt.upper()}*\n\n{r}")

def main():
    print("StockSensei Bot starting...")
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
