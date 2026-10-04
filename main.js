// بله دسکتاپ — wrapper سبک Electron
// تم light اجباری (رفع کندی رندر emoji در دارک)
// tray icon توسط tray.py (XEmbed — کلیک چپ=باز/بسته، راست=منو، شمارنده روی آیکون)
// ارتباط: SIGHUP به این پروسه = toggle پنجره؛ فایل unread = تعداد نخوانده‌ها
const { app, BrowserWindow, nativeTheme, shell } = require('electron');
const path = require('path');
const fs = require('fs');
const os = require('os');

const BALE_URL = 'https://web.bale.ai';
const startHidden = process.argv.includes('--hidden');
const STATE_DIR = path.join(os.homedir(), '.cache', 'bale-wrapper');
const PID_FILE = path.join(STATE_DIR, 'pid');
const UNREAD_FILE = path.join(STATE_DIR, 'unread');

let win = null;
let quitting = false;
let lastUnread = -1;

nativeTheme.themeSource = 'light';

fs.mkdirSync(STATE_DIR, { recursive: true });
fs.writeFileSync(PID_FILE, String(process.pid));

function writeUnread(n) {
  if (n === lastUnread) return;
  lastUnread = n;
  try { fs.writeFileSync(UNREAD_FILE, String(n)); } catch (e) {}
}

function toggleWindow() {
  if (!win || win.isDestroyed()) return;
  if (win.isVisible() && win.isFocused()) win.hide();
  else { win.setSkipTaskbar(false); win.show(); win.focus(); }
}


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

  // بستن و مینیمایز = مخفی (از تسک‌بار هم حذف شود)
  const hideToTray = () => { win.hide(); };
  win.on('close', (e) => { if (!quitting) { e.preventDefault(); hideToTray(); } });
  win.on('minimize', (e) => { e.preventDefault(); hideToTray(); });
  win.on('hide', () => { if (win && !win.isDestroyed()) win.setSkipTaskbar(true); });
  win.on('show', () => { if (win && !win.isDestroyed()) win.setSkipTaskbar(false); });
  win.once('ready-to-show', () => { if (!startHidden) win.show(); else win.hide(); });


  // شمارنده نخوانده از DOM: بج‌های span.eVv8xC (ارقام فارسی)، حذف mute و مخفی‌ها
  const JS_ERR_LOG = require('path').join(os.homedir(), '.cache', 'bale-wrapper', 'js-err.log');
  setInterval(() => {
    if (!win || win.isDestroyed()) return;
    const script =
      'try {' +
      'const toNum = t => {' +
      '  let v = 0;' +
      '  for (const ch of t) {' +
      "    const fi = '۰۱۲۳۴۵۶۷۸۹'.indexOf(ch);" +
      '    v = v * 10 + (fi >= 0 ? fi : (/[0-9]/.test(ch) ? +ch : NaN));' +
      '  }' +
      '  return v;' +
      '};' +
      "const re = /^[0-9\u06F0-\u06F9]{1,4}$/;" +
      "const isRedBadge = el => {" +
      '  const st = getComputedStyle(el).backgroundColor;' +
      "  const m = st.match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)/);" +
      '  if (!m) return false;' +
      '  const r = +m[1], g = +m[2], b = +m[3];' +
      '  return r > 120 && r > g + 40 && r > b + 40;' +
      '};' +
      "let els = document.querySelectorAll('span.eVv8xC');" +
      'if (els.length === 0) {' +
      "  els = [...document.querySelectorAll('span')].filter(el =>" +
      "    el.children.length === 0 && re.test((el.textContent || '').trim()));" +
      '}' +
      'let sum = 0;' +
      'els.forEach(el => {' +
      "  if (el.offsetParent === null && getComputedStyle(el).position !== 'fixed') return;" +
      '  if (!isRedBadge(el)) return;' +
      "  const t = (el.textContent || '').trim();" +
      '  if (re.test(t)) { const v = toNum(t); if (!isNaN(v)) sum += v; }' +
      '});' +
      'String(sum);' +
      '} catch (e) { String("PAGE-ERR:" + e.message); }';
    win.webContents.executeJavaScript(script)
      .then(n => {
        if (String(n).startsWith('PAGE-ERR:')) {
          try { require('fs').appendFileSync(JS_ERR_LOG, String(n).slice(0, 140) + '\n'); } catch (_) {}
          return;
        }
        writeUnread(parseInt(n, 10) || 0);
        try { require('fs').appendFileSync(require('path').join(os.homedir(), '.cache', 'bale-wrapper', 'tick.log'), new Date().toISOString().slice(11,19) + ' n=' + n + '\n'); } catch (_) {}
      })
      .catch(e => {
        try { require('fs').appendFileSync(JS_ERR_LOG, String(e).slice(0, 120) + '\n'); } catch (_) {}
      });
  }, 2000);
}

const gotLock = app.requestSingleInstanceLock();
if (!gotLock) { app.quit(); }
app.on('second-instance', () => {
  if (win && !win.isDestroyed()) { win.setSkipTaskbar(false); win.show(); win.focus(); }
});

app.whenReady().then(() => {
  createWindow();
  writeUnread(0);
});

app.on('window-all-closed', () => {});
app.on('before-quit', () => { quitting = true; });
