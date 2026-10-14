#!/bin/bash
# ساخت بستهٔ deb کامل بله — electron باندل‌شده، نصب و اجرای آفلاین
# کاربرد: ./build-deb.sh [version]
# node_modules از نصب موجود (~/.apps یا NODE_SRC=مسیر) برداشته می‌شود
set -e
VER="${1:-1.6.2}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
NODE_SRC="${NODE_SRC:-$HOME/apps/bale-wrapper/node_modules}"
[ -d "$NODE_SRC" ] || { echo "NODE_SRC not found: $NODE_SRC"; exit 1; }
PKG="$(mktemp -d)/bale-linux_${VER}_amd64"
mkdir -p "$PKG/DEBIAN" "$PKG/opt/bale-linux" "$PKG/usr/bin" \
         "$PKG/usr/lib/systemd/user" "$PKG/usr/share/applications" \
         "$PKG/usr/share/doc/bale-linux" "$PKG/etc/xdg/autostart"

# محتویات بسته از همین ریپو + node_modules و package.json از نصب موجود
cp "$ROOT"/{tray.py,main.js,make-badges.py,launch-bale.sh,show-bale.sh,bale.png,LICENSE,README.md} "$PKG/opt/bale-linux/"
[ -f "$ROOT/package.json" ] && cp "$ROOT/package.json" "$PKG/opt/bale-linux/" || cp "$(dirname "$NODE_SRC")/package.json" "$PKG/opt/bale-linux/"
cp -a "$ROOT/badges" "$PKG/opt/bale-linux/badges"
cp -a "$NODE_SRC" "$PKG/opt/bale-linux/node_modules"

# لانچر عمومی
cat > "$PKG/usr/bin/bale-linux" <<'EOF'
#!/bin/sh
exec /opt/bale-linux/node_modules/electron/dist/electron --no-sandbox --ozone-platform=x11 /opt/bale-linux "$@"
EOF
chmod +x "$PKG/usr/bin/bale-linux"

# یونیت‌های systemd --user با مسیر /opt
for u in bale.service bale-tray.service; do
  sed "s|%h/apps/bale-wrapper|/opt/bale-linux|g" "$ROOT/systemd/$u" > "$PKG/usr/lib/systemd/user/$u"
done

# لانچر منو
cat > "$PKG/usr/share/applications/bale-linux.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Bale
Comment=Unofficial Bale messenger (Electron wrapper)
Exec=bale-linux
Icon=/opt/bale-linux/bale.png
Terminal=false
Categories=Network;InstantMessaging;
EOF

# autostart سیستم‌گیرانه: هر سشن گرافیکی سرویس‌ها را بالا می‌آورد — نصب‌کننده هیچ کاری نمی‌کند
cat > "$PKG/etc/xdg/autostart/bale-linux.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Bale (bale-linux)
Comment=Start the bale services (tray + messenger)
Exec=systemctl --user start bale.service bale-tray.service
TryExec=systemctl
Terminal=false
X-GNOME-Autostart-enabled=true
EOF

cat > "$PKG/DEBIAN/control" <<EOF
Package: bale-linux
Version: $VER
Architecture: amd64
Maintainer: hamidi <hamidi@gmail.com>
Depends: python3, python3-gi, gir1.2-gtk-3.0, wmctrl, xdotool, x11-utils
Recommends: xfce4-panel
Section: net
Priority: optional
Description: Unofficial Bale messenger desktop client (XFCE/Xubuntu focused)
 Lightweight Electron wrapper around the official Bale web app with a
 tray icon (unread badge, three-state toggle, click-queue), close-to-tray
 and forced light theme. Electron is bundled: installs and runs fully
 offline. Built and tested on Xubuntu/XFCE; the tray needs a panel that
 hosts legacy XEmbed or SNI icons.
EOF

cat > "$PKG/DEBIAN/postinst" <<'EOF'
#!/bin/sh
# شروع فوری برای کسی که همین حالا با sudo در سشن گرافیکی نصب می‌کند (best-effort)
if [ -n "${SUDO_USER:-}" ] && [ -d "/run/user/$(id -u "$SUDO_USER" 2>/dev/null)" ]; then
  runuser -u "$SUDO_USER" -- systemctl --user enable --now bale.service bale-tray.service >/dev/null 2>&1 || true
fi
cat <<'MSG'

bale-linux نصب شد (/opt/bale-linux). از لاگین بعدی خودکار در tray است —
هیچ کار دستی لازم نیست. اجرا/بستن: آیکون tray یا منوی برنامه‌ها → Bale.
MSG
EOF
chmod +x "$PKG/DEBIAN/postinst"

cp "$ROOT/README.md" "$PKG/usr/share/doc/bale-linux/"

mkdir -p "$ROOT/dist"
dpkg-deb --build --root-owner-group "$PKG" "$ROOT/dist/bale-linux_${VER}_amd64.deb"
du -sh "$ROOT/dist/bale-linux_${VER}_amd64.deb"
