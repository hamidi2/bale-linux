// بله دسکتاپ — wrapper سبک Electron
// تم light اجباری (رفع کندی رندر emoji در دارک)
// «بستن» = پنجره به خارج از صفحه می‌رود + از taskbar حذف (مپ می‌ماند تا title خوانده شود)
// tray.py: کلیک = SIGHUP به این پروسه (toggle)؛ تعداد نخوانده = از title پنجره (WM-level)
const { app, BrowserWindow, nativeTheme, shell } = require('electron');
const path = require('path');
const fs = require('fs');
const os = require('os');

const BALE_URL = 'https://web.bale.ai';
const startHidden = process.argv.includes('--hidden');

let win = null;
let quitting = false;
let offscreen = false;
let savedBounds = null;

nativeTheme.themeSource = 'light';
fs.mkdirSync(path.join(os.homedir(), '.cache', 'bale-wrapper'), { recursive: true });
try { fs.writeFileSync(path.join(os.homedir(), '.cache', 'bale-wrapper', 'pid'), String(process.pid)); } catch (e) {}

function hideToTray() {
  if (!win || win.isDestroyed()) return;
  savedBounds = win.getBounds();
  offscreen = true;
  win.setSkipTaskbar(true);
  win.setPosition(-32768, -32768);
}

function showFromTray() {
  if (!win || win.isDestroyed()) return;
  offscreen = false;
  win.setSkipTaskbar(false);
  if (savedBounds) win.setBounds(savedBounds);
  win.show();
  win.focus();
}

function toggleWindow() {
  if (offscreen) showFromTray(); else hideToTray();
}

process.on('SIGHUP', () => { if (app.isReady()) toggleWindow(); });

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

  win.webContents.setWindowOpenHandler(({ url }) => {
    if (!url.includes('bale.ai')) {
      shell.openExternal(url);
      return { action: 'deny' };
    }
    return { action: 'allow' };
  });

  // بستن/مینیمایز = خارج از صفحه + بدون taskbar (پنجره mapped می‌ماند)
  win.on('close', (e) => { if (!quitting) { e.preventDefault(); hideToTray(); } });
  win.on('minimize', (e) => { e.preventDefault(); hideToTray(); });
  win.once('ready-to-show', () => {
    if (startHidden) hideToTray(); else { win.show(); win.focus(); }
  });
}

const gotLock = app.requestSingleInstanceLock();
if (!gotLock) { app.quit(); }
app.on('second-instance', () => {
  if (!app.isReady() || !win || win.isDestroyed()) return;
  if (offscreen) showFromTray();
  else if (win.isVisible() && win.isFocused()) hideToTray();
  else { win.show(); win.focus(); }
});

app.whenReady().then(() => { createWindow(); });

app.on('window-all-closed', () => {});
app.on('before-quit', () => { quitting = true; });
