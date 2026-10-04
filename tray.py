#!/usr/bin/env python3
# آیکون tray بله — Gtk.StatusIcon (همان مسیر گواک که روی این دسکتاپ اثبات شده)
# کلیک چپ = باز/بسته پنجره بله (با wmctrl)، راست‌کلیک = منو، شمارنده روی آیکون
import subprocess, time
from pathlib import Path
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

BASE = Path.home() / 'apps' / 'bale-wrapper'
STATE = Path.home() / '.cache' / 'bale-wrapper'
UNREAD_FILE = STATE / 'unread'

def icon_path(n):
    n = max(0, min(99, n))
    p = BASE / 'badges' / f'badge-{n}.png'
    return str(p if p.exists() else BASE / 'bale.png')

def toggle(*a):
    # اگر پنجره دیده می‌شود → close (که main.js آن را hide می‌کند)؛
    # وگرنه اجرای لانچر → single-instance الکترون به پروسه زنده پیام show می‌دهد
    out = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True).stdout
    for line in out.splitlines():
        if 'Bale Web' in line or 'بله' in line:
            subprocess.run(['wmctrl', '-i', '-c', line.split()[0]])
            return
    subprocess.Popen([str(BASE / 'show-bale.sh')],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def quit_all(*a):
    out = subprocess.run(['wmctrl', '-lx'], capture_output=True, text=True).stdout
    for line in out.splitlines():
        if 'bale' in line.lower():
            subprocess.run(['wmctrl', '-i', '-c', line.split()[0]])
    GLib.idle_add(Gtk.main_quit)

icon = Gtk.StatusIcon.new_from_file(icon_path(0))
icon.set_tooltip_text('Bale')

def on_popup(si, button, time_):
    menu = Gtk.Menu()
    m1 = Gtk.MenuItem(label='بله — باز/بسته')
    m1.connect('activate', toggle)
    menu.append(m1)
    m2 = Gtk.MenuItem(label='خروج')
    m2.connect('activate', quit_all)
    menu.append(m2)
    menu.show_all()
    menu.popup(None, None, Gtk.StatusIcon.position_menu, si, button, time_)

icon.connect('activate', toggle)
icon.connect('popup-menu', on_popup)

last = [-1]
def poll():
    try:
        n = int(UNREAD_FILE.read_text().strip() or 0)
    except Exception:
        n = 0
    if n != last[0]:
        last[0] = n
        GLib.idle_add(icon.set_from_file, icon_path(n))
        GLib.idle_add(icon.set_tooltip_text, f'Bale - {n} unread' if n else 'Bale')
    return True

GLib.timeout_add_seconds(1, poll)
Gtk.main()
