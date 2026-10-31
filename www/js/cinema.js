// Sinematik oynatıcı: tam ekran, kareler arası yavaş kaydırma/yakınlaşma, altyazı ve ses bandı.
// Zamanlama ses bandının currentTime'ından gelir (ses yoksa saatten).

const $ = id => document.getElementById(id);
let DATA = {};
let active = null;

export function setCinemaData(d) { DATA = d || {}; }
export const cinemaInfo = key => DATA[key];

function build() {
  const root = $('cinema');
  root.innerHTML = `
    <div class="cine-stage" id="cineStage"></div>
    <div class="cine-cap" id="cineCap" aria-live="polite"></div>
    <div class="cine-bar"><span class="cine-prog"><i id="cineProg"></i></span></div>
    <button class="cine-skip" id="cineSkip">Geç</button>
    <div class="cine-ready" id="cineReady" hidden>
      <span class="cine-ready-title" id="cineReadyTitle"></span>
      <button class="cine-play" id="cinePlay" aria-label="Oynat"><svg class="ic"><use href="#i-play"/></svg></button>
      <button class="cine-later" id="cineLater">Şimdi değil</button>
    </div>`;
}

/**
 * Sahneyi oynatır. autoplay=false ise önce "Oynat" düğmesi gösterilir (tarayıcı ses için dokunuş ister).
 * Bitince ya da geçilince onDone() çağrılır.
 */
export function playCinema(key, { autoplay = true, onDone = () => {} } = {}) {
  const sc = DATA[key];
  if (!sc) { onDone(); return; }
  stopCinema(false);
  build();
  const root = $('cinema');
  root.hidden = false;
  document.body.classList.add('cine-on');

  const stage = $('cineStage');
  const frames = sc.kareler.map(f => {
    const el = document.createElement('div');
    el.className = 'cine-frame';
    if (f.img) {
      const im = new Image();
      im.src = f.img;
      im.alt = '';
      im.decoding = 'async';
      el.append(im);
    }
    stage.append(el);
    return { ...f, el, img: el.querySelector('img') };
  });
  let t0 = 0;
  for (const f of frames) { f.t0 = t0; t0 += f.sure; }
  const total = t0;

  const audio = new Audio(sc.ses);
  audio.preload = 'auto';
  const st = active = { key, audio, raf: 0, start: 0, onDone, frames, total, shown: -1, cap: '' };

  const now = () => (audio.readyState >= 2 && !audio.paused && audio.currentTime > 0)
    ? audio.currentTime : (performance.now() - st.start) / 1000;

  function render() {
    if (active !== st) return;
    const t = now();
    if (t >= total) { finish(); return; }
    let idx = frames.findIndex(f => t >= f.t0 && t < f.t0 + f.sure);
    if (idx < 0) idx = frames.length - 1;
    const f = frames[idx];
    if (idx !== st.shown) {
      frames.forEach((g, i) => g.el.classList.toggle('on', i === idx));
      st.shown = idx;
    }
    // yavaş kaydırma ve yakınlaşma (Ken Burns)
    const p = Math.min(1, (t - f.t0) / f.sure);
    const e = p * p * (3 - 2 * p) * 0.6 + p * 0.4;
    if (f.img) {
      const x = f.bas[0] + (f.son[0] - f.bas[0]) * e;
      const s = f.bas[1] + (f.son[1] - f.bas[1]) * e;
      f.img.style.objectPosition = `${(x * 100).toFixed(2)}% 50%`;
      f.img.style.transform = `scale(${s.toFixed(4)})`;
    }
    // altyazı
    const lt = t - f.t0;
    const cap = f.yazi.find(c => lt >= c.bas && lt < c.son);
    const text = cap ? cap.metin : '';
    if (text !== st.cap) {
      const el = $('cineCap');
      el.classList.remove('on');
      st.cap = text;
      if (text) { el.textContent = text; void el.offsetWidth; el.classList.add('on'); }
    }
    $('cineProg').style.width = `${(t / total * 100).toFixed(2)}%`;
    st.raf = requestAnimationFrame(render);
  }

  function begin() {
    $('cineReady').hidden = true;
    st.start = performance.now();
    audio.play().catch(() => {});
    st.raf = requestAnimationFrame(render);
  }
  function finish() { stopCinema(true); }

  $('cineSkip').addEventListener('click', finish);
  $('cinePlay').addEventListener('click', begin);
  $('cineLater').addEventListener('click', finish);

  if (autoplay) {
    begin();
  } else {
    frames[0].el.classList.add('on');
    if (frames[0].img) frames[0].img.style.objectPosition = `${frames[0].bas[0] * 100}% 50%`;
    $('cineReadyTitle').textContent = sc.baslik;
    $('cineReady').hidden = false;
  }
}

export function stopCinema(callDone = true) {
  const st = active;
  if (!st) return;
  active = null;
  cancelAnimationFrame(st.raf);
  st.audio.pause();
  const root = $('cinema');
  root.hidden = true;
  root.innerHTML = '';
  document.body.classList.remove('cine-on');
  if (callDone) st.onDone();
}

export const cinemaPlaying = () => !!active;
