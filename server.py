import http.server as h, subprocess as sp, os, json, time, random, atexit, shlex, threading, copy, socket, secrets

D = os.path.expanduser("~/sp")
CF = D + "/config.json"
RUN = D + "/run.json"
X = D + "/xray/xray"
HOST = "127.0.0.1"
NAME = "S.p.e.d.r.n.g.localhost"


def pick(lo=20000, hi=40000, ex=()):
    while True:
        p = random.randint(lo, hi)
        if p in ex:
            continue
        s = socket.socket()
        try:
            s.bind((HOST, p))
            return p
        except OSError:
            pass
        finally:
            s.close()


PORT = pick()
TOKEN = secrets.token_urlsafe(9)
SITE = "https://samer405f16-dev.github.io"
SITE_URL = SITE + f"/Spaedr-ir-panel-/#p={PORT}&t={TOKEN}"
S = {"p": None, "c": None, "ip": None, "err": None, "n": "xray"}


def sh(c):
    return sp.run(c, shell=True, capture_output=True, text=True).stdout.strip()


PROC = [None]


def killall():
    pr = PROC[0]
    if pr is not None and pr.poll() is None:
        pr.terminate()
        try:
            pr.wait(3)
        except Exception:
            pr.kill()
    sh("pkill -x aether; pkill -x xray")


atexit.register(killall)


def load():
    return json.load(open(CF))


def is_aether(c):
    return "aetherCommand" in c


def acmd(c, p):
    a = shlex.split(c["aetherCommand"])
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


def withport(c, p, cp=None):
    c = copy.deepcopy(c)
    for ib in c.get("inbounds", []):
        if ib.get("tag") == "mixed-in" or ib.get("protocol") in ("mixed", "socks"):
            ib["port"] = p
            if cp:
                ib2 = copy.deepcopy(ib)
                ib2["tag"] = "mixed-in-2"
                ib2["port"] = cp
                c["inbounds"].append(ib2)
            break
    return c


def watch(p):
    n = S["n"]
    for _ in range(35):
        time.sleep(3)
        pr = PROC[0]
        if pr is None or pr.poll() is not None:
            rc = pr.returncode if pr is not None else "?"
            S["err"] = f"❌ {n} بسته شد (کد {rc})\n" + sh(f"tail -4 {D}/engine.log")
            return
        ip = ""
        if n == "aether":
            t = sh(f"curl -m 8 -s -x socks5h://127.0.0.1:{p} https://www.cloudflare.com/cdn-cgi/trace")
            ip = next((l[3:] for l in t.splitlines() if l.startswith("ip=")), "")
        else:
            t = sh(f"curl -m 8 -s -x socks5h://127.0.0.1:{p} https://api.ipify.org")
            ip = t if t and len(t) < 64 and "<" not in t else ""
        if ip:
            S["ip"] = ip
            return
    S["err"] = "❌ وصل نشد (زمان تمام شد)\n" + sh(f"tail -4 {D}/engine.log")


def proxy():
    if not os.path.exists(CF):
        return {"t": "❌ config.json نیست. کد نصب را دوباره بزن."}
    try:
        c = load()
    except Exception:
        return {"t": "❌ config.json خراب است."}
    p = pick(40000, 50000, (PORT,))
    cp = pick(50001, 60000, (PORT, p))
    killall()
    time.sleep(1)
    log = open(D + "/engine.log", "w")
    try:
        if is_aether(c):
            S["n"] = "aether"
            os.makedirs(D + "/data", exist_ok=True)
            PROC[0] = sp.Popen(acmd(c, p), cwd=D + "/data", stdin=sp.DEVNULL, stdout=log, stderr=sp.STDOUT)
        else:
            S["n"] = "xray"
            json.dump(withport(c, p, cp), open(RUN, "w"))
            PROC[0] = sp.Popen([X, "run", "-c", RUN], stdin=sp.DEVNULL, stdout=log, stderr=sp.STDOUT,
                               env={**os.environ, "XRAY_LOCATION_ASSET": D + "/xray"})
    except Exception:
        return {"t": "❌ موتور نصب نیست. کد نصب را دوباره بزن."}
    S.update(p=p, c=(p if S["n"] == "aether" else cp), ip=None, err=None)
    threading.Thread(target=watch, args=(p,), daemon=True).start()
    return {"t": "⏳ در حال ساخت پروکسی... (چند ثانیه تا یک‌ونیم دقیقه)", "wait": 1}


