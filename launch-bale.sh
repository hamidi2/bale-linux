#!/bin/bash
# استارت ایدمپوتنت: هرکدام از پروسه‌ها نبود، بالا بیاورد (بدون کشتن هیچ‌چیز)
export DISPLAY=${DISPLAY:-:0}
export XAUTHORITY=${XAUTHORITY:-$HOME/.Xauthority}
cd /home/hamidi/apps/bale-wrapper
pgrep -x electron >/dev/null || ./node_modules/electron/dist/electron --disable-gpu-sandbox . "$@" &
sleep 3
pgrep -f "bale-wrapper/tray[.]py" >/dev/null || python3 /home/hamidi/apps/bale-wrapper/tray.py >/dev/null 2>&1 &
disown -a
