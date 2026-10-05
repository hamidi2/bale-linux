#!/usr/bin/env python3
# آیکون tray بله — Gtk.StatusIcon
# تشخیص پنجره فقط با window id ذخیره‌شده (هرگز با جستجوی title — بله‌ی داخل فایرفاکس را می‌دزدید!)
# کلیک: مخفی→نمایش | نمایان بی‌فوکوس→فوکوس | نمایان فوکوس→مخفی
# شمارنده: title همان پنجره (xprop -id) — حتی مخفی
import subprocess, re
from pathlib import Path
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

BASE = Path.home() / 'apps' / 'bale-wrapper'
STATE = Path.home() / '.cache' / 'bale-wrapper'
WID_FILE = STATE / 'wid'

def icon_path(n):
    if n > 0:
        dot = BASE / 'badges' / 'badge-dot.png'
        if dot.exists(): return str(dot)
    return str(BASE / 'badges' / 'badge-0.png')

def get_wid():
    try:
        wid = WID_FILE.read_text().strip()
        if wid.startswith('0x'):
            return wid
    except Exception:
        pass
    return None

def win_state(wid):
    """'visible' | 'hidden' | 'gone'"""
    r = subprocess.run(['xprop', '-id', wid, 'WM_STATE'],
                       capture_output=True, text=True)
    if r.returncode != 0 or 'no such window' in r.stderr.lower():
        return 'gone'
    m = re.search(r'window state:\s*(\w+)', r.stdout)
    if not m:
        return 'gone'
    return 'visible' if m.group(1) == 'Normal' else 'hidden'

def is_focused(wid):
    out = subprocess.run(['xprop', '-root', '_NET_ACTIVE_WINDOW'],
                         capture_output=True, text=True).stdout
    m = re.search(r'window id # (0x[0-9a-f]+)', out)
    return bool(m) and int(m.group(1), 16) == int(wid, 16)

def toggle(*a):
    wid = get_wid()
    if not wid or win_state(wid) == 'gone':
        # الکترون مرده → لانچر آن را بالا می‌آورد
        subprocess.Popen([str(BASE / 'show-bale.sh')],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return
    if win_state(wid) == 'hidden':
        subprocess.Popen([str(BASE / 'show-bale.sh')],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif is_focused(wid):
        subprocess.run(['wmctrl', '-i', '-c', wid])
    else:
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

icon.connect('activate', toggle)
icon.connect('popup-menu', on_popup)

last = [-2]
def poll():
    n = 0
    wid = get_wid()
    if wid:
        r = subprocess.run(['xprop', '-id', wid, '_NET_WM_NAME'],
                           capture_output=True, text=True)
        m = re.search(r'=\s*"(.*)"\s*$', r.stdout)
        if m:
            mm = re.search(r'\((\d{1,4})\)\s*$', m.group(1))
            if mm: n = int(mm.group(1))
    if n != last[0]:
        last[0] = n
        GLib.idle_add(icon.set_from_file, icon_path(n))
        GLib.idle_add(icon.set_tooltip_text, f'Bale — {n} unread' if n else 'Bale')
    return True

GLib.timeout_add_seconds(2, poll)
Gtk.main()
