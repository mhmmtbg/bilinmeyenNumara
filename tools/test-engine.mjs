// Motor testleri: node tools/test-engine.mjs
import assert from 'node:assert/strict';
import { parse, normalize, validate } from '../www/js/parser.js';
import { pickNotifications } from '../www/js/notify.js';
import { newState, advance, choose, answer, upcoming, rewind, skipWait, nextClock, typingMs } from '../www/js/engine.js';

let n = 0;
const test = (name, fn) => { fn(); n++; console.log('✓', name); };

const src = `
=== basla
!ad Elif
Merhaba
~ 10dk
İkinci
* Evet -> evet
* [guven>=9] Gizli -> evet
* Hayır -> hayir
=== evet
$ guven + 2
Sevindim
-> sor
=== hayir
Üzüldüm
=== sor
?? Şifre?
= değirmen|degirmen -> dogru
= * -> yanlis
=== dogru
Bildin
~ @21:10 en az 1sa
Akşam oldu
!son iyi | İyi Son
=== yanlis
Bilemedin
!ara Devamı yok
`;
const story = parse(src, 'test');
const T0 = new Date(2026, 10, 2, 10, 0, 0).getTime();

test('ayrıştırma hatasız', () => {
  assert.deepEqual(story.errors, []);
  assert.deepEqual(validate(story), []);
  assert.equal(story.nodes.basla.find(o => o.t === 'choice').opts.length, 3);
});

test('ilk mesaj yazma süresi kadar sonra düşer, öncesinde "yazıyor"', () => {
  const st = newState(T0);
  const s = advance(story, st, T0 + 100);
  assert.equal(s.kind, 'typing');
  assert.equal(st.log.length, 0);
  advance(story, st, T0 + typingMs({ t: 'msg', text: 'Merhaba' }));
  assert.equal(st.log[0].text, 'Merhaba');
  assert.equal(st.meta.ad, 'Elif');
});

test('bekleme sırasında "uzakta", sonra mesaj gerçek saatiyle kaydedilir', () => {
  const st = newState(T0);
  const s = advance(story, st, T0 + 60_000);
  assert.equal(s.kind, 'away');
  advance(story, st, T0 + 3_600_000); // uygulama bir saat kapalı kaldı
  const second = st.log.find(e => e.text === 'İkinci');
  assert.ok(second.at > T0 + 600_000 && second.at < T0 + 620_000, 'mesaj 10. dakikada düşmüş görünmeli');
  assert.equal(st.waiting.type, 'choice');
  assert.equal(st.waiting.opts.length, 2, 'koşullu seçenek gizli');
});

test('seçim, değişken ve yazılı cevap (Türkçe karakter esnek)', () => {
  const st = newState(T0);
  advance(story, st, T0 + 3_600_000);
  choose(story, st, 0, T0 + 3_600_000);
  advance(story, st, T0 + 3_700_000);
  assert.equal(st.vars.guven, 5);
  assert.equal(st.waiting.type, 'input');
  answer(story, st, 'Bence DEĞİRMEN!', T0 + 3_700_000, normalize);
  advance(story, st, T0 + 3_710_000);
  assert.ok(st.log.some(e => e.text === 'Bildin'));
});

test('~ @21:10 en az 1sa: yerel saatle bir sonraki 21:10', () => {
  assert.equal(new Date(nextClock(new Date(2026, 10, 2, 21, 30).getTime(), 21, 10)).getDate(), 3);
  const st = newState(T0);
  advance(story, st, T0 + 3_600_000);
  choose(story, st, 0, T0 + 3_600_000);
  advance(story, st, T0 + 3_700_000);
  answer(story, st, 'degirmen', T0 + 3_700_000, normalize);
  const up = upcoming(story, st, T0 + 3_700_000);
  const aksam = up.items.find(e => e.text === 'Akşam oldu');
  const d = new Date(aksam.at);
  assert.equal(d.getHours(), 21);
  assert.equal(d.getMinutes(), 10);
  assert.equal(up.final, 'ended');
  assert.equal(st.ended, null, 'upcoming asıl durumu değiştirmez');
});

test('beklemeyi atla ve geri sar', () => {
  const st = newState(T0);
  advance(story, st, T0 + 60_000);
  assert.ok(skipWait(story, st, T0 + 60_000));
  advance(story, st, T0 + 70_000);
  assert.equal(st.waiting.type, 'choice');
  choose(story, st, 1, T0 + 70_000);
  advance(story, st, T0 + 90_000);
  assert.ok(st.log.some(e => e.text === 'Üzüldüm'));
  assert.ok(rewind(st, T0 + 95_000));
  assert.equal(st.waiting.type, 'choice');
  assert.ok(!st.log.some(e => e.text === 'Üzüldüm'));
});

test('hız çarpanı beklemeleri kısaltır', () => {
  const st = newState(T0);
  advance(story, st, T0 + 20_000, { scale: 60 });
  assert.ok(st.log.some(e => e.text === 'İkinci'));
});

test('normalize', () => {
  assert.equal(normalize('  Değirmen, ŞİMDİ! '), 'degirmen simdi');
});

test('hatalı senaryo yakalanır', () => {
  const bad = parse('=== basla\n* Seç -> yok\n~ 5 dakika\n!uç', 'bad');
  const errs = validate(bad);
  assert.ok(errs.some(e => e.includes('"yok"')));
  assert.ok(errs.some(e => e.includes('geçersiz bekleme')));
  assert.ok(errs.some(e => e.includes('bilinmeyen komut')));
});

test('bildirim: yalnızca sessizlikten sonra gelen ilk mesaj', () => {
  const list = pickNotifications([
    { kind: 'msg', from: 'Elif', text: 'a', at: 1_000 },
    { kind: 'msg', from: 'Elif', text: 'b', at: 5_000 },
    { kind: 'msg', from: 'Elif', text: 'c', at: 600_000 },
    { kind: 'photo', from: 'Elif', at: 700_000 },
    { kind: 'msg', from: 'Nazlı', text: 'd', at: 701_000 },
  ], 0, 'Elif');
  assert.deepEqual(list.map(x => x.body), ['c', '📷 Fotoğraf']);
});

console.log(`\n${n} test geçti`);
