// Gerçek zamanlı senaryo motoru. Saf: "şimdi" her çağrıda parametre olarak verilir.
// st.cursor = son olayın gerçekleştiği an (ms). Bir mesajın teslim anı = cursor + yazma süresi.
// Uygulama kapalıyken geçen zaman, advance(now) çağrıldığında olması gereken saatlerle yakalanır.

export const SAVE_VERSION = 1;
const READ_PAUSE = 1400;          // oyuncu cevap verdikten sonra Ece'nin okuyup yazmaya başlaması
const MAX_STEPS = 20000;

export function typingMs(op) {
  if (op.t === 'photo') return 2600;
  if (op.t === 'voice') return 4200;
  return Math.min(8000, 1000 + op.text.length * 50);
}

export function newState(now, vars = {}) {
  return {
    v: SAVE_VERSION,
    node: 'basla', i: 0,
    cursor: now,
    vars: { guven: 3, ...vars },
    log: [],
    seq: 0,
    meta: { ad: null, pil: null, durum: null, gun: 0, gunAdi: '' },
    waiting: null,
    ended: null,
    paused: null,
    history: [],
    startedAt: now,
  };
}

// Bir sonraki "HH:MM" anı (yerel saat), en erken `from` anından sonra
export function nextClock(from, h, m) {
  const d = new Date(from);
  d.setHours(h, m, 0, 0);
  if (d.getTime() <= from) d.setDate(d.getDate() + 1);
  return d.getTime();
}

function evalCond(st, c) {
  const val = c.v === 'saat' ? new Date(st.cursor).getHours() : (st.vars[c.v] ?? 0);
  switch (c.op) {
    case '>=': return val >= c.n;
    case '<=': return val <= c.n;
    case '>': return val > c.n;
    case '<': return val < c.n;
    case '==': return val === c.n;
    case '!=': return val !== c.n;
  }
  return false;
}

function jump(story, st, to) {
  if (!story.nodes[to]) throw new Error(`Senaryoda "${to}" düğümü yok`);
  st.node = to; st.i = 0;
}

function addLog(st, entry) {
  st.log.push({ id: ++st.seq, ...entry });
}

function currentOp(story, st) {
  // Düğüm bitince sıradaki düğüme düş
  for (;;) {
    const ops = story.nodes[st.node];
    if (!ops) throw new Error(`Senaryoda "${st.node}" düğümü yok`);
    if (st.i < ops.length) return ops[st.i];
    const idx = story.order.indexOf(st.node);
    const next = story.order[idx + 1];
    if (!next) return null;
    st.node = next; st.i = 0;
  }
}

function clamp(n, a, b) { return Math.max(a, Math.min(b, n)); }

/**
 * `now` anına kadar olması gereken her şeyi oynatır (st'yi değiştirir).
 * Dönen durum arayüze ne göstereceğini söyler:
 *  - { kind:'typing', from, at }   şu an yazıyor; `at` anında mesaj düşecek
 *  - { kind:'away', wakeAt }       uzakta; `wakeAt` anında yazmaya başlayacak
 *  - { kind:'choice' } / { kind:'input' } oyuncunun cevabı bekleniyor
 *  - { kind:'ended' } / { kind:'paused' }
 */
