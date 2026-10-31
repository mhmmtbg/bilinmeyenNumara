// Ece'nin gönderdiği "fotoğraflar". Düz renkli, temadan bağımsız SVG çizimler (400×300).

const hand = (cx, cy, deg, len, w, c) => {
  const a = (deg - 90) * Math.PI / 180;
  return `<line x1="${cx}" y1="${cy}" x2="${(cx + Math.cos(a) * len).toFixed(1)}" y2="${(cy + Math.sin(a) * len).toFixed(1)}" stroke="${c}" stroke-width="${w}" stroke-linecap="round"/>`;
};

const PHOTOS = {
  defter: () => `
<svg viewBox="0 0 400 300" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Defterin son sayfası: el yazısı bir not ve bir telefon numarası">
  <rect width="400" height="300" fill="#3A3129"/>
  <g transform="rotate(-4 200 150)">
    <rect x="58" y="22" width="292" height="268" fill="#E8DFC9"/>
    <rect x="58" y="22" width="292" height="268" fill="none" stroke="#C9BC9E"/>
    ${Array.from({ length: 10 }, (_, i) => `<line x1="58" x2="350" y1="${62 + i * 23}" y2="${62 + i * 23}" stroke="#A9BBC9" stroke-width="1"/>`).join('')}
    <line x1="90" x2="90" y1="22" y2="290" stroke="#D99A8E" stroke-width="1.2"/>
    <g font-family="Georgia, 'Noto Serif', serif" font-style="italic" fill="#2C3A57" font-size="17">
      <text x="98" y="80">Ilgındere'de başın sıkışırsa</text>
      <text x="98" y="103">bu numaraya yaz. O bilir.</text>
      <text x="104" y="150" font-size="24" letter-spacing="3" font-style="normal">05</text>
      <text x="98" y="218" font-size="16">Saat dokuzu geçe.</text>
    </g>
    <path d="M140 140 q14 -10 26 2 t28 -4 t30 4 t26 -6 t30 6" fill="none" stroke="#2C3A57" stroke-width="2.2" stroke-linecap="round" opacity=".85"/>
    <path d="M138 133 c30 -22 120 -18 156 6 c20 14 8 30 -24 30 c-40 2 -100 4 -124 -8 c-18 -9 -20 -20 -8 -28z" fill="#6F8197" opacity=".28"/>
    <path d="M150 146 c24 -12 90 -10 118 2" fill="none" stroke="#6F8197" stroke-width="5" opacity=".25" stroke-linecap="round"/>
    <line x1="98" x2="236" y1="224" y2="222" stroke="#2C3A57" stroke-width="1.4"/>
    <text x="300" y="270" font-family="Georgia, serif" font-style="italic" fill="#7A6E58" font-size="12">— K.</text>
  </g>
</svg>`,

  kule: () => `
<svg viewBox="0 0 400 300" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Taş saat kulesi; saat dokuzu on geçe durmuş, tepede bir çan">
  <rect width="400" height="300" fill="#8796A1"/>
  <rect y="170" width="400" height="130" fill="#6B7A70"/>
  <path d="M0 176 L60 150 L120 168 L190 140 L260 162 L330 138 L400 158 V180 H0z" fill="#5D6E77"/>
  <g fill="#B9AC97">
    <rect x="20" y="186" width="74" height="60"/><path d="M14 188 L57 160 L100 188z" fill="#8A5E4B"/>
    <rect x="300" y="190" width="84" height="56"/><path d="M294 192 L342 164 L390 192z" fill="#8A5E4B"/>
  </g>
  <rect x="44" y="210" width="20" height="36" fill="#4B5A63"/>
  <path d="M47 214 l14 28 M61 214 l-14 28" stroke="#C0392B" stroke-width="3"/>
  <rect x="324" y="206" width="22" height="22" fill="#4B5A63"/>
  <path d="M327 209 l16 16 M343 209 l-16 16" stroke="#C0392B" stroke-width="3"/>
  <rect x="150" y="70" width="100" height="186" fill="#A99E8B"/>
  ${Array.from({ length: 11 }, (_, i) => `<line x1="150" x2="250" y1="${86 + i * 16}" y2="${86 + i * 16}" stroke="#8E8471" stroke-width="1"/>`).join('')}
  ${Array.from({ length: 12 }, (_, i) => `<line x1="${i % 2 ? 175 : 200}" x2="${i % 2 ? 175 : 200}" y1="${70 + i * 16}" y2="${86 + i * 16}" stroke="#8E8471" stroke-width="1"/>`).join('')}
  <rect x="142" y="20" width="116" height="52" fill="#9A8F7C"/>
  <path d="M136 24 L200 0 L264 24z" fill="#6D4C3D"/>
  <path d="M160 70 V44 a12 12 0 0 1 24 0 V70z M216 70 V44 a12 12 0 0 1 24 0 V70z" fill="#4A4E50"/>
  <path d="M190 34 q10 -6 20 0 l3 22 h-26z" fill="#A87B3C"/>
  <circle cx="200" cy="58" r="3.5" fill="#A87B3C"/>
  <circle cx="200" cy="122" r="30" fill="#EFE9DC" stroke="#6D4C3D" stroke-width="4"/>
  ${Array.from({ length: 12 }, (_, i) => { const a = i * 30 * Math.PI / 180; return `<line x1="${(200 + Math.sin(a) * 24).toFixed(1)}" y1="${(122 - Math.cos(a) * 24).toFixed(1)}" x2="${(200 + Math.sin(a) * 27).toFixed(1)}" y2="${(122 - Math.cos(a) * 27).toFixed(1)}" stroke="#3B3B3B" stroke-width="2"/>`; }).join('')}
  ${hand(200, 122, (9 + 10 / 60) * 30, 15, 3.5, '#222')}
  ${hand(200, 122, 60, 22, 2.4, '#222')}
  <circle cx="200" cy="122" r="2.5" fill="#222"/>
  <rect x="186" y="214" width="28" height="42" fill="#5A4636"/>
  <rect x="186" y="230" width="28" height="4" fill="#7A7A7A"/>
  <rect x="196" y="234" width="8" height="10" fill="#8A6B3A"/>
</svg>`,

  duvar: () => `
<svg viewBox="0 0 400 300" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Kapı kasasında kurşun kalemle çizilmiş boy çizgileri: Kemal 1971, Nazlı 1973 ve diğerleri">
  <rect width="400" height="300" fill="#CFC6B4"/>
  <rect x="0" y="0" width="130" height="300" fill="#3F3A33"/>
  <rect x="130" y="0" width="56" height="300" fill="#9C7D5C"/>
  <line x1="186" y1="0" x2="186" y2="300" stroke="#7E6347" stroke-width="2"/>
  <rect x="186" y="0" width="214" height="300" fill="#D8D0BE"/>
  <path d="M260 40 c20 10 50 6 70 22 M300 210 c26 -6 50 10 70 4" stroke="#C3B9A3" stroke-width="10" fill="none" opacity=".6" stroke-linecap="round"/>
  <g stroke="#55504A" stroke-width="1.6" stroke-linecap="round">
    <line x1="134" x2="182" y1="250" y2="250"/>
    <line x1="134" x2="182" y1="222" y2="221"/>
    <line x1="134" x2="182" y1="196" y2="197"/>
    <line x1="134" x2="182" y1="172" y2="171"/>
    <line x1="134" x2="182" y1="146" y2="146"/>
    <line x1="134" x2="182" y1="124" y2="125"/>
  </g>
  <g font-family="Georgia, 'Noto Serif', serif" font-style="italic" font-size="12.5" fill="#3E3934">
    <text x="192" y="254">Kemal 1971</text>
    <text x="192" y="225">Nazlı 1973</text>
    <text x="192" y="200">Kemal 1974</text>
    <text x="192" y="175">Nazlı 1976</text>
    <text x="192" y="150">Kemal 1978</text>
    <text x="192" y="128">Nazlı 1981</text>
  </g>
  <rect x="104" y="150" width="14" height="8" rx="2" fill="#8C8C8C"/>
</svg>`,
};

export function photoSvg(key) {
  const f = PHOTOS[key];
  if (f) return f();
  return `<svg viewBox="0 0 400 300" xmlns="http://www.w3.org/2000/svg"><rect width="400" height="300" fill="#2A3238"/><text x="200" y="155" fill="#8494A0" font-family="sans-serif" font-size="16" text-anchor="middle">Fotoğraf yüklenemedi</text></svg>`;
}
