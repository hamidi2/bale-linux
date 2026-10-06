# بله برای گنو/لینوکس (Bale for Linux)

کلاینت دسکتاپ غیررسمی [پیام‌رسان بله](https://ble.ir) برای گنو/لینوکس — یک wrapper سبک
[Electron](https://www.electronjs.org) حول وب‌اپ رسمی، با مشکلات رایج حل‌شده.

> **نکته**: بله کلاینت رسمی لینوکس ندارد (ویندوز/وب/موبایل دارد). این پروژه مستقل و
> غیررسمی است و هیچ ارتباطی با شرکت صاحب بله ندارد.

## چرا این wrapper؟ (ویژگی‌ها)

- **تم روشن اجباری** → رفع کندی رندر emoji که در تم تیره‌ی وب‌اپ در کرومیوم دیده می‌شود
- **آیکون نوار وضعیت (tray)** با رفتار درست (`Gtk.StatusIcon` — کلیک چپ real می‌دهد):
  - **toggle سه‌حالته مثل تلگرام**: مخفی → نمایش+فوکوس | نمایانِ بی‌فوکوس → فوکوس |
    نمایانِ فوکوس → مخفی
  - **هر کلیک حساب است**: کلیک دوم حتی اگر بلافاصله بعد از اولی باشد پنجره را بسته
    (یا باز) می‌کند؛ کلیکی که وسطِ در حال باز/بسته‌شدن برسد، به‌محض جا افتادن پنجره
    اعمال می‌شود — هیچ کلیکی گم نمی‌شود
  - **بج و tooltip پیام نخوانده**: با وجود unread، نقطه‌ی قرمز روی آیکون می‌نشیند و
    تعداد دقیق در tooltip می‌آید
- **شمارنده از title پنجره** (نه DOM) — مرجع و پایدار، حتی وقتی پنجره مخفی است
  - **ضدفلیکر**: صفرِ لحظه‌ی باز شدن پنجره (که بله موقع show در title می‌گذارد) تا
    ‏۴ ثانیه بعد از آخرین عدد غیرصفر نادیده گرفته می‌شود
- بستن یا مینیمایز = مخفی‌شدن به tray (پروسه در حال اجرا می‌ماند؛ پیام‌ها می‌رسند)
- استارت خودکار در login (به‌صورت مخفی در tray) + ری‌استارت خودکار در کرش (systemd)
- لینک‌های خارجی در مرورگر سیستم باز می‌شوند
- اجرای دوباره‌ی لانچر = فقط نمایش پنجره (single-instance؛ تصمیم toggle با tray است)

## پیش‌نیازها

- Node.js و npm (برای نصب Electron)
- پایتون ۳ با `gi` (PyGObject) و GTK3 — روی اوبونتو/دبیان: `python3-gi` و `libgtk-3-0`
- `wmctrl`، `xdotool` و `x11-utils` (دستورات `xprop` و `xwininfo`)
- پایتون `Pillow` (فقط برای تولید مجدد badge ها: `python3-pil`)

## نصب

```bash
git clone https://github.com/hamidi2/bale-linux.git ~/apps/bale-wrapper
cd ~/apps/bale-wrapper
npm install            # electron را می‌گیرد
./make-badges.py       # آیکون‌ها (badge ها از قبل موجودند؛ فقط در صورت نیاز)
```

### اجرای پایدار (توصیه‌شده): سرویس systemd --user

الکترون زیر systemd سخت‌گیرانه با sandbox برخورد می‌کند؛ سرویس‌های آماده با `--no-sandbox`:

```bash
mkdir -p ~/.config/systemd/user
cp systemd/bale.service systemd/bale-tray.service ~/.config/systemd/user/
sed -i "s|%h/apps/bale-wrapper|%h/YOUR/PATH|g" ~/.config/systemd/user/bale*.service  # اگر مسیر دیگری دارید
systemctl --user daemon-reload && systemctl --user enable --now bale.service bale-tray.service
```

با این روش اگر الکترون یا tray کرش کند خودش بالا می‌آید (`Restart=on-failure`) و لاگ در
`journalctl --user -u bale.service -u bale-tray.service` است.
مسیر قدیمی (بدون systemd): `launch-bale.sh` (nohup، ایدمپوتنت).

## معماری کوتاه (برای نگهداری)

- `main.js` — پروسه‌ی Electron: پنجره + تم light + بستن/مینیمایز → hide (پروسه زنده،
  خارج از taskbar) + لینک خارجی → مرورگر سیستم + single-instance (اجرای دوباره =
  `second-instance` → show+focus).
- `tray.py` — آیکون tray و تمام هوشِ آن:
  - تشخیص پنجره با `WM_CLASS='bale-wrapper'` از `xwininfo -root -tree` (پنجره بعد از
    hide هم در tree می‌ماند)، وضعیت با `WM_STATE` و فوکوس با `_NET_ACTIVE_WINDOW`
  - شمارنده از `_NET_WM_NAME` (الگوی «(N)» انتهای title که خود بله می‌گذارد)، هر ۲ ثانیه —
    بدون دست زدن به DOM
  - بج نقطه‌ای (`badges/badge-dot.png`) + tooltip؛ ضدفلیکر ۴ ثانیه‌ای؛ کلیک‌های حین
    جابه‌جایی صف می‌شوند و بعد از جا افتادن پنجره اعمال می‌شوند (`_busy`/`_pending`)
- `show-bale.sh` — فقط سیگنال show به الکترون (اجرای دوباره‌ی باینری → second-instance).
- `launch-bale.sh` — استارت ایدمپوتنت؛ **هرگز pkill داخلش نگذارید**.
- `systemd/` — سرویس‌های `bale.service` (الکترون) و `bale-tray.service` (tray).

## عیب‌یابی

- **کلیک چپ روی آیکون منو باز می‌کند نه toggle** → دسکتاپ شما آیکون را SNI ثبت کرده
  است؛ این پروژه از `Gtk.StatusIcon` استفاده می‌کند که در اکثر محیط‌ها activate می‌دهد.
  اگر در محیط شما منو باز می‌شود، پنل‌تان StatusNotifierItem را به منو ترجیح می‌دهد —
  رفتار tray را با روش محیط خودتان جایگزین کنید.
- **شمارنده همیشه صفر یا غلط است** → شمارنده به الگوی «(N)» انتهای title تکیه دارد؛ اگر
  بله در نسخه‌ای فرمت title را عوض کند، regex داخل `poll()` در `tray.py` را به‌روز کنید.
- **آیکون tray نمی‌آید** → در پنل‌های فقط-SNI مطمئن شوید افزونه‌ی systray فعال است؛
  `Gtk.StatusIcon` راه XEmbed می‌رود و بسیاری از پنل‌ها هر دو را میزبانی می‌کنند.
- **Emoji کند است در تم دارک** → همین مشکل انگیزه‌ی ساخت این پروژه بود؛ تم light
  اجباری است و حل می‌کند.

## مجوز

کد این پروژه تحت MIT است (فایل LICENSE).
لوگوی بله (`bale.png` و badge ها) متعلق به صاحب اثر بله است و صرفاً برای سازگاری
با کلاینت غیررسمی اینجا قرار گرفته؛ اگر مالک آن درخواست حذف کند برداشته می‌شود.

---
*Bale for GNU/Linux — an unofficial lightweight Electron wrapper around the official
web app: tray icon with a Telegram-style 3-state toggle (every click counts — clicks
arriving mid-transition are applied once the window settles), unread badge + tooltip
read from the window title (works while hidden, with anti-flicker grace),
close-to-tray, forced light theme (fixes emoji rendering slowness in dark mode), and
systemd --user services. MIT licensed; not affiliated with Bale.*
