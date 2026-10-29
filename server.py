import http.server as h, subprocess as sp, os, json, time, random, atexit, shlex, threading

D = os.path.expanduser("~/sp")
CF = D + "/config.json"
HOST = "127.0.0.1"
PORT = int(open(D + "/port").read().strip())
S = {"p": None, "ip": None, "err": None}


def sh(c):
    return sp.run(c, shell=True, capture_output=True, text=True).stdout.strip()


atexit.register(lambda: sh("pkill -x aether"))


def cmd(p):
    a = shlex.split(json.load(open(CF))["aetherCommand"])
    o, i = [], 0
    while i < len(a):
        if a[i] == "--upstream":
            i += 2
        elif a[i] == "--bind":
            o += ["--bind", f"127.0.0.1:{p}"]
            i += 2
        else:
            o.append(a[i])
            i += 1
    return o


def watch(p):
    for _ in range(35):
        time.sleep(3)
        if not sh("pgrep -x aether"):
            S["err"] = "❌ aether بسته شد\n" + sh(f"tail -4 {D}/aether.log")
            return
        t = sh(f"curl -m 8 -s -x socks5h://127.0.0.1:{p} https://www.cloudflare.com/cdn-cgi/trace")
        for ln in t.splitlines():
            if ln.startswith("ip="):
                S["ip"] = ln[3:]
                return
    S["err"] = "❌ وصل نشد (زمان تمام شد)\n" + sh(f"tail -4 {D}/aether.log")


def proxy():
    if not os.path.exists(CF):
        return {"t": "❌ config.json نیست. کد نصب را دوباره بزن."}
    p = random.randint(40000, 60000)
    try:
        c = cmd(p)
    except Exception:
        return {"t": "❌ config.json خراب است."}
    sh("pkill -x aether")
    time.sleep(1)
    os.makedirs(D + "/data", exist_ok=True)
    try:
        sp.Popen(c, cwd=D + "/data", stdin=sp.DEVNULL,
                 stdout=open(D + "/aether.log", "w"), stderr=sp.STDOUT)
    except FileNotFoundError:
        return {"t": "❌ aether نصب نیست. کد نصب را دوباره بزن."}
    S.update(p=p, ip=None, err=None)
    threading.Thread(target=watch, args=(p,), daemon=True).start()
    return {"t": "⏳ در حال پیدا کردن مسیر... (تا یک‌ونیم دقیقه ممکن است طول بکشد)", "wait": 1}


def status():
    if S["ip"]:
        p = S["p"]
        return {"done": 1, "t": f"✅ پروکسی SOCKS5 ساخته شد\nsocks5://127.0.0.1:{p}\nIP: {S['ip']}",
                "tg": f"https://t.me/socks?server=127.0.0.1&port={p}"}
    if S["err"]:
        return {"done": 1, "t": S["err"]}
    return {"done": 0}


def conf():
    p = S["p"] or random.randint(40000, 60000)
    j = json.dumps(json.load(open(CF)), indent=1, ensure_ascii=False).replace("10819", str(p))
    return {"t": f"socks5://127.0.0.1:{p}\n\n{j}"}


class R(h.BaseHTTPRequestHandler):
    log_message = lambda *a: 0

    def allowed(self):
        hs = (f"127.0.0.1:{PORT}", f"localhost:{PORT}")
        o = self.headers.get("Origin")
        return self.headers.get("Host", "") in hs and ((not o) or o in tuple("http://" + x for x in hs))

    def out(self, body, ctype, code=200):
        b = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if not self.allowed():
            return self.out("forbidden", "text/plain", 403)
        if self.path == "/status":
            return self.out(json.dumps(status()), "application/json")
        self.out(open(D + "/index.html", encoding="utf-8").read(), "text/html")

    def do_POST(self):
        if not self.allowed():
            return self.out("forbidden", "text/plain", 403)
        if self.path == "/proxy":
            d = proxy()
        elif self.path == "/config":
            d = conf()
        else:
            sh("pkill -x aether")
            S.update(p=None, ip=None, err=None)
            d = {"t": "⛔ خاموش شد"}
        self.out(json.dumps(d), "application/json")


URL = f"http://{HOST}:{PORT}"
print(f"\n🛡️ Spaedr ir panel\nآدرس پنل (خودکار باز می‌شود):\n\n   {URL}\n\nبرای خروج: Ctrl+C\n")


def opener():
    time.sleep(1.5)
    try:
        sp.run(["termux-open-url", URL], timeout=10)
    except Exception:
        pass


threading.Thread(target=opener, daemon=True).start()
h.ThreadingHTTPServer((HOST, PORT), R).serve_forever()
