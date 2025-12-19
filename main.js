// main.js
const { app, Tray, Menu, nativeImage } = require('electron');
const path = require('path');
const express = require('express');
const puppeteer = require('puppeteer');

const START_URL = 'https://wraith.software/';
const HTTP_PORT = 3000; // İstersen değiştir

let tray = null;
let browser = null;
let page = null;
let server = null;
let initialRefreshInterval = null;
let isHidden = false;

const forceKiosk = false; // true -> kiosk (istersen aç)

const { execFile } = require('child_process');

const WINCTL_PATH = path.join(
  __dirname,
  'python',
  'dist',
  'winctl.exe'
);

// ------------------- notification -------------------

function showTrayNotification(title, body) {
  if (tray) {
    // Windows için balloon notification
    try {
      tray.displayBalloon({ title, content: body });
    } catch (e) {
      // silent fallback
    }

    // Diğer platformlar için Notification API
    try {
      new Notification({ title, body }).show();
    } catch (e) {
      // silent fallback
    }
  }
}

async function getActiveProfileId() {
  if (!page) return null;

  try {
    const index = await page.evaluate(() => {
      const val = getComputedStyle(document.documentElement)
        .getPropertyValue('--translateY')
        .replace('%', '')
        .trim();

      const num = Number(val);
      if (isNaN(num)) return null;

      return Math.round(num / 100);
    });

    const profileMap = [
      'ProfileDef', // 0%
      'Profile1',   // 100%
      'Profile2',   // 200%
      'Profile3',   // 300%
      'Profile4'    // 400%
    ];

    return profileMap[index] || null;
  } catch {
    return null;
  }
}

function getChromiumPid() {
  try {
    const proc = browser?.process?.();
    return proc?.pid || null;
  } catch {
    return null;
  }
}

function hideChromiumWindow() {
  const pid = getChromiumPid();
  if (!pid) return;

  execFile(WINCTL_PATH, ['hide', String(pid)], { windowsHide: true }, () => {});
}

function showChromiumWindow() {
  const pid = getChromiumPid();
  if (!pid) return;

  execFile(WINCTL_PATH, ['show', String(pid)], { windowsHide: true }, () => {});
}

function toggleChromiumWindow() {
  if (isHidden) {
    showChromiumWindow();
    isHidden = false;
  } else {
    hideChromiumWindow();
    isHidden = true;
  }
}

// ------------------- SHUTDOWN -------------------

async function shutdownAndExit(code = 0) {
  try {
    // stop initial refresh interval if running
    if (initialRefreshInterval) {
      clearInterval(initialRefreshInterval);
      initialRefreshInterval = null;
    }

    if (server) {
      try { server.close(); } catch (e) { /* ignore */ }
      server = null;
    }

    if (browser) {
      try { await browser.close(); } catch (e) { /* ignore */ }
      browser = null;
    }
  } catch (e) {
    // silent
  }

  try { app.quit(); } catch (e) { process.exit(code); }
}

// ------------------- PUPPETEER / CHROMIUM -------------------

async function startBrowser() {
  const userDataPath = path.join(__dirname, 'chromium-profile');

  const launchArgs = [
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--start-maximized',
    '--disable-infobars',
    '--disable-session-crashed-bubble',
    '--disable-features=TranslateUI',
    `--app=${START_URL}` // URL bar'ı gizler
  ];
  if (forceKiosk) launchArgs.push('--kiosk');

  browser = await puppeteer.launch({
    headless: false,
    userDataDir: userDataPath,
    args: launchArgs,
    defaultViewport: null
  });

  // sayfa referansını al
  const pages = await browser.pages();
  page = pages.length ? pages[0] : await browser.newPage();

  // gitmeye çalış, hata olursa silent catch
  await page.goto(START_URL, { waitUntil: 'networkidle2' }).catch(() => {});
  await page.bringToFront().catch(() => {});

  // sağlam kapanış handler'ları kur
  setupCloseHandlers();

  // İlk açılışta profiller gelene kadar 3 saniyede bir refresh et (sessiz)
  if (!initialRefreshInterval) {
    initialRefreshInterval = setInterval(async () => {
      if (!page) return;

      try {
      // 1️⃣ Önce tray isimlerini güncelle
        await refreshTrayNames();

      // En az bir profil adı gerçekten yüklendi mi?
        const namesLoaded = trayMenuTemplate.some(
          item => item.id && item.label && !item.label.startsWith('Profile ')
        );

        if (!namesLoaded) return;

      // 2️⃣ İsimler geldikten sonra aktif profili tespit et
        const activeProfileId = await getActiveProfileId();
        if (!activeProfileId) return;

        clearInterval(initialRefreshInterval);
        initialRefreshInterval = null;

        const activeProfile = trayMenuTemplate.find(
          item => item.id === activeProfileId
        );

        if (activeProfile) {
          showTrayNotification(
            'Başlatıldı',
            `Aktif profil: ${activeProfile.label}`
          );
        }
      } catch {
      // silent
      }
    }, 3000);
  }



  // ayrıca başlangıçta bir defa dene (intervali beklemeden)
  try { await refreshTrayNames(); } catch (e) { /* silent */ }
}

// ------------------- SAYFA İÇİ TIKLAMA -------------------

async function runClickById(id) {
  if (!page) {
    return false;
  }
  try {
    const res = await page.evaluate((el) => {
      const target = document.getElementById(el);
      if (!target) return { ok: false };
      target.click();
      return { ok: true };
    }, id);
    return !!(res && res.ok);
  } catch (err) {
    return false;
  }
}

// ------------------- TRAY & DYNAMIC NAMES -------------------

