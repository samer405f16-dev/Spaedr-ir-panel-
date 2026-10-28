#!/data/data/com.termux/files/usr/bin/bash
# Spaedr ir panel installer
R="https://raw.githubusercontent.com/USER/REPO/main"

mkdir -p /data/data/com.termux/cache/apt/archives/partial
command -v python >/dev/null || pkg install -y python
command -v wget >/dev/null || pkg install -y wget unzip curl

mkdir -p ~/sp && cd ~/sp
curl -sL "$R/server.py" -o server.py
curl -sL "$R/index.html" -o index.html

[ -f xray/xray ] || {
  wget -qO x.zip https://github.com/XTLS/Xray-core/releases/latest/download/Xray-android-arm64-v8a.zip \
  && unzip -qo x.zip -d xray && chmod +x xray/xray
}

[ -f port ] || echo $((20000 + RANDOM % 20000)) > port

echo 'termux-wake-lock; python ~/sp/server.py' > $PREFIX/bin/panel
chmod +x $PREFIX/bin/panel

termux-wake-lock
exec python server.py
