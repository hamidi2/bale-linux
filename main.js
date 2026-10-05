// بله دسکتاپ — wrapper سبک Electron
// تم light اجباری (رفع کندی رندر emoji در دارک)
// بستن/مینیمایز = hide (پروسه زنده) | کلیک tray = toggle منطق تلگرامی (در tray.py)
// شمارنده: tray.py از title پنجره می‌خواند (window id در ~/.cache/bale-wrapper/wid)
const { app, BrowserWindow, nativeTheme, shell } = require('electron');
const path = require('path');
const fs = require('fs');
const os = require('os');

const BALE_URL = 'https://web.bale.ai';
const startHidden = process.argv.includes('--hidden');
const STATE_DIR = path.join(os.homedir(), '.cache', 'bale-wrapper');

let win = null;
let quitting = false;

nativeTheme.themeSource = 'light';
fs.mkdirSync(STATE_DIR, { recursive: true });

function createWindow() {
  win = new BrowserWindow({
    width: 1280,
    height: 860,
    minWidth: 500,
    minHeight: 400,
    show: false,
    icon: path.join(__dirname, 'bale.png'),
    title: 'بله',
    backgroundColor: '#ffffff',
    webPreferences: { contextIsolation: true, spellcheck: false, backgroundThrottling: false },
  });

  win.loadURL(BALE_URL);

  // window id برای tray.py (خواندن title حتی وقتی پنجره hide است)
  try {
    const wh = win.getNativeWindowHandle();
    fs.writeFileSync(path.join(STATE_DIR, 'wid'), '0x' + wh.readUInt32LE(0).toString(16));
  } catch (e) {}

  win.webContents.setWindowOpenHandler(({ url }) => {
    if (!url.includes('bale.ai')) {
      shell.openExternal(url);
      return { action: 'deny' };
    }
    return { action: 'allow' };
  });

  // بستن/مینیمایز = مخفی از taskbar (پروسه زنده)
  win.on('close', (e) => { if (!quitting) { e.preventDefault(); win.hide(); } });
  win.on('minimize', (e) => { e.preventDefault(); win.hide(); });
  win.on('hide', () => { if (win && !win.isDestroyed()) win.setSkipTaskbar(true); });
  win.on('show', () => { if (win && !win.isDestroyed()) win.setSkipTaskbar(false); });
  win.once('ready-to-show', () => { if (!startHidden) { win.show(); win.focus(); } else win.hide(); });
}

const gotLock = app.requestSingleInstanceLock();
if (!gotLock) { app.quit(); }
// اجرای دوباره لانچر = فقط نمایش (تصمیم toggle با tray.py است)
app.on('second-instance', () => {
  if (!app.isReady() || !win || win.isDestroyed()) return;
  win.setSkipTaskbar(false);
  win.show();
  win.focus();
});

app.whenReady().then(() => { createWindow(); });

app.on('window-all-closed', () => {});
app.on('before-quit', () => { quitting = true; });
