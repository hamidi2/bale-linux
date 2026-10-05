#!/usr/bin/env python3
# آیکون tray بله — Gtk.StatusIcon
# کلیک چپ: در taskbar نیست→نمایش+فوکوس | هست ولی فوکوس نیست→فوکوس | هست و فوکوس است→مخفی
# دایره قرمز برای نخوانده؛ تعداد در tooltip
import subprocess, re, re
from pathlib import Path
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

BASE = Path.home() / 'apps' / 'bale-wrapper'
STATE = Path.home() / '.cache' / 'bale-wrapper'
UNREAD_FILE = STATE / 'unread'

def icon_path(n):
    if n > 0:
        dot = BASE / 'badges' / 'badge-dot.png'
        if dot.exists(): return str(dot)
    return str(BASE / 'badges' / 'badge-0.png')

def find_window():
    out = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True).stdout
    for line in out.splitlines():
        if 'Bale Web' in line or 'بله' in line:
            return line.split()[0]
    return None

def toggle(*a):
    wid = find_window()
    if wid is None:
        subprocess.Popen([str(BASE / 'show-bale.sh')],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return
    act = subprocess.run(['xprop', '-root', '_NET_ACTIVE_WINDOW'],
                         capture_output=True, text=True).stdout
    m = re.search(r'window id # (0x[0-9a-f]+)', act)
    active = int(m.group(1), 16) if m else 0
    if active == int(wid, 16):
        subprocess.run(['wmctrl', '-i', '-c', wid])          # فوکوس است → مخفی
    else:
        subprocess.run(['xdotool', 'windowactivate', wid])   # فوکوس نیست → فوکوس

def quit_all(*a):
    wid = find_window()
    if wid:
        subprocess.run(['wmctrl', '-i', '-c', wid])
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
    try:
        n = int(UNREAD_FILE.read_text().strip() or 0)
    except Exception:
        n = 0
    if n != last[0]:
        last[0] = n
        GLib.idle_add(icon.set_from_file, icon_path(n))
        GLib.idle_add(icon.set_tooltip_text, f'Bale — {n} unread' if n else 'Bale')
    return True

GLib.timeout_add_seconds(1, poll)
Gtk.main()
