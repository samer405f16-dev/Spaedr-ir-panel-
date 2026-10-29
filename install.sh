#!/data/data/com.termux/files/usr/bin/bash
# Spaedr ir panel installer
R="https://raw.githubusercontent.com/samer405f16-dev/Spaedr-ir-panel-/main"

mkdir -p /data/data/com.termux/cache/apt/archives/partial 2>/dev/null
for t in curl wget unzip; do command -v $t >/dev/null || pkg install -y $t; done

if ! command -v python >/dev/null; then
  pkg install -y python || {
    mkdir -p ~/.apt/archives/partial
    apt-get -o Dir::Cache=$HOME/.apt -o Dir::Cache::archives=$HOME/.apt/archives \
      -o Dir::Cache::pkgcache= -o Dir::Cache::srcpkgcache= install -y python
  }
fi

mkdir -p ~/sp/data && cd ~/sp
for f in server.py index.html config.json; do curl -sL "$R/$f" -o "$f"; done
[ -f port ] || echo $((20000 + RANDOM % 20000)) > port

if grep -q aetherCommand config.json; then
  command -v aether >/dev/null || {
    cd ~
    curl -fsSL https://raw.githubusercontent.com/CluvexStudio/aether/main/aether.sh -o aether.sh \
      && chmod +x aether.sh && ./aether.sh install
    cd ~/sp
  }
else
  [ -f xray/xray ] || {
    wget -qO x.zip https://github.com/XTLS/Xray-core/releases/latest/download/Xray-android-arm64-v8a.zip \
    && unzip -qo x.zip -d xray && chmod +x xray/xray
  }
fi

echo 'pkill -f sp/server.py; pkill -x aether; pkill -x xray; sleep 1; termux-wake-lock; python ~/sp/server.py' > $PREFIX/bin/panel
chmod +x $PREFIX/bin/panel

termux-wake-lock
exec python server.py
