#!/usr/bin/env python3
# آیکون tray بله — Gtk.StatusIcon
# کلیک چپ: مخفی→نمایش+فوکوس | نمایان بی‌فوکوس→فوکوس | نمایان فوکوس→مخفی (منطق تلگرام)
# هر کلیک یک بار عمل می‌کند؛ کلیکی که وسط جابه‌جایی برسد بعد از جا افتادن پنجره اعمال می‌شود
# شمارنده: title پنجره (xprop -id) — حتی وقتی مخفی
import subprocess, re, time
from pathlib import Path
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

BASE = Path(__file__).resolve().parent
unread_file = Path.home() / '.cache' / 'bale-wrapper' / 'unread'  # main.js می‌نویسد   # کنار همین فایل — هم ~/apps/bale-wrapper هم /opt/bale-linux (deb)
FLAG = Path.home() / '.config' / 'bale-linux' / 'no-smooth-scrolling'   # بودنِ فایل = اسکرول پله‌ای (بدون لغزش)

def smooth_on():
    return not FLAG.exists()

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

def is_visible(wid):
    """Map State واقعی — پنجره‌ای که با --hidden بالا آمده اصلاً WM_STATE ندارد!"""
    r = subprocess.run(['xwininfo', '-id', wid], capture_output=True, text=True)
    return 'IsViewable' in r.stdout

def is_focused(wid):
    r = subprocess.run(['xprop', '-root', '_NET_ACTIVE_WINDOW'], capture_output=True, text=True)
    m = re.search(r'window id # (0x[0-9a-f]+)', r.stdout)
    return bool(m) and int(m.group(1), 16) == int(wid, 16)

_pending = [0]     # کلیک‌هایی که وسط جابه‌جایی رسیده‌اند — هیچ کلیکی دور ریخته نمی‌شود
_busy = [False]    # فرمان قبلی هنوز جا نیفتاده
_started = []      # مهرزمان toggleهای اخیر — مدارشکن ضدحلقهٔ show/hide

