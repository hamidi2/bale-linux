#!/usr/bin/env python3
# آیکون tray بله — Gtk.StatusIcon
# کلیک چپ: مخفی→نمایش+فوکوس | نمایان بی‌فوکوس→فوکوس | نمایان فوکوس→مخفی (منطق تلگرام)
# شمارنده: title پنجره (xprop -id) — حتی وقتی مخفی
import subprocess, re, time
from pathlib import Path
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

BASE = Path.home() / 'apps' / 'bale-wrapper'

def icon_path(n):
    if n > 0:
        dot = BASE / 'badges' / 'badge-dot.png'
        if dot.exists(): return str(dot)
    return str(BASE / 'badges' / 'badge-0.png')

def get_wid():
    """پنجره با WM_CLASS='bale-wrapper' — بعد از hide هم در tree هست (unmapped)"""
    out = subprocess.run(['xwininfo', '-root', '-tree'], capture_output=True, text=True).stdout
    for line in out.splitlines():
        if '"bale-wrapper"' in line:
            return line.split()[0]
    return None

def win_state(wid):
    r = subprocess.run(['xprop', '-id', wid, 'WM_STATE'], capture_output=True, text=True)
    m = re.search(r'window state:\s*(\w+)', r.stdout)
    return m.group(1) if m else 'gone'

def is_focused(wid):
    r = subprocess.run(['xprop', '-root', '_NET_ACTIVE_WINDOW'], capture_output=True, text=True)
    m = re.search(r'window id # (0x[0-9a-f]+)', r.stdout)
    return bool(m) and int(m.group(1), 16) == int(wid, 16)

def toggle(*a):
    wid = get_wid()
    if not wid:
        subprocess.Popen(['systemctl', '--user', 'restart', 'bale.service'])
        return
    st = win_state(wid)
    if st == 'Withdrawn':   # مخفی
        subprocess.Popen([str(BASE / 'show-bale.sh')],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif is_focused(wid):   # فوکوس بود → مخفی
        subprocess.run(['wmctrl', '-ic', wid])
    else:                   # نمایان بی‌فوکوس → فوکوس
        subprocess.run(['xdotool', 'windowactivate', wid])

def quit_all(*a):
    wid = get_wid()
    if wid and win_state(wid) != 'gone':
        subprocess.run(['wmctrl', '-ic', wid])
    GLib.idle_add(Gtk.main_quit)

icon = Gtk.StatusIcon.new_from_file(icon_path(0))
icon.set_tooltip_text('Bale')

def on_popup(si, button, time_):
    menu = Gtk.Menu()
    m1 = Gtk.MenuItem(label='بله — باز/بسته')
    m1.connect('activate', toggle)
    m2 = Gtk.MenuItem(label='خروج')
    m2.connect('activate', quit_all)
    menu.append(m1); menu.append(m2); menu.show_all()
    menu.popup(None, None, Gtk.StatusIcon.position_menu, si, button, time_)

import time as _time
_last_toggle = [0.0]
def toggle_debounced(*a):
    now = _time.time()
    if now - _last_toggle[0] < 0.7:   # دابل‌کلیک = دو activate پشت هم؛ فقط اولی عمل کند
        return
    _last_toggle[0] = now
    toggle(*a)
icon.connect('activate', toggle_debounced)
icon.connect('popup-menu', on_popup)

last = [-2]
last_nonzero = 0.0
def poll():
    global last, last_nonzero
    n = 0
    wid = get_wid()
    if wid:
        r = subprocess.run(['xprop', '-id', wid, '_NET_WM_NAME'], capture_output=True, text=True)
        m = re.search(r'=\s*"(.*)"\s*$', r.stdout)
        if m:
            mm = re.search(r'\((\d{1,4})\)\s*$', m.group(1))
            if mm: n = int(mm.group(1))
    # ضدفلیکر: وقتی پنجره باز می‌شود، بله یک لحظه title را بدون عدد می‌گذارد.
    # صفر را فقط ۴ ثانیه بعد از آخرین عددِ غیرصفر قبول کن.
    now = time.time()
    if n > 0:
        last_nonzero = now
    elif now - last_nonzero < 4:
        n = last[0] if last[0] > 0 else 0
    if n != last[0]:
        last[0] = n
        GLib.idle_add(icon.set_from_file, icon_path(n))
        GLib.idle_add(icon.set_tooltip_text, f'Bale — {n} unread' if n else 'Bale')
    return True

GLib.timeout_add_seconds(2, poll)
Gtk.main()
