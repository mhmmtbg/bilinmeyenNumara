// Yerel bildirimler (Capacitor LocalNotifications). Tarayıcıda sessizce devre dışı.
// Uygulama arka plana geçince gelecek mesajlar için bildirim kurulur, öne gelince hepsi iptal edilir.

const LN = () => window.Capacitor?.Plugins?.LocalNotifications;
const MAX = 40;
const BURST_GAP = 45_000;   // bu kadar sessizlikten sonra gelen ilk mesaj bildirim olur

export const notifyAvailable = () => !!LN();

export async function permissionState() {
  const ln = LN();
  if (!ln) return 'yok';
  try { return (await ln.checkPermissions()).display; } catch { return 'yok'; }
}

export async function requestPermission() {
  const ln = LN();
  if (!ln) return 'yok';
  try {
    await ln.createChannel?.({ id: 'mesaj', name: 'Mesajlar', description: 'Gelen mesajlar', importance: 4, visibility: 0, vibration: true });
  } catch {}
  try { return (await ln.requestPermissions()).display; } catch { return 'denied'; }
}

export function preview(e) {
  if (e.kind === 'photo') return '📷 Fotoğraf';
  if (e.kind === 'voice') return '🎤 Ses kaydı';
  if (e.kind === 'end') return e.text;
  return e.text;
}

// items: upcoming() çıktısı; now: şimdiki an; title: başlıktaki ad
export function pickNotifications(items, now, title) {
  const out = [];
  let prev = now;
  for (const e of items) {
    if (!['msg', 'photo', 'voice', 'end'].includes(e.kind)) { prev = e.at; continue; }
    if (e.at - prev >= BURST_GAP) out.push({ at: e.at, title: e.from && e.from !== 'Ece' ? e.from : title, body: preview(e) });
    prev = e.at;
    if (out.length >= MAX) break;
  }
  return out;
}

export async function schedule(list) {
  const ln = LN();
  if (!ln) return;
  await cancelAll();
  if (!list.length) return;
  try {
    await ln.schedule({
      notifications: list.map((n, i) => ({
        id: 1000 + i,
        title: n.title,
        body: n.body,
        channelId: 'mesaj',
        schedule: { at: new Date(n.at), allowWhileIdle: true },
        smallIcon: 'ic_stat_message',
      })),
    });
  } catch (e) { console.warn('Bildirim kurulamadı', e); }
}

export async function cancelAll() {
  const ln = LN();
  if (!ln) return;
  try {
    const p = await ln.getPending();
    if (p.notifications?.length) await ln.cancel({ notifications: p.notifications.map(n => ({ id: n.id })) });
  } catch {}
}
