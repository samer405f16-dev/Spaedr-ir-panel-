import http.server as h, subprocess as sp, os, json, time, random, atexit, shlex, threading, socket

D = os.path.expanduser("~/spl")
HOST = "127.0.0.1"
NAME = "S.p.e.d.r.n.g.localhost"
CMD = ("aether --bind 127.0.0.1:{P} --protocol mim --scan balanced --ip v4 --masque-sni www.cloudflare.com --h2 "
       "--tls-ciphers ALL:!aPSK:!ECDSA+SHA1:!3DES --tls-groups X25519MLKEM768:X25519:P-256:P-384 "
       "--tls-sigalgs mldsa44:mldsa65:mldsa87:ecdsa_secp256r1_sha256:rsa_pss_rsae_sha256:rsa_pkcs1_sha256:ecdsa_secp384r1_sha384:rsa_pss_rsae_sha384:rsa_pkcs1_sha384:rsa_pss_rsae_sha512:rsa_pkcs1_sha512 "
       "--tls-cert-compression brotli --tls-alps new "
       "--tls-trust-anchors 44947.2.1:44947.2.6:44947.2.13:44947.2.14:44947.2.15:44947.2.18:44947.2.19:44947.2.20:52580.200109.1.7:52580.200109.1.8:52580.200109.1.9:52580.200109.1.10:52580.200109.1.11:52580.200109.1.12:52580.200109.1.13:52580.200109.1.18:52580.200109.1.19:11129.9.1:11129.9.4:11129.9.5:11129.9.6:11129.9.7:11129.9.8:11129.9.10:11129.9.11:11129.9.12:11129.9.13:11129.9.15 "
       "--tls-server-padding 6000 --enable-grease-sigalgs --enable-ech-grease "
       "--mim-outer 162.159.198.82:443 --mim-inner 162.159.198.192:443 --quick-reconnect")
S = {"p": None, "ip": None, "err": None}
PROC = [None]


def sh(c):
    return sp.run(c, shell=True, capture_output=True, text=True).stdout.strip()


def killall():
    pr = PROC[0]
    if pr is not None and pr.poll() is None:
        pr.terminate()
        try:
            pr.wait(3)
        except Exception:
            pr.kill()
    sh("pkill -x aether")


atexit.register(killall)


def pick(lo, hi, ex=()):
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


PORT = pick(20000, 40000)


def watch(p):
    for _ in range(35):
        time.sleep(3)
        pr = PROC[0]
        if pr is None or pr.poll() is not None:
            S["err"] = f"❌ aether بسته شد (کد {pr.returncode if pr else '?'})\n" + sh(f"tail -4 {D}/aether.log")
            return
        t = sh(f"curl -m 8 -s -x socks5h://127.0.0.1:{p} https://www.cloudflare.com/cdn-cgi/trace")
        for ln in t.splitlines():
            if ln.startswith("ip="):
                S["ip"] = ln[3:]
                return
    S["err"] = "❌ وصل نشد (زمان تمام شد)\n" + sh(f"tail -4 {D}/aether.log")


def proxy():
    p = pick(40000, 60000, (PORT,))
    killall()
    time.sleep(1)
    os.makedirs(D + "/data", exist_ok=True)
    try:
        PROC[0] = sp.Popen(shlex.split(CMD.replace("{P}", str(p))), cwd=D + "/data", stdin=sp.DEVNULL,
                           stdout=open(D + "/aether.log", "w"), stderr=sp.STDOUT)
    except FileNotFoundError:
        return {"t": "❌ aether نصب نیست. کد نصب را دوباره بزن."}
    S.update(p=p, ip=None, err=None)
    threading.Thread(target=watch, args=(p,), daemon=True).start()
    return {"t": "⏳ در حال ساخت پروکسی... (تا یک‌ونیم دقیقه)", "wait": 1}


def status():
    if S["ip"]:
        p = S["p"]
        return {"done": 1, "t": f"✅ پروکسی SOCKS5 آماده است\n\nآی‌پی: 127.0.0.1\nپورت: {p}\n\nsocks5://127.0.0.1:{p}",
                "tg": f"https://t.me/socks?server=127.0.0.1&port={p}"}
    if S["err"]:
        return {"done": 1, "t": S["err"]}
    return {"done": 0}


class R(h.BaseHTTPRequestHandler):
    log_message = lambda *a: 0

    def allowed(self):
        hs = (f"127.0.0.1:{PORT}", f"localhost:{PORT}", f"{NAME.lower()}:{PORT}")
        o = (self.headers.get("Origin") or "").lower()
        return self.headers.get("Host", "").lower() in hs and ((not o) or o in tuple("http://" + x for x in hs))

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
        else:
            killall()
            S.update(p=None, ip=None, err=None)
            d = {"t": "⛔ خاموش شد"}
        self.out(json.dumps(d), "application/json")


URL = f"http://{NAME}:{PORT}"
print(f"\n🛡️ Spaedr ng\nآدرس (خودکار باز می‌شود):\n\n   {URL}\n\nاگر باز نشد:\n   http://{HOST}:{PORT}\n\nبرای خروج: Ctrl+C\n")


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
    print("\n" + s.get("t", "⏳ هنوز آماده نیست، صفحه را باز کن") + "\n")
    if s.get("tg"):
        print("لینک افزودن به تلگرام:\n" + s["tg"] + "\n")


threading.Thread(target=opener, daemon=True).start()
threading.Thread(target=auto, daemon=True).start()
h.ThreadingHTTPServer((HOST, PORT), R).serve_forever()
