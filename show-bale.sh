#!/bin/bash
# فقط سیگنال show به الکترون (بدون دست زدن به tray!)
export DISPLAY=${DISPLAY:-:0}
cd "$(dirname "$(readlink -f "$0")")"
exec ./node_modules/electron/dist/electron --no-sandbox . >/dev/null 2>&1
