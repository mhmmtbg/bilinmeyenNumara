// Sohbet ekranı çizimi: mesaj baloncukları, ayraçlar, alt alan.
import { photoSvg } from './photos.js';

const $ = id => document.getElementById(id);
const pad = n => String(n).padStart(2, '0');
export const hhmm = at => { const d = new Date(at); return `${pad(d.getHours())}:${pad(d.getMinutes())}`; };

const AYLAR = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'];
function dateLabel(at) {
  const d = new Date(at), t = new Date();
  const day = x => new Date(x.getFullYear(), x.getMonth(), x.getDate()).getTime();
  const diff = Math.round((day(t) - day(d)) / 86400000);
  if (diff === 0) return 'Bugün';
  if (diff === 1) return 'Dün';
  return `${d.getDate()} ${AYLAR[d.getMonth()]}`;
}
const dateKey = at => { const d = new Date(at); return `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`; };

function el(tag, cls, html) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (html !== undefined) e.innerHTML = html;
  return e;
}
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);

function waveBars(seed, n = 34) {
  let h = 2166136261;
  for (const ch of seed) h = Math.imul(h ^ ch.charCodeAt(0), 16777619);
  let out = '';
  for (let i = 0; i < n; i++) {
    h = Math.imul(h ^ (h >>> 13), 1274126177);
    const v = 20 + ((h >>> 0) % 80);
    out += `<i style="height:${v}%"></i>`;
  }
  return out;
}

export function createLogView(onPhoto) {
  const log = $('log');
  let lastSeq = 0;
  let lastDate = null;
  let typingEl = null;

  function entryEl(e) {
    const time = `<span class="t">${hhmm(e.at)}</span>`;
    switch (e.kind) {
      case 'msg': {
        const speaker = e.from !== 'Ece' ? `<span class="speaker">${esc(e.from)}</span>` : '';
        return el('div', 'msg in', `${speaker}${esc(e.text)}${time}`);
      }
      case 'me': return el('div', 'msg out', `${esc(e.text)}${time}`);
      case 'photo': {
        const b = el('button', 'msg in photo', `<span class="photo-img">${photoSvg(e.key)}</span>${e.caption ? `<span class="cap">${esc(e.caption)}</span>` : ''}${time}`);
        b.setAttribute('aria-label', `Fotoğraf: ${e.caption || ''}. Büyütmek için dokun.`);
        b.addEventListener('click', () => onPhoto(e));
        return b;
      }
      case 'voice':
        return el('div', 'msg in voice', `<div class="voice-row"><svg class="ic" aria-hidden="true"><use href="#i-mic"/></svg><span class="wave" aria-hidden="true">${waveBars(e.text)}</span><span class="voice-len">${esc(e.len)}</span></div><div class="voice-text">${esc(e.text)}</div>${time}`);
      case 'sys': return el('div', 'sys', esc(e.text));
      case 'day': return el('div', 'day', `${e.n}. gün<b>${esc(e.text)}</b>`);
      case 'end': return el('div', 'day', `Son<b>${esc(e.text)}</b>`);
      default: return el('div', 'sys', '');
    }
  }

  function nearBottom() { return log.scrollHeight - log.scrollTop - log.clientHeight < 140; }
  function toBottom(smooth) {
    log.style.scrollBehavior = smooth ? 'smooth' : 'auto';
    log.scrollTop = log.scrollHeight;
  }

  return {
    reset() { log.innerHTML = ''; lastSeq = 0; lastDate = null; typingEl = null; },
    sync(st, typing) {
      // Geri sarma sonrası günlük kısaldıysa baştan çiz
      if (st.log.length && st.log[st.log.length - 1].id < lastSeq) this.reset();
      if (!st.log.length && lastSeq) this.reset();
      const stick = nearBottom() || lastSeq === 0;
      const fresh = st.log.filter(e => e.id > lastSeq);
      if (typingEl) { typingEl.remove(); typingEl = null; }
      const firstPaint = lastSeq === 0;
      for (const e of fresh) {
        const k = dateKey(e.at);
        if (k !== lastDate && e.kind !== 'day') {
          log.append(el('div', 'date-sep', dateLabel(e.at)));
          lastDate = k;
        }
        const node = entryEl(e);
        if (firstPaint) node.style.animation = 'none';
        log.append(node);
        lastSeq = e.id;
      }
      if (typing) {
        typingEl = el('div', 'typing', '<i></i><i></i><i></i>');
        typingEl.setAttribute('aria-label', 'yazıyor');
        log.append(typingEl);
      }
      if (stick || fresh.some(e => e.kind === 'me')) toBottom(!firstPaint);
    },
  };
}

