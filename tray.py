#!/usr/bin/env python3
# آیکون tray بله — Gtk.StatusIcon
# کلیک چپ (منطق تلگرامی):
#   در taskbar نیست → بیار بالا و فوکوس
#   هست ولی فوکوس نیست → فوکوس
#   هست و فوکوس است → از taskbar حذف (hide)
# شمارنده: title پنجره («Bale Web (n)») — با window id ذخیره‌شده حتی hidden خوانده می‌شود
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

def bale_window():
    """(wid قابل‌کلیک یا None) — فقط پنجره‌های قابل‌مشاهده"""
    out = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True).stdout
    for line in out.splitlines():
        if 'Bale Web' in line or 'بله' in line:
            return line.split()[0]
    return None

def toggle(*a):
    wid = bale_window()
    if wid is None:
        subprocess.Popen([str(BASE / 'show-bale.sh')],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return
    act = subprocess.run(['xprop', '-root', '_NET_ACTIVE_WINDOW'],
                         capture_output=True, text=True).stdout
    m = re.search(r'window id # (0x[0-9a-f]+)', act)
    if m and int(m.group(1), 16) == int(wid, 16):
        subprocess.run(['wmctrl', '-i', '-c', wid])      # فوکوس بود → hide
    else:
        subprocess.run(['xdotool', 'windowactivate', wid])  # نبود → فوکوس

def quit_all(*a):
    wid = bale_window()
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
    n = 0
    try:
        wid = WID_FILE.read_text().strip()
        out = subprocess.run(['xprop', '-id', wid, '_NET_WM_NAME'],
                             capture_output=True, text=True).stdout
        m = re.search(r'"(.*)"\s*$', out)
        if m:
            t = m.group(1)
            mm = re.search(r'\((\d{1,3})\)\s*$', t)
            if mm: n = int(mm.group(1))
    except Exception:
        pass
    if n != last[0]:
        last[0] = n
        GLib.idle_add(icon.set_from_file, icon_path(n))
        GLib.idle_add(icon.set_tooltip_text, f'Bale — {n} unread' if n else 'Bale')
    return True

GLib.timeout_add_seconds(2, poll)
Gtk.main()