export function advance(story, st, now, opt = {}) {
  const scale = opt.scale || 1;
  for (let steps = 0; steps < MAX_STEPS; steps++) {
    if (st.ended) return { kind: 'ended' };
    if (st.paused) return { kind: 'paused' };
    if (st.waiting) return { kind: st.waiting.type };

    const op = currentOp(story, st);
    if (!op) { st.paused = { text: '', at: st.cursor }; return { kind: 'paused' }; }

    switch (op.t) {
      case 'msg': case 'photo': case 'voice': {
        const dur = typingMs(op) / scale;
        const at = st.cursor + dur;
        if (at > now) {
          const from = op.t === 'msg' ? op.from : 'Ece';
          return now >= st.cursor ? { kind: 'typing', from, at } : { kind: 'away', wakeAt: st.cursor };
        }
        if (op.t === 'msg') addLog(st, { kind: 'msg', from: op.from, text: op.text, at });
        else if (op.t === 'photo') addLog(st, { kind: 'photo', from: 'Ece', key: op.key, caption: op.caption, at });
        else addLog(st, { kind: 'voice', from: 'Ece', key: op.key, text: op.text, at });
        st.cursor = at; st.i++;
        break;
      }
      case 'cinema':
        if (st.cursor > now) return { kind: 'away', wakeAt: st.cursor };
        addLog(st, { kind: 'cinema', key: op.key, at: st.cursor }); st.i++; break;
      case 'sys':
        if (st.cursor > now) return { kind: 'away', wakeAt: st.cursor };
        addLog(st, { kind: 'sys', text: op.text, at: st.cursor }); st.i++; break;
      case 'day':
        if (st.cursor > now) return { kind: 'away', wakeAt: st.cursor };
        st.meta.gun = op.n; st.meta.gunAdi = op.title;
        addLog(st, { kind: 'day', n: op.n, text: op.title, at: st.cursor }); st.i++; break;
      case 'meta':
        if (op.k === 'pil') st.meta.pil = clamp(op.val, 0, 100);
        else st.meta[op.k] = op.val;
        st.i++; break;
      case 'set': {
        const old = st.vars[op.v] ?? 0;
        st.vars[op.v] = op.op === '=' ? op.n : op.op === '+' ? old + op.n : old - op.n;
        if (op.v === 'guven') st.vars.guven = clamp(st.vars.guven, 0, 10);
        st.i++; break;
      }
      case 'wait':
        st.cursor += op.ms / scale; st.i++; break;
      case 'until': {
        const target = nextClock(st.cursor + op.min, op.h, op.m);
        st.cursor += (target - st.cursor) / scale; st.i++; break;
      }
      case 'goto': jump(story, st, op.to); break;
      case 'if':
        if (evalCond(st, op.cond)) jump(story, st, op.to); else st.i++;
        break;
      case 'choice': {
        if (st.cursor > now) return { kind: 'away', wakeAt: st.cursor };
        const opts = op.opts.filter(o => !o.cond || evalCond(st, o.cond));
        st.waiting = { type: 'choice', opts: opts.map(o => ({ text: o.text, to: o.to })), since: st.cursor };
        return { kind: 'choice' };
      }
      case 'input': {
        if (st.cursor > now) return { kind: 'away', wakeAt: st.cursor };
        st.waiting = { type: 'input', hint: op.hint, answers: op.answers, since: st.cursor };
        return { kind: 'input' };
      }
      case 'end':
        if (st.cursor > now) return { kind: 'away', wakeAt: st.cursor };
        st.ended = { key: op.key, title: op.title, at: st.cursor };
        addLog(st, { kind: 'end', key: op.key, text: op.title, at: st.cursor });
        return { kind: 'ended' };
      case 'pause':
        if (st.cursor > now) return { kind: 'away', wakeAt: st.cursor };
        st.paused = { text: op.text, at: st.cursor };
        return { kind: 'paused' };
      default:
        throw new Error(`Bilinmeyen işlem ${op.t}`);
    }
  }
  throw new Error('Senaryo sonsuz döngüye girdi (bekleme olmadan kendine dönen düğüm)');
}

function snapshot(st) {
  st.history.push({ node: st.node, i: st.i, vars: { ...st.vars }, meta: { ...st.meta }, logLen: st.log.length, seq: st.seq, waiting: st.waiting, cursor: st.cursor });
  if (st.history.length > 60) st.history.shift();
}

export function choose(story, st, idx, now, opt = {}) {
  const w = st.waiting;
  if (!w || w.type !== 'choice') throw new Error('Şu an seçim beklenmiyor');
  const o = w.opts[idx];
  if (!o) throw new Error('Geçersiz seçenek');
  snapshot(st);
  addLog(st, { kind: 'me', text: o.text, at: now });
  st.waiting = null;
  st.cursor = now + READ_PAUSE / (opt.scale || 1);
  jump(story, st, o.to);
}

export function answer(story, st, text, now, normalize, opt = {}) {
  const w = st.waiting;
  if (!w || w.type !== 'input') throw new Error('Şu an yazılı cevap beklenmiyor');
  const clean = text.trim();
  if (!clean) return false;
  const n = normalize(clean);
  const hit = w.answers.find(a => !a.any && a.words.some(word => n === word || n.split(' ').includes(word) || n.includes(word)))
    || w.answers.find(a => a.any);
  snapshot(st);
  addLog(st, { kind: 'me', text: clean, at: now });
  st.waiting = null;
  st.cursor = now + READ_PAUSE / (opt.scale || 1);
  jump(story, st, hit.to);
  return true;
}

// Son seçimin öncesine dön (ileride "geri sar" özelliği için)
export function rewind(st, now) {
  const h = st.history.pop();
  if (!h) return false;
  st.node = h.node; st.i = h.i; st.vars = h.vars; st.meta = h.meta; st.seq = h.seq;
  st.log.length = h.logLen; st.waiting = h.waiting; st.ended = null; st.paused = null;
  st.cursor = Math.min(h.cursor, now);
  if (st.waiting) st.waiting.since = st.cursor;
  return true;
}

// Uzun beklemeyi bitirir: Ece hemen yazmaya başlar (geliştirici / ileride ödüllü reklam)
export function skipWait(story, st, now, opt = {}) {
  const s = advance(story, st, now, opt);
  if (s.kind !== 'away') return false;
  st.cursor = now;
  return true;
}

/**
 * Geleceği kopya bir durum üzerinde oynatır: oyuncu cevap verene kadar düşecek mesajlar.
 * Bildirim planlaması için kullanılır; asıl duruma dokunmaz.
 */
export function upcoming(story, st, now, opt = {}) {
  const copy = JSON.parse(JSON.stringify(st));
  const before = copy.log.length;
  const s = advance(story, copy, Number.MAX_SAFE_INTEGER / 2, opt);
  const items = copy.log.slice(before).filter(e => e.at > now);
  return { items, final: s.kind, endsAt: copy.cursor };
}
