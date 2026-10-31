// Ses kaydı baloncukları için tek bir oynatıcı: aynı anda tek kayıt çalar.

let current = null;   // { audio, bubble, raf }

function fmt(s) {
  s = Math.max(0, Math.round(s));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
}

function paint(bubble, audio, total) {
  const bars = bubble.querySelectorAll('.wave i');
  const p = audio ? audio.currentTime / (audio.duration || total) : 0;
  const lit = Math.round(p * bars.length);
  bars.forEach((b, i) => b.classList.toggle('on', i < lit));
  bubble.querySelector('.voice-len').textContent = audio && !audio.paused ? fmt(audio.currentTime) : fmt(total);
}

export function stopVoice() {
  if (!current) return;
  const { audio, bubble, raf, total } = current;
  cancelAnimationFrame(raf);
  audio.pause();
  bubble.classList.remove('playing');
  bubble.querySelector('.play use').setAttribute('href', '#i-play');
  paint(bubble, null, total);
  current = null;
}

export function toggleVoice(bubble, src, total) {
  if (current && current.bubble === bubble) { stopVoice(); return; }
  stopVoice();
  const audio = new Audio(src);
  const c = current = { audio, bubble, raf: 0, total };
  bubble.classList.add('playing');
  bubble.querySelector('.play use').setAttribute('href', '#i-pause');
  const loop = () => { paint(bubble, audio, total); c.raf = requestAnimationFrame(loop); };
  audio.addEventListener('ended', () => { if (current === c) stopVoice(); });
  audio.addEventListener('error', () => {
    if (current === c) stopVoice();
    bubble.querySelector('.voice-len').textContent = 'açılamadı';
  });
  audio.play().then(loop).catch(() => { if (current === c) stopVoice(); });
}

export { fmt as fmtDuration };