def status():
    if S["ip"]:
        p = S["p"]
        return {"done": 1,
                "t": f"✅ آماده است\n\n🔌 پروکسی تلگرام:\nsocks5://127.0.0.1:{p}\n\n📦 پورت کانفیگ:\nsocks5://127.0.0.1:{S['c']}\n\nIP: {S['ip']}",
                "tg": f"https://t.me/socks?server=127.0.0.1&port={p}"}
    if S["err"]:
        return {"done": 1, "t": S["err"]}
    return {"done": 0}


def conf():
    try:
        c = load()
    except Exception:
        return {"t": "❌ config.json خراب است."}
    p = S["c"] or S["p"] or pick(50001, 60000, (PORT,))
    if is_aether(c):
        j = json.dumps(c, indent=1, ensure_ascii=False).replace("10819", str(p))
    else:
        j = json.dumps(withport(c, p), indent=1, ensure_ascii=False)
    return {"t": f"socks5://127.0.0.1:{p}\n\n{j}"}


class R(h.BaseHTTPRequestHandler):
    log_message = lambda *a: 0

    def allowed(self):
        hs = (f"127.0.0.1:{PORT}", f"localhost:{PORT}", f"{NAME.lower()}:{PORT}")
        o = (self.headers.get("Origin") or "").lower()
        if self.headers.get("Host", "").lower() not in hs:
            return False
        if not o or o in tuple("http://" + x for x in hs):
            return True
        return o == SITE and self.headers.get("X-Token") == TOKEN

    def do_OPTIONS(self):
        o = (self.headers.get("Origin") or "").lower()
        if o != SITE:
            return self.out("forbidden", "text/plain", 403)
        self.send_response(204)
        for k, v in (("Access-Control-Allow-Origin", SITE), ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
                     ("Access-Control-Allow-Headers", "X-Token, Content-Type"),
                     ("Access-Control-Allow-Private-Network", "true"),
                     ("Access-Control-Max-Age", "600"), ("Vary", "Origin")):
            self.send_header(k, v)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def out(self, body, ctype, code=200):
        b = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        if (self.headers.get("Origin") or "").lower() == SITE:
            self.send_header("Access-Control-Allow-Origin", SITE)
            self.send_header("Vary", "Origin")
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if not self.allowed():
            return self.out("forbidden", "text/plain", 403)
        if self.path == "/status":
            return self.out(json.dumps(status()), "application/json")
        if self.path == "/info":
            pr = PROC[0]
            return self.out(json.dumps({"panel": URL, "host": HOST, "tg": S["p"], "cfg": S["c"], "ip": S["ip"],
                                        "on": bool(pr is not None and pr.poll() is None), "err": S["err"]}),
                            "application/json")
        self.out(open(D + "/index.html", encoding="utf-8").read(), "text/html")

    def do_POST(self):
        if not self.allowed():
            return self.out("forbidden", "text/plain", 403)
        if self.path == "/proxy":
            d = proxy()
        elif self.path == "/config":
            d = conf()
        else:
            killall()
            S.update(p=None, ip=None, err=None)
            d = {"t": "⛔ خاموش شد"}
        self.out(json.dumps(d), "application/json")


URL = f"http://{NAME}:{PORT}"
print(f"\n🛡️ Spaedr ir panel\n🛡️ آدرس Spaedr ng (خودکار باز می‌شود):\n\n   {URL}\n\n🌐 لینک سایت (اختیاری):\n   {SITE_URL}\n\nبرای خروج: Ctrl+C\n")


def opener():
    time.sleep(1.5)
    try:
        sp.run(["termux-open-url", URL], timeout=10)
    except Exception:
        pass


def auto():
    proxy()
    for _ in range(40):
        time.sleep(3)
        if S["ip"] or S["err"]:
            break
    s = status()
    print("\n" + s.get("t", "⏳ هنوز آماده نیست، پنل را باز کن") + "\n")
    if s.get("tg"):
        print("لینک افزودن به تلگرام:\n" + s["tg"] + "\n")


threading.Thread(target=opener, daemon=True).start()
threading.Thread(target=auto, daemon=True).start()
h.ThreadingHTTPServer((HOST, PORT), R).serve_forever()
