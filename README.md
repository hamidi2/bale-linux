# بله برای گنو/لینوکس (Bale for Linux)

کلاینت دسکتاپ غیررسمی [پیام‌رسان بله](https://ble.ir) برای گنو/لینوکس — یک wrapper سبک
[Electron](https://www.electronjs.org) حول وب‌اپ رسمی، با مشکلات رایج حل‌شده.

> **نکته**: بله کلاینت رسمی لینوکس ندارد (ویندوز/وب/موبایل دارد). این پروژه مستقل و
> غیررسمی است و هیچ ارتباطی با شرکت صاحب بله ندارد.

## چرا این wrapper؟ (ویژگی‌ها)

- **تم روشن اجباری** → رفع کندی رندر emoji که در تم تیره‌ی وب‌اپ در کرومیوم‌ها دیده می‌شود
- **آیکون نوار وضعیت (tray)** با رفتار درست:
  - کلیک چپ = باز/بسته‌ی پنجره (مثل تلگرام)
  - **شمارنده‌ی پیام‌های نخوانده روی آیکون** — خوانده‌شده مستقیم از DOM اپ، پس
    برخلاف روش «خواندن از title»، با باز/فوکوس‌شدن پنجره صفر نمی‌شود
- بستن یا مینیمایز = مخفی‌شدن به tray (پروسه در حال اجرا می‌ماند؛ پیام‌ها می‌رسند)
- استارت خودکار در login (به‌صورت مخفی در tray)
- لینک‌های خارجی در مرورگر سیستم باز می‌شوند

## پیش‌نیازها

- Node.js و npm (برای نصب Electron)
- پایتون ۳ با `gi` (PyGObject) و GTK3 — روی اوبونتو/دبیان: `python3-gi` و `libgtk-3-0`
- `wmctrl`
- پایتون `Pillow` (فقط برای تولید مجدد badge ها: `python3-pil`)

## نصب

```bash
git clone <این-ریپو> ~/apps/bale-wrapper
cd ~/apps/bale-wrapper
npm install            # electron را می‌گیرد
./make-badges.py       # آیکون‌های شمارنده (badge ها از قبل موجودند؛ فقط در صورت نیاز)
~/apps/bale-wrapper/launch-bale.sh
```

استارت خودکار: فایل `bale-wrapper.desktop` نمونه را در `~/.config/autostart/` بگذارید
با `Exec=/home/USER/apps/bale-wrapper/launch-bale.sh --hidden`.

## معماری کوتاه (برای نگهداری)

- `main.js` — پروسه‌ی Electron: پنجره + تم light + جمع شمارنده از DOM (badge های
  `span.eVv8xC` با ارقام فارسی) و نوشتن در `~/.cache/bale-wrapper/unread`.
  **توجه**: اگر بله کلاس badge را در نسخه‌ی بعد عوض کند، fallback خودکار به
  «هر span عددی» فعال می‌شود؛ اگر شمارنده خراب شد selector را به‌روز کنید.
- `tray.py` — آیکون tray با `Gtk.StatusIcon` (روی دسکتاپ‌های بدون XEmbed مثل پنل‌های
  SNI-only این روش کار می‌کند و کلیک چپ real می‌دهد). toggle پنجره: بسته‌شدن با
  `wmctrl -c` (که main.js آن را به hide تبدیل می‌کند) و بازشدن با اجرای دوباره‌ی
  الکترون → second-instance → show.
- `show-bale.sh` / `launch-bale.sh` — دومی idempotent است؛ **هرگز pkill داخلش نگذارید**.

## عیب‌یابی

- **کلیک چپ روی آیکون منو باز می‌کند نه toggle** → دسکتاپ شما آیکون را SNI ثبت کرده
  است؛ این پروژه از `Gtk.StatusIcon` استفاده می‌کند که در اکثر محیط‌ها activate می‌دهد.
  اگر در محیط شما منو باز می‌شود، رفتار status-notifier پنل‌تان StatusNotifierItem را
  به منو ترجیح می‌دهد — tray.py را با روش محیط خودتان جایگزین کنید.
- **شمارنده کار نمی‌کند** → selector کلاس badge تغییر کرده؛ در `main.js` بخش شمارنده
  را به‌روز کنید (DOM بله را با DevTools الکترون — `Ctrl+Shift+I` — بررسی کنید).
- **Emoji کند است در تم دارک** → همین مشکل انگیزه‌ی ساخت این پروژه بود؛ تم light
  اجباری است و حل می‌کند.

## مجوز

کد این پروژه تحت MIT است (فایل LICENSE).
لوگوی بله (`bale.png` و badge ها) متعلق به صاحب اثر بله است و صرفاً برای سازگاری
با کلاینت غیررسمی اینجا قرار گرفته؛ اگر مالک آن درخواست حذف کند برداشته می‌شود.

---
*Bale for GNU/Linux — an unofficial lightweight Electron wrapper around the official
web app with a proper tray icon, unread counter (read from DOM, survives focus),
light-theme enforcement (fixes emoji rendering slowness in dark mode), and
close-to-tray behavior. MIT licensed; not affiliated with Bale.*
