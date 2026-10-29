#!/data/data/com.termux/files/usr/bin/bash
# Spaedr ir panel installer (Aether engine)
R="https://raw.githubusercontent.com/samer405f16-dev/Spaedr-ir-panel-/main"

mkdir -p /data/data/com.termux/cache/apt/archives/partial 2>/dev/null
command -v curl >/dev/null || pkg install -y curl

if ! command -v python >/dev/null; then
  pkg install -y python || {
    mkdir -p ~/.apt/archives/partial
    apt-get -o Dir::Cache=$HOME/.apt -o Dir::Cache::archives=$HOME/.apt/archives \
      -o Dir::Cache::pkgcache= -o Dir::Cache::srcpkgcache= install -y python
  }
fi

if ! command -v aether >/dev/null; then
  cd ~
  curl -fsSL https://raw.githubusercontent.com/CluvexStudio/aether/main/aether.sh -o aether.sh \
    && chmod +x aether.sh && ./aether.sh install
fi

mkdir -p ~/sp/data && cd ~/sp
for f in server.py index.html config.json; do curl -sL "$R/$f" -o "$f"; done
[ -f port ] || echo $((20000 + RANDOM % 20000)) > port

echo 'termux-wake-lock; python ~/sp/server.py' > $PREFIX/bin/panel
chmod +x $PREFIX/bin/panel

termux-wake-lock
exec python server.py
