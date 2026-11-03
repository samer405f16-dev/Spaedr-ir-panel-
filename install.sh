#!/data/data/com.termux/files/usr/bin/bash
# Spaedr ng lite installer (proxy only, no config needed)
R="https://raw.githubusercontent.com/samer405f16-dev/Spaedr-ir-panel-/main/lite"

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

mkdir -p ~/spl/data && cd ~/spl
for f in server.py index.html; do curl -sL "$R/$f" -o "$f"; done

echo 'pkill -f spl/server.py; pkill -x aether; sleep 1; termux-wake-lock; python ~/spl/server.py' > $PREFIX/bin/spaedr
chmod +x $PREFIX/bin/spaedr

termux-wake-lock
exec python server.py
