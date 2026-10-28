import http.server as h, subprocess as sp, os, json, time, random, atexit

D = os.path.expanduser("~/sp")
C = D + "/c.json"
X = D + "/xray/xray"
HOST = "127.0.0.1"
PORT = int(open(D + "/port").read().strip())
cur = [10808]


def sh(c):
    return sp.run(c, shell=True, capture_output=True, text=True).stdout.strip()


atexit.register(lambda: sh("pkill -x xray"))


def proxy():
    if not os.path.exists(C):
        return {"t": "❌ فایل ~/sp/c.json نیست. اول کانفیگ سرورت را در این مسیر بگذار."}
    p = random.randint(40000, 60000)
    c = json.load(open(C))
    c["inbounds"][0]["port"] = p
    json.dump(c, open(C, "w"))
    sh("pkill -x xray")
    time.sleep(1)
    sp.Popen([X, "run", "-c", C],
             env={**os.environ, "XRAY_LOCATION_ASSET": D + "/xray"},
             stdout=open(D + "/x.log", "w"), stderr=sp.STDOUT)
    time.sleep(3)
    cur[0] = p
    ip = sh(f"curl -m 10 -s -x socks5h://127.0.0.1:{p} https://api.ipify.org")
    if not ip:
        return {"t": "❌ وصل نشد\n" + sh(f"tail -3 {D}/x.log")}
    return {"t": f"✅ پروکسی SOCKS5 ساخته شد\nsocks5://127.0.0.1:{p}\nIP: {ip}",
            "tg": f"https://t.me/socks?server=127.0.0.1&port={p}"}


def conf():
    p = cur[0]
    j = json.dumps({"remarks": "Spaedr ir SOCKS5",
                    "outbounds": [{"protocol": "socks",
                                   "settings": {"servers": [{"address": "127.0.0.1", "port": p}]}}]},
                   indent=1)
    return {"t": f"socks://127.0.0.1:{p}#Spaedr-ir\n\n{j}"}


class R(h.BaseHTTPRequestHandler):
    log_message = lambda *a: 0

    def out(self, body, ctype):
        b = body.encode()
        self.send_response(200)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        self.out(open(D + "/index.html", encoding="utf-8").read(), "text/html")

    def do_POST(self):
        if self.path == "/proxy":
            d = proxy()
        elif self.path == "/config":
            d = conf()
        else:
            sh("pkill -x xray")
            d = {"t": "⛔ خاموش شد"}
        self.out(json.dumps(d), "application/json")


print("\n🛡️ Spaedr ir panel")
print("آی‌پی و پورت پنل (در مرورگر گوشی باز کن):\n")
print(f"   http://{HOST}:{PORT}\n")
print("برای خروج: Ctrl+C\n")
h.ThreadingHTTPServer((HOST, PORT), R).serve_forever()