// ---------- Alt alan ----------
export function renderDock(st, status, h) {
  const dock = $('dock');
  dock.innerHTML = '';
  const name = st.meta.ad || 'Bilinmeyen Numara';

  if (status.kind === 'choice') {
    st.waiting.opts.forEach((o, i) => {
      const b = el('button', 'choice', esc(o.text));
      b.addEventListener('click', () => h.choose(i), { once: true });
      dock.append(b);
    });
    return;
  }
  if (status.kind === 'input') {
    if (st.waiting.hint) dock.append(el('div', 'input-hint', esc(st.waiting.hint)));
    const row = el('form', 'input-row');
    row.innerHTML = `<input type="text" autocomplete="off" autocapitalize="off" spellcheck="false" placeholder="Bir şey yaz…" aria-label="Cevabın"><button class="send" aria-label="Gönder"><svg class="ic"><use href="#i-send"/></svg></button>`;
    row.addEventListener('submit', ev => {
      ev.preventDefault();
      const v = row.querySelector('input').value;
      if (v.trim()) h.answer(v);
    });
    dock.append(row);
    return;
  }
  if (status.kind === 'ended') {
    dock.append(el('div', 'ending', `<b>${esc(st.ended.title)}</b><span class="muted small">Hikâye bitti. Ayarlardan baştan başlayabilirsin.</span>`));
    return;
  }
  if (status.kind === 'paused') {
    dock.append(el('div', 'dock-note', `<svg class="ic" aria-hidden="true"><use href="#i-clock"/></svg><span>${esc(st.paused.text || 'Devamı yakında.')}</span>`));
    return;
  }
  if (status.kind === 'typing') {
    dock.append(el('div', 'dock-note', `<span>${esc(status.from === 'Ece' ? name : status.from)} yazıyor…</span>`));
    return;
  }
  // uzakta
  const wait = status.wakeAt - h.now();
  if (wait < 90_000) {
    dock.append(el('div', 'dock-note', '<span>…</span>'));
  } else {
    const extra = h.dev ? ` <span class="small">(test: ${hhmm(h.realWake(status.wakeAt))})</span>` : '';
    dock.append(el('div', 'dock-note', `<svg class="ic" aria-hidden="true"><use href="#i-moon"/></svg><span>${esc(name)} şu an uzakta. Yazınca bildirim gelecek.${extra}</span>`));
  }
}

export function renderHeader(st, status, now) {
  const name = st.meta.ad || 'Bilinmeyen Numara';
  $('whoName').textContent = name;
  const av = $('avatar');
  av.textContent = st.meta.ad ? st.meta.ad[0] : '?';
  av.classList.toggle('named', !!st.meta.ad);

  const s = $('whoStatus');
  let text = '', live = false;
  if (status.kind === 'typing') { text = 'yazıyor…'; live = true; }
  else if (status.kind === 'choice' || status.kind === 'input') { text = 'çevrimiçi'; live = true; }
  else if (status.kind === 'away' && status.wakeAt - now < 90_000 && st.meta.durum !== 'çevrimdışı') { text = 'çevrimiçi'; live = true; }
  else {
    const last = [...st.log].reverse().find(e => e.kind !== 'me' && e.kind !== 'day' && e.kind !== 'sys');
    text = last ? `son görülme ${hhmm(last.at)}` : '';
  }
  s.textContent = text;
  s.classList.toggle('live', live);

  $('infoDay').textContent = st.meta.gun ? `${st.meta.gun}. gün · ${st.meta.gunAdi}` : '';
  const bat = $('infoBat');
  if (st.meta.pil === null || st.meta.pil === undefined) { bat.hidden = true; }
  else {
    bat.hidden = false;
    $('batText').textContent = `%${st.meta.pil}`;
    $('batFill').setAttribute('width', (19 * st.meta.pil / 100).toFixed(1));
    bat.classList.toggle('low', st.meta.pil <= 20);
  }
}
