// Başlatma ve oyun döngüsü.
import { loadStory } from './story.js';
import { normalize } from './parser.js';
import { newState, advance, choose, answer, upcoming, skipWait, rewind } from './engine.js';
import { loadGame, saveGame, clearGame, loadPrefs, savePrefs } from './save.js';
import { createLogView, renderDock, renderHeader } from './ui.js';
import { requestPermission, permissionState, pickNotifications, schedule, cancelAll } from './notify.js';
import { photoSvg } from './photos.js';
import { FEATURES } from './features.js';
import { VERSION, BUILD } from './version.js';

const $ = id => document.getElementById(id);
const prefs = loadPrefs();
const dev = FEATURES.dev;
let story = null;
let st = null;
let timer = 0;
let lastStatus = null;

const opt = () => ({ scale: dev ? prefs.speed : 1 });
const now = () => Date.now();

// ---------- Görünüm ayarları ----------
function applyPrefs() {
  document.documentElement.dataset.theme = prefs.theme;
  document.documentElement.style.setProperty('--scale', prefs.size);
  for (const [id, key] of [['themeSeg', 'theme'], ['sizeSeg', 'size'], ['speedSeg', 'speed']]) {
    for (const b of $(id).querySelectorAll('button')) b.classList.toggle('on', String(prefs[key]) === b.dataset.v);
  }
  window.Capacitor?.Plugins?.StatusBar?.setStyle?.({ style: prefs.theme === 'dark' ? 'DARK' : 'LIGHT' }).catch?.(() => {});
}

function bindSeg(id, key, cast = v => v) {
  $(id).addEventListener('click', e => {
    const b = e.target.closest('button');
    if (!b) return;
    prefs[key] = cast(b.dataset.v);
    savePrefs(prefs);
    applyPrefs();
    if (key === 'speed') tick();
  });
}

// ---------- Döngü ----------
const view = createLogView(showPhoto);

function tick() {
  clearTimeout(timer);
  if (!st || !story) return;
  const t = now();
  let status;
  try {
    status = advance(story, st, t, opt());
  } catch (e) {
    console.error(e);
    status = { kind: 'paused' };
    st.paused = { text: `Senaryo hatası: ${e.message}`, at: t };
  }
  lastStatus = status;
  saveGame(st);
  view.sync(st, status.kind === 'typing');
  renderHeader(st, status, t);
  renderDock(st, status, {
    choose: i => { choose(story, st, i, now(), opt()); tick(); },
    answer: v => { answer(story, st, v, now(), normalize, opt()); tick(); },
    now, dev, realWake: x => x,
  });

  let next = null;
  if (status.kind === 'typing') next = status.at - t;
  else if (status.kind === 'away') next = Math.min(status.wakeAt - t, 30_000);
  if (next !== null) timer = setTimeout(tick, Math.max(40, next + 15));
}

// ---------- Bildirimler ----------
async function planNotifications() {
  if (!st || !story) return;
  const t = now();
  const { items } = upcoming(story, st, t, opt());
  await schedule(pickNotifications(items, t, st.meta.ad || 'Bilinmeyen Numara'));
}

function onHide() { clearTimeout(timer); planNotifications(); }
function onShow() { cancelAll(); tick(); }

document.addEventListener('visibilitychange', () => (document.hidden ? onHide() : onShow()));
const App = window.Capacitor?.Plugins?.App;
App?.addListener?.('pause', onHide);
App?.addListener?.('resume', onShow);
App?.addListener?.('backButton', () => {
  if (!$('viewer').hidden) $('viewer').hidden = true;
  else if (!$('settings').hidden) $('settings').hidden = true;
  else App.minimizeApp?.();
});

// ---------- Fotoğraf ----------
function showPhoto(e) {
  $('viewerImg').innerHTML = photoSvg(e.key);
  $('viewerCap').textContent = e.caption || '';
  $('viewer').hidden = false;
}
$('viewer').addEventListener('click', () => { $('viewer').hidden = true; });

// ---------- Ayarlar ----------
async function openSettings() {
  $('settings').hidden = false;
  const p = await permissionState();
  $('notifState').textContent = { granted: 'Açık', denied: 'Kapalı (telefon ayarlarından aç)', prompt: 'Sorulmadı', yok: 'Bu cihazda yok' }[p] || p;
}
$('settingsBtn').addEventListener('click', openSettings);
$('settings').addEventListener('click', e => {
  if (e.target === $('settings') || e.target.closest('[data-close]')) $('settings').hidden = true;
});
$('resetBtn').addEventListener('click', () => {
  if (!confirm('Hikâye en baştan başlayacak. Bütün mesajlar silinecek. Emin misin?')) return;
  clearGame(); cancelAll();
  st = null; view.reset();
  $('settings').hidden = true;
  showIntro();
});
$('skipBtn').addEventListener('click', () => { if (st && skipWait(story, st, now(), opt())) { $('settings').hidden = true; tick(); } });
$('rewindBtn').addEventListener('click', () => { if (st && rewind(st, now())) { view.reset(); $('settings').hidden = true; tick(); } });
$('varsBtn').addEventListener('click', () => {
  const o = $('varsOut');
  o.hidden = !o.hidden;
  o.textContent = st ? JSON.stringify({ dugum: st.node, ...st.vars, pil: st.meta.pil, durum: lastStatus?.kind }, null, 1) : '';
});
bindSeg('themeSeg', 'theme');
bindSeg('sizeSeg', 'size', Number);
bindSeg('speedSeg', 'speed', Number);
$('devBox').hidden = !dev;
$('versionText').textContent = `Bilinmeyen Numara ${VERSION} (${BUILD})`;

// ---------- Ekranlar ----------
function showIntro() {
  $('chat').hidden = true;
  $('intro').hidden = false;
}
function showChat() {
  $('intro').hidden = true;
  $('chat').hidden = false;
  tick();
}

$('startBtn').addEventListener('click', async () => {
  $('startBtn').disabled = true;
  await requestPermission();
  st = newState(now());
  saveGame(st);
  $('startBtn').disabled = false;
  showChat();
});

// ---------- Başlat ----------
(async function boot() {
  applyPrefs();
  try {
    story = await loadStory();
  } catch (e) {
    document.body.innerHTML = `<p style="padding:24px">Hikâye yüklenemedi: ${e.message}</p>`;
    return;
  }
  st = loadGame();
  window.SplashScreen?.hide?.();
  if (st) { cancelAll(); showChat(); } else showIntro();
})();
