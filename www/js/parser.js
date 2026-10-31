// .hikaye senaryo dili ayrıştırıcısı. Saf fonksiyon: metin girer, düğümler çıkar.
// Dil tanımı: docs/PLAN.md → "Senaryo dili"

const DUR_RE = /^(\d+(?:[.,]\d+)?)\s*(sn|dk|sa)$/i;
const UNIT = { sn: 1000, dk: 60_000, sa: 3_600_000 };

export function parseDuration(s) {
  let total = 0;
  for (const part of s.trim().split(/\s+/)) {
    const m = part.match(DUR_RE);
    if (!m) return null;
    total += parseFloat(m[1].replace(',', '.')) * UNIT[m[2].toLowerCase()];
  }
  return total;
}

export function parseCond(s) {
  const m = s.trim().match(/^([a-zçğıöşü_][\wçğıöşü]*)\s*(>=|<=|==|!=|>|<)\s*(-?\d+)$/i);
  if (!m) return null;
  return { v: m[1], op: m[2], n: Number(m[3]) };
}

export function parse(text, file = 'hikaye') {
  const nodes = {};
  const order = [];
  const errors = [];
  let cur = null;
  let lastWasChoice = false;
  let lastWasInput = false;

  const err = (ln, msg) => errors.push(`${file}:${ln}: ${msg}`);
  const push = (ln, op) => {
    if (!cur) { err(ln, 'düğüm dışında satır (önce "=== ad" yaz)'); return; }
    op.ln = ln;
    nodes[cur].push(op);
  };

  text.split(/\r?\n/).forEach((raw, i) => {
    const ln = i + 1;
    const line = raw.trim();
    if (!line || line.startsWith('#')) return;
    const wasChoice = lastWasChoice, wasInput = lastWasInput;
    lastWasChoice = false; lastWasInput = false;

    if (line.startsWith('===')) {
      const id = line.slice(3).trim();
      if (!/^[\w]+$/.test(id)) { err(ln, `geçersiz düğüm adı "${id}"`); return; }
      if (nodes[id]) err(ln, `"${id}" düğümü iki kez tanımlı`);
      nodes[id] = []; order.push(id); cur = id;
      return;
    }

    if (line.startsWith('*')) {
      const m = line.match(/^\*\s*(?:\[([^\]]+)\]\s*)?(.+?)\s*->\s*(\w+)$/);
      if (!m) { err(ln, 'seçenek biçimi: * Metin -> hedef'); return; }
      const cond = m[1] ? parseCond(m[1]) : null;
      if (m[1] && !cond) err(ln, `geçersiz koşul "${m[1]}"`);
      const opt = { text: m[2].trim(), to: m[3], cond };
      const last = cur && nodes[cur][nodes[cur].length - 1];
      if (wasChoice && last && last.t === 'choice') last.opts.push(opt);
      else push(ln, { t: 'choice', opts: [opt] });
      lastWasChoice = true;
      return;
    }

    if (line.startsWith('??')) {
      push(ln, { t: 'input', hint: line.slice(2).trim(), answers: [] });
      lastWasInput = true;
      return;
    }
    if (line.startsWith('=')) {
      const last = cur && nodes[cur][nodes[cur].length - 1];
      if (!wasInput || !last || last.t !== 'input') { err(ln, '"=" satırı yalnızca "??" satırından sonra gelir'); return; }
      const m = line.match(/^=\s*(.+?)\s*->\s*(\w+)$/);
      if (!m) { err(ln, 'cevap biçimi: = cevap1|cevap2 -> hedef'); return; }
      const any = m[1].trim() === '*';
      last.answers.push({ any, words: any ? [] : m[1].split('|').map(normalize).filter(Boolean), to: m[2] });
      lastWasInput = true;
      return;
    }

    if (line.startsWith('~')) {
      const body = line.slice(1).trim();
      const at = body.match(/^@(\d{1,2}):(\d{2})(?:\s+en az\s+(.+))?$/i);
      if (at) {
        const h = +at[1], mi = +at[2];
        if (h > 23 || mi > 59) err(ln, `geçersiz saat "${body}"`);
        const min = at[3] ? parseDuration(at[3]) : 0;
        if (min === null) err(ln, `geçersiz süre "${at[3]}"`);
        push(ln, { t: 'until', h, m: mi, min: min || 0 });
        return;
      }
      const ms = parseDuration(body);
      if (ms === null) { err(ln, `geçersiz bekleme "${body}" (örn. ~ 30sn, ~ 5dk, ~ 2sa, ~ @21:10)`); return; }
      push(ln, { t: 'wait', ms });
      return;
    }

    if (line.startsWith('$')) {
      const m = line.match(/^\$\s*([a-zçğıöşü_][\wçğıöşü]*)\s*([+\-=])\s*(-?\d+)$/i);
      if (!m) { err(ln, 'değişken biçimi: $ ad + 1 / $ ad = 1'); return; }
      push(ln, { t: 'set', v: m[1], op: m[2], n: Number(m[3]) });
      return;
    }

    if (line.startsWith('?')) {
      const m = line.match(/^\?\s*(.+?)\s*->\s*(\w+)$/);
      const cond = m && parseCond(m[1]);
      if (!cond) { err(ln, 'koşul biçimi: ? guven >= 3 -> hedef'); return; }
      push(ln, { t: 'if', cond, to: m[2] });
      return;
    }

    if (line.startsWith('->')) {
      const to = line.slice(2).trim();
      if (!/^\w+$/.test(to)) { err(ln, `geçersiz hedef "${to}"`); return; }
      push(ln, { t: 'goto', to });
      return;
    }

    if (line.startsWith('>>')) { push(ln, { t: 'sys', text: line.slice(2).trim() }); return; }

    if (line.startsWith('!')) {
      const m = line.match(/^!(\w+)\s*(.*)$/);
      const cmd = m[1], arg = m[2].trim();
      const [a, b] = arg.split('|').map(s => s.trim());
      switch (cmd) {
        case 'foto': push(ln, { t: 'photo', key: a, caption: b || '' }); break;
        case 'ses': push(ln, { t: 'voice', len: a, text: b || '' }); break;
        case 'pil': push(ln, { t: 'meta', k: 'pil', val: Number(a) }); break;
        case 'ad': push(ln, { t: 'meta', k: 'ad', val: a }); break;
        case 'durum': push(ln, { t: 'meta', k: 'durum', val: a }); break;
        case 'gun': {
          const g = a.match(/^(\d+)\s*(.*)$/);
          if (!g) err(ln, '!gun 2 Başlık');
          else push(ln, { t: 'day', n: +g[1], title: g[2] });
          break;
        }
        case 'son': push(ln, { t: 'end', key: a, title: b || a }); break;
        case 'ara': push(ln, { t: 'pause', text: arg }); break;
        default: err(ln, `bilinmeyen komut "!${cmd}"`);
      }
      return;
    }

    // Konuşmacılı mesaj: "Nazlı: metin" (yalnızca tanımlı konuşmacılar)
    const sp = line.match(/^(Nazlı|Rıza|Selim|Bilinmeyen):\s*(.+)$/);
    if (sp) { push(ln, { t: 'msg', from: sp[1], text: sp[2] }); return; }
    push(ln, { t: 'msg', from: 'Ece', text: line });
  });

  return { nodes, order, errors };
}

