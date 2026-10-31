// Senaryo denetçisi: biçim hataları, olmayan hedefler, ulaşılamayan düğümler
// ve bütün dalların bir sona/ara noktasına ulaşıp ulaşmadığı.
// Kullanım: node tools/check-story.mjs   (CI'da STORY_OUT=$GITHUB_STEP_SUMMARY ile rapor yazar)
import { readFileSync, appendFileSync, existsSync } from 'node:fs';
import { parse, merge, validate } from '../www/js/parser.js';
import { newState, advance, choose, answer } from '../www/js/engine.js';
import { normalize } from '../www/js/parser.js';
import { STORY_FILES } from '../www/js/story.js';

const story = merge(STORY_FILES.map(f => parse(readFileSync(new URL(`../www/hikaye/${f}`, import.meta.url), 'utf8'), f)));
const errors = validate(story);

// Dosya denetimi: senaryonun andığı fotoğraf, ses ve sinema dosyaları var mı
const www = p => new URL(`../www/${p}`, import.meta.url);
const sesMeta = existsSync(www('ses/ses.json')) ? JSON.parse(readFileSync(www('ses/ses.json'), 'utf8')) : {};
const sinema = existsSync(www('sinema/sinema.json')) ? JSON.parse(readFileSync(www('sinema/sinema.json'), 'utf8')) : {};
for (const id of story.order) for (const op of story.nodes[id]) {
  const where = `${id} (satır ${op.ln})`;
  if (op.t === 'photo' && !existsSync(www(`img/foto/${op.key}.jpg`))) errors.push(`${where}: img/foto/${op.key}.jpg yok`);
  if (op.t === 'voice') {
    if (!existsSync(www(`ses/${op.key}.ogg`))) errors.push(`${where}: ses/${op.key}.ogg yok`);
    if (!sesMeta[op.key]) errors.push(`${where}: ses.json içinde "${op.key}" yok`);
  }
  if (op.t === 'cinema') {
    const sc = sinema[op.key];
    if (!sc) { errors.push(`${where}: sinema.json içinde "${op.key}" yok`); continue; }
    if (!existsSync(www(sc.ses))) errors.push(`${where}: ${sc.ses} yok`);
    for (const f of sc.kareler) if (f.img && !existsSync(www(f.img))) errors.push(`${where}: ${f.img} yok`);
  }
}

// Bütün dalları dolaş (başlangıç saati sabah 10:00 ve gece 22:30 iki ayrı senaryo)
const START_TIMES = [
  ['sabah 10:00', new Date(2026, 10, 2, 10, 0).getTime()],
  ['gece 22:30', new Date(2026, 10, 2, 22, 30).getTime()],
];
const FAR = Number.MAX_SAFE_INTEGER / 2;
const outcomes = new Map();
let paths = 0;
let minActive = Infinity, maxActive = 0, minTotal = Infinity, maxTotal = 0;
let maxChoices = 0;

const seen = new Set();
function walk(st, depth, choices) {
  if (paths > 50000) return;
  if (st.waiting === null) {
    const sig = `${st.node}|${st.i}|${JSON.stringify(st.vars)}|${st.meta.ad}|${st.meta.pil}|${st.startedAt}|${new Date(st.cursor).getHours()}`;
    if (seen.has(sig)) return;
    seen.add(sig);
  }
  // Düğüm ziyaretlerini kaydetmek için adım adım ilerle
  const s = advance(story, st, FAR);
  if (s.kind === 'choice') {
    for (let i = 0; i < st.waiting.opts.length; i++) {
      const c = structuredClone(st);
      choose(story, c, i, c.cursor + 8000);
      walk(c, depth + 1, choices + 1);
    }
    return;
  }
  if (s.kind === 'input') {
    const tries = [...new Set(st.waiting.answers.filter(a => !a.any).map(a => a.words[0])), 'bilmiyorum zzz'];
    for (const t of tries) {
      const c = structuredClone(st);
      answer(story, c, t, c.cursor + 20000, normalize);
      walk(c, depth + 1, choices + 1);
    }
    return;
  }
  paths++;
  const key = s.kind === 'ended' ? `Son: ${st.ended.title}` : `Ara: ${st.paused.text || '(dosya sonu)'}`;
  outcomes.set(key, (outcomes.get(key) || 0) + 1);
  const total = st.cursor - st.startedAt;
  // "Etkin" süre: 2 dakikadan kısa boşluklar (yazışma) toplamı
  let active = 0, prev = st.startedAt;
  for (const e of st.log) { const gap = e.at - prev; if (gap < 120000) active += gap; prev = e.at; }
  minActive = Math.min(minActive, active); maxActive = Math.max(maxActive, active);
  minTotal = Math.min(minTotal, total); maxTotal = Math.max(maxTotal, total);
  maxChoices = Math.max(maxChoices, choices);
}

const fmt = ms => {
  const m = Math.round(ms / 60000);
  return m >= 60 ? `${Math.floor(m / 60)} sa ${m % 60} dk` : `${m} dk`;
};

const report = [];
if (!errors.length) {
  for (const [label, t0] of START_TIMES) {
    try {
      walk(newState(t0), 0, 0);
    } catch (e) { errors.push(`${label}: ${e.message}`); }
  }
  // Durağan erişilebilirlik: seçenek/atlama hedefleri + düğüm sonu atlama değilse sıradaki düğüm
  const visited = new Set(['basla']);
  const queue = ['basla'];
  while (queue.length) {
    const id = queue.shift();
    const ops = story.nodes[id];
    const next = [];
    for (const op of ops) {
      if (op.t === 'choice') next.push(...op.opts.map(o => o.to));
      if (op.t === 'input') next.push(...op.answers.map(a => a.to));
      if (op.t === 'goto' || op.t === 'if') next.push(op.to);
    }
    const last = ops[ops.length - 1];
    const terminal = last && ['goto', 'choice', 'input', 'end', 'pause'].includes(last.t);
    const k = story.order.indexOf(id);
    if (!terminal && k < story.order.length - 1) next.push(story.order[k + 1]);
    for (const n of next) if (!visited.has(n)) { visited.add(n); queue.push(n); }
  }
  for (const id of story.order) if (!visited.has(id)) errors.push(`"${id}" düğümüne hiçbir yerden ulaşılamıyor`);
}

report.push('## Senaryo denetimi', '');
report.push(`- Dosyalar: ${STORY_FILES.join(', ')}`);
report.push(`- Düğüm: ${story.order.length}, mesaj: ${story.order.reduce((n, id) => n + story.nodes[id].filter(o => o.t === 'msg').length, 0)}`);
if (paths) {
  report.push(`- Dal sayısı (iki başlangıç saatiyle): ${paths}, bir oyunda en fazla ${maxChoices} seçim`);
  report.push(`- Etkin yazışma süresi: ${fmt(minActive)} – ${fmt(maxActive)}`);
  report.push(`- Gerçek toplam süre: ${fmt(minTotal)} – ${fmt(maxTotal)}`);
  report.push('', '| Sonuç | Dal |', '| --- | --- |');
  for (const [k, n] of outcomes) report.push(`| ${k} | ${n} |`);
}
report.push('', errors.length ? `### ❌ ${errors.length} hata\n\n${errors.map(e => `- ${e}`).join('\n')}` : '### ✅ Hata yok');

const text = report.join('\n');
console.log(text);
if (process.env.STORY_OUT) appendFileSync(process.env.STORY_OUT, text + '\n');
process.exit(errors.length ? 1 : 0);
