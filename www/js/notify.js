// Yerel bildirimler (Capacitor LocalNotifications). Tarayıcıda sessizce devre dışı.
//
// Neden bu şekilde:
// - Android 12+ "tam zamanlı alarm" izni çoğu telefonda kapalıdır. Eklenti bu izin yokken bildirim
//   kurulmak istenince ayarlar ekranını açmaya çalışır; uygulama arka plana geçerken bu olmaz ve hiçbir
//   bildirim kurulmaz. Bu yüzden bildirimler "yaklaşık zamanlı" (isExactNotification:false) kurulur;
//   Android birkaç dakika kaydırabilir, hikâye için sorun değil.
// - Kurulum yalnızca arka plana geçişe bırakılmaz (o anda JS durdurulabilir): uygulama açıkken de her
//   değişiklikte planlanır. Uygulama öndeyken düşen bildirimler hemen kaldırılır.
// - Aynı kimlik aralığı (1000–1039) her seferinde yeniden kullanılır; önce iptal, sonra kurma sırayla
//   eklentinin kuyruğuna girer, beklemeye gerek yoktur.

const LN = () => window.Capacitor?.Plugins?.LocalNotifications;
const MAX = 40;
const BASE_ID = 1000;
const BURST_GAP = 45_000;   // bu kadar sessizlikten sonra gelen ilk mesaj bildirim olur
const CHANNEL = 'mesajlar';

export const notifyAvailable = () => !!LN();

let channelReady = false;
export async function ensureChannel() {
  const ln = LN();
  if (!ln || channelReady) return;
  try {
    await ln.createChannel?.({ id: CHANNEL, name: 'Mesajlar', description: 'Gelen mesajlar', importance: 4, visibility: 1, vibration: true });
    channelReady = true;
  } catch {}
}

export async function permissionState() {
  const ln = LN();
  if (!ln) return 'yok';
  try { return (await ln.checkPermissions()).display; } catch { return 'yok'; }
}

export async function requestPermission() {
  const ln = LN();
  if (!ln) return 'yok';
  await ensureChannel();
  try { return (await ln.requestPermissions()).display; } catch { return 'denied'; }
}

export function preview(e) {
  if (e.kind === 'photo') return '📷 Fotoğraf';
  if (e.kind === 'voice') return '🎤 Ses kaydı';
  return e.text;
}

const MAIN = new Set(['Elif', 'Ece']);   // eski kayıtlar ilk karakter adıyla (Ece) yazılmış olabilir

// items: upcoming() çıktısı; now: şimdiki an; title: başlıktaki ad
export function pickNotifications(items, now, title) {
  const out = [];
  let prev = now;
  for (const e of items) {
    if (!['msg', 'photo', 'voice', 'end'].includes(e.kind)) { prev = e.at; continue; }
    if (e.at - prev >= BURST_GAP) out.push({ at: e.at, title: e.from && !MAIN.has(e.from) ? e.from : title, body: preview(e) });
    prev = e.at;
    if (out.length >= MAX) break;
  }
  return out;
}

const ALL_IDS = Array.from({ length: MAX }, (_, i) => ({ id: BASE_ID + i }));
let lastSig = '';

export function schedule(list) {
  const ln = LN();
  if (!ln) return;
  const sig = list.map(n => `${n.at}|${n.body}`).join('\n');
  if (sig === lastSig) return;          // değişiklik yoksa eklentiyi yorma
  lastSig = sig;
  ln.cancel({ notifications: ALL_IDS }).catch(() => {});
  if (!list.length) return;
  ln.schedule({
    notifications: list.map((n, i) => ({
      id: BASE_ID + i,
      title: n.title,
      body: n.body,
      channelId: CHANNEL,
      smallIcon: 'ic_stat_message',
      iconColor: '#79CDB2',
      isExactNotification: false,
      schedule: { at: new Date(Math.max(n.at, Date.now() + 2000)), allowWhileIdle: true },
    })),
  }).catch(e => { lastSig = ''; console.warn('Bildirim kurulamadı', e); });
}

export function cancelAll() {
  const ln = LN();
  if (!ln) return;
  lastSig = '';
  ln.cancel({ notifications: ALL_IDS }).catch(() => {});
}

// Uygulama öndeyken düşen bildirimleri bildirim çekmecesinden kaldır
export function clearDelivered() {
  LN()?.removeAllDeliveredNotifications?.().catch?.(() => {});
}

export function onReceived(fn) {
  LN()?.addListener?.('localNotificationReceived', fn);
}

// Ayarlardaki "Bildirimi dene": 5 saniye sonra bir deneme bildirimi
export async function testNotification(title) {
  const ln = LN();
  if (!ln) return 'yok';
  const p = await requestPermission();
  if (p !== 'granted') return p;
  try {
    await ln.schedule({
      notifications: [{
        id: 999, title, body: 'Bildirimler çalışıyor. Uygulamayı kapatabilirsin.', channelId: CHANNEL,
        smallIcon: 'ic_stat_message', isExactNotification: false,
        schedule: { at: new Date(Date.now() + 5000), allowWhileIdle: true },
      }],
    });
    return 'kuruldu';
  } catch (e) { return `hata: ${e?.message || e}`; }
}