def _apply():
    """یک toggle بر اساس state فعلی؛ برچسبِ فرمان را برمی‌گرداند."""
    wid = get_wid()
    if not wid:
        subprocess.Popen(['systemctl', '--user', 'restart', 'bale.service'])
        return 'restart'
    if not is_visible(wid):             # مخفی (حتی اگر WM_STATE نداشته باشد) → نمایش
        subprocess.Popen([str(BASE / 'show-bale.sh')],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return 'show'
    if is_focused(wid):                 # فوکوس → مخفی
        subprocess.run(['wmctrl', '-ic', wid])
        return 'hide'
    subprocess.run(['xdotool', 'windowactivate', wid])   # بی‌فوکوس → فوکوس
    return 'focus'

def _settled(goal):
    """پنجره به نتیجه‌ی فرمانِ در جریان رسیده؟"""
    wid = get_wid()
    if goal == 'restart':
        return bool(wid)
    if not wid:
        return goal == 'hide'
    if goal == 'show':
        return is_visible(wid)
    if goal == 'hide':
        return not is_visible(wid)
    return True   # focus

def _drain():
    if _pending[0] > 0 and not _busy[0]:
        _pending[0] -= 1   # صف واقعی است؛ بدون تخلیه، toggle تا ابد خودش را صدا می‌زد (باگ حلقه)
        print(f'drain: pending applied', flush=True)
        toggle()

def toggle(*a):
    print(f'toggle enter: busy={_busy[0]} pending={_pending[0]}', flush=True)
    if _busy[0]:   # وسط باز/بسته‌شدن: بعد از جا افتادن پنجره اعمال می‌شود
        _pending[0] = min(_pending[0] + 1, 3)
        return
    now = time.time()
    _started[:] = [t for t in _started if now - t < 10]
    if len(_started) >= 12:   # مدارشکن: تراکمِ بالاتر از کلیک انسانی = حلقه؛ ریست کامل
        _pending[0] = 0
        return
    _started.append(now)
    goal = _apply()
    print(f'toggle: goal={goal} pending={_pending[0]}', flush=True)
    _busy[0] = True
    deadline = time.time() + 4
    def watch():
        if _settled(goal) or time.time() > deadline:
            _busy[0] = False
            # revive بعد از مرگ الکترون با --hidden بی‌صدا است؛ کلیکی که بیدارش کرد
            # قصد «باز کردن» داشت — اگر کلیک دیگری در صف نبود خودمان show کنیم
            if goal == 'restart' and _settled(goal) and not _pending[0]:
                subprocess.Popen([str(BASE / 'show-bale.sh')],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            GLib.idle_add(_drain)
            return False
        return True
    GLib.timeout_add(100, watch)

def quit_all(*a):
    wid = get_wid()
    if wid and is_visible(wid):
        subprocess.run(['wmctrl', '-ic', wid])
    GLib.idle_add(Gtk.main_quit)

def make_icon():
    ic = Gtk.StatusIcon.new_from_file(icon_path(0))
    ic.connect('activate', toggle)
    ic.connect('popup-menu', on_popup)
    ic.set_tooltip_text('Bale')
    return ic

_embedded = [None]
def poll():
    global last, last_nonzero, icon
    # خودترمیمی ثبت آیکون: اگر tray.py قبل از پنل بالا آمده باشد یا پنل میان‌کار
    # ری‌استارت شده باشد، چرخهٔ visible کافی نیست — آیکون باید از نو ساخته شود
    # تا GTK دوباره manager را ببیند (مسابقهٔ لاگین؛ تجربهٔ کانتینر تست)
    e = icon.is_embedded()
    if e != _embedded[0]:
        print(f'embedded: {e}', flush=True)
        _embedded[0] = e
    if not e:
        print('icon rebuilt', flush=True)
        icon = make_icon()
    # شمارنده: اول فایل state که main.js از title زندهٔ صفحه می‌نویسد (مستقل از X —
    # title در حالت hidden به X نمی‌رسد!)؛ فایل کهنه/غایب → مسیر قدیمی xprop
    n = 0
    try:
        st = unread_file.stat()
        if time.time() - st.st_mtime < 15:
            n = int(unread_file.read_text().strip() or '0')
    except (OSError, ValueError):
        n = 0
    if n == 0:
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
        print(f'count: {n}', flush=True)
        GLib.idle_add(icon.set_from_file, icon_path(n))
        GLib.idle_add(icon.set_tooltip_text, f'Bale — {n} unread' if n else 'Bale')
    return True   # تایمر ۲ ثانیه‌ای باید زنده بماند

def on_smooth_toggle(mi):
    want_smooth = mi.get_active()
    try:
        if want_smooth:
            FLAG.unlink(missing_ok=True)
        else:
            FLAG.parent.mkdir(parents=True, exist_ok=True)
            FLAG.touch()
    except OSError as e:
        print(f'smooth flag error: {e}', flush=True)
        return
    print(f'smooth scrolling -> {"on" if want_smooth else "off"}; restarting bale.service', flush=True)
    subprocess.Popen(['systemctl', '--user', 'restart', 'bale.service'])
    def _reshow():
        subprocess.Popen([str(BASE / 'show-bale.sh')],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return False
    GLib.timeout_add_seconds(4, _reshow)

def on_popup(si, button, time_):
    menu = Gtk.Menu()
    m1 = Gtk.MenuItem(label='بله — باز/بسته')
    m1.connect('activate', toggle)
    ms = Gtk.CheckMenuItem(label='اسکرول نرم (لغزشی)')
    ms.set_active(smooth_on())   # قبل از connect — تا سیگنال کاذب نیاید
    ms.connect('toggled', on_smooth_toggle)
    m2 = Gtk.MenuItem(label='خروج')
    m2.connect('activate', quit_all)
    menu.append(m1); menu.append(ms); menu.append(m2); menu.show_all()
    menu.popup(None, None, Gtk.StatusIcon.position_menu, si, button, time_)

icon = make_icon()   # اتصال activate/popup-menu داخل make_icon انجام می‌شود — دوباره وصل نکن (هر کلیک دو بار می‌شد!)

last = [-2]
last_nonzero = 0.0

GLib.timeout_add_seconds(2, poll)
Gtk.main()