// Template içindeki her profil objesinde "id" -> sayfadaki "for" attribute'u ile eşleşir.
// örn: <label for="Profile1" class="profileName">123</label>
let trayMenuTemplate = [
  { id: 'ProfileDef', label: 'Default', click: () => clickAndUpdate('ProfileDef') },
  { id: 'Profile1',  label: 'Profile 1', click: () => clickAndUpdate('Profile1') },
  { id: 'Profile2',  label: 'Profile 2', click: () => clickAndUpdate('Profile2') },
  { id: 'Profile3',  label: 'Profile 3', click: () => clickAndUpdate('Profile3') },
  { id: 'Profile4',  label: 'Profile 4', click: () => clickAndUpdate('Profile4') },
  { type: 'separator' },
  { label: 'Yenile', click: () => refreshTrayNames() },
  { label: 'Gizle / Göster', click: () => toggleChromiumWindow() },
  { label: 'Exit', click: () => shutdownAndExit(0) }
];

function buildTray() {
  let iconPath = path.join(__dirname, 'tray-icon.png'); // opsiyonel
  let image = null;
  try {
    image = nativeImage.createFromPath(iconPath);
    if (image.isEmpty()) image = null;
  } catch (e) {
    image = null;
  }

  tray = new Tray(image || nativeImage.createEmpty());
  tray.setToolTip('Wraith Tray Controller');
  updateTrayMenu();

  tray.on('click', () => {
    toggleChromiumWindow();
  });
}

function updateTrayMenu() {
  // Menu.buildFromTemplate kopyalar; click fonksiyonları korunur
  const menu = Menu.buildFromTemplate(trayMenuTemplate.map(item => Object.assign({}, item)));
  tray.setContextMenu(menu);
}

async function refreshTrayNames() {
  if (!page) return;
  try {
    const namesAndActive = await page.evaluate(() => {
      const map = {};
      let activeId = null;

      document.querySelectorAll('label.profileName').forEach(el => {
        const key = el.getAttribute('for');
        if (key) {
          map[key] = el.textContent.trim();
          if (el.classList.contains('active')) { // sayfa aktif profil sınıfı
            activeId = key;
          }
        }
      });
      return { map, activeId };
    });

    const { map, activeId } = namesAndActive;

    trayMenuTemplate = trayMenuTemplate.map(item => {
      if (item.id && map[item.id]) {
        return Object.assign({}, item, { label: map[item.id] || item.label });
      }
      return item;
    });

    updateTrayMenu();

    return activeId; // aktif profil ID’sini döndür
  } catch (e) {
    // silent
    return null;
  }
}

async function clickAndUpdate(profileId) {
  try {
    const ok = await runClickById(profileId);
    if (ok) {
      // Profil değişti, bildirim göster
      const profileName = trayMenuTemplate.find(item => item.id === profileId)?.label || profileId;
      showTrayNotification('Profil değişti', `Aktif profil: ${profileName}`);
    }
  } catch (e) {
    // silent
  }
  // isimleri yenile (sayfa state değişmiş olabilir)
  await refreshTrayNames().catch(() => {});
}

// ------------------- HTTP SERVER (POST /control) -------------------

function startHttpServer() {
  const appServer = express();
  appServer.use(express.json());

  appServer.post('/control', async (req, res) => {
    const p = Number(req.body?.port);

    const map = {
      1: 'ProfileDef',
      2: 'Profile1',
      3: 'Profile2',
      4: 'Profile3',
      5: 'Profile4'
    };

    if (!map[p]) {
      return res.status(400).json({ error: 'invalid port. use 1..5' });
    }

    const profileId = map[p];
    const ok = await runClickById(profileId);
    await refreshTrayNames().catch(() => {});

    if (ok) {
      const profileName = trayMenuTemplate.find(item => item.id === profileId)?.label || profileId;

    // Uzak JSON komut ile değişim bildirimi
      showTrayNotification('Profil uzaktan değiştirildi', `Aktif profil: ${profileName}`);

      res.json({ status: 'ok' });
    } else {
      res.status(500).json({ status: 'error' });
    }
  });

  server = appServer.listen(HTTP_PORT);
}

// ------------------- CLOSE HANDLERS -------------------

// Kurulum: browser referansı mevcutken çağır
function setupCloseHandlers() {
  if (!browser) return;

  // Puppeteer disconnected event
  try {
    browser.on('disconnected', () => {
      // hemen uygulamayı kapat
      shutdownAndExit(0);
    });
  } catch (e) {
    // silent
  }

  // child process (chromium) exit event - ekstra güvenlik
  try {
    const proc = browser.process && browser.process();
    if (proc && proc.pid) {
      proc.on('exit', () => {
        shutdownAndExit(0);
      });
      proc.on('close', () => {
        shutdownAndExit(0);
      });
    }
  } catch (e) {
    // silent
  }

  // Electron tarafı: app kapanırken browser'ı kapat
  app.on('before-quit', async () => {
    if (browser) {
      try { await browser.close(); } catch (e) { /* silent */ }
      browser = null;
    }
  });

  // Tüm pencereler kapandıysa da kapat
  app.on('window-all-closed', () => {
    shutdownAndExit(0);
  });

  // Process sinyalleri
  process.on('SIGINT', () => shutdownAndExit(0));
  process.on('SIGTERM', () => shutdownAndExit(0));
}

// ------------------- ELECTRON LIFECYCLE -------------------

app.on('ready', async () => {
  try {
    buildTray();
    await startBrowser();
    startHttpServer();
  } catch (err) {
    // silent - kapat
    shutdownAndExit(1);
  }
});

// Eğer tüm pencereler kapansa bile uygulamayı sonlandırma (Chromium puppeteer ile yönetiliyor)
app.on('window-all-closed', () => {
  // handled above
});