// Birden çok dosyayı birleştirir (sıra korunur: dosya sonundaki düğüm bir sonraki dosyanın ilk düğümüne düşer)
export function merge(parts) {
  const out = { nodes: {}, order: [], errors: [] };
  for (const p of parts) {
    for (const id of p.order) {
      if (out.nodes[id]) out.errors.push(`"${id}" düğümü birden çok dosyada tanımlı`);
      out.nodes[id] = p.nodes[id];
      out.order.push(id);
    }
    out.errors.push(...p.errors);
  }
  return out;
}

// Türkçe karakterleri sadeleştirir: yazarak verilen cevaplar için
export function normalize(s) {
  return String(s)
    .toLocaleLowerCase('tr')
    .replace(/[çğıöşüâîû]/g, c => ({ ç: 'c', ğ: 'g', ı: 'i', ö: 'o', ş: 's', ü: 'u', â: 'a', î: 'i', û: 'u' })[c])
    .replace(/[^a-z0-9 ]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

// Senaryo bütünlüğü: hedefler var mı, seçenek grupları dolu mu
export function validate(story) {
  const errors = [...story.errors];
  const ids = new Set(story.order);
  for (const id of story.order) {
    for (const op of story.nodes[id]) {
      const where = `${id} (satır ${op.ln})`;
      const targets = op.t === 'choice' ? op.opts.map(o => o.to)
        : op.t === 'input' ? op.answers.map(a => a.to)
        : (op.t === 'goto' || op.t === 'if') ? [op.to] : [];
      for (const to of targets) if (!ids.has(to)) errors.push(`${where}: "${to}" diye bir düğüm yok`);
      if (op.t === 'input' && !op.answers.some(a => a.any)) errors.push(`${where}: yazılı cevapta "= * -> hedef" (yanlış cevap) dalı yok`);
      if (op.t === 'choice' && op.opts.length > 3) errors.push(`${where}: en fazla 3 seçenek`);
      if (op.t === 'choice') for (const o of op.opts) if (o.text.length > 48) errors.push(`${where}: seçenek çok uzun (${o.text.length} > 48): "${o.text}"`);
    }
  }
  if (!ids.has('basla')) errors.push('"basla" düğümü yok');
  return errors;
}
