#!/bin/bash
# استارت ایدمپوتنت بله — لاگ در ~/.cache/bale-wrapper/launcher.log
export DISPLAY=${DISPLAY:-:0}
export XAUTHORITY=${XAUTHORITY:-$HOME/.Xauthority}
cd /home/hamidi/apps/bale-wrapper
LOG="$HOME/.cache/bale-wrapper/launcher.log"

if ! pgrep -x electron >/dev/null 2>&1; then
  nohup ./node_modules/electron/dist/electron --no-sandbox . "$@" >>"$LOG" 2>&1 &
  echo "$(date +%T) electron spawn pid=$!" >>"$LOG"
else
  echo "$(date +%T) electron از قبل بود" >>"$LOG"
fi
sleep 2
if ! pgrep -f "bale-wrapper/tray[.]py" >/dev/null 2>&1; then
  nohup python3 /home/hamidi/apps/bale-wrapper/tray.py >>"$LOG" 2>&1 &
  echo "$(date +%T) tray spawn pid=$!" >>"$LOG"
else
  echo "$(date +%T) tray از قبل بود" >>"$LOG"
fi
exit 0
