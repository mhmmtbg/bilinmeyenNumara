"""Prosedürel görüntü araçları: gürültü, maske, doku, ışık ve "telefon fotoğrafı" sonrası işleme.
Görüntüler [Y, X, 3] float32 dizileridir (0..1, doğrusal değil, sRGB benzeri)."""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage

FONTS = Path(__file__).resolve().parent / 'fonts'


def rng(seed):
    return np.random.default_rng(seed)


# ---------------------------------------------------------------- gürültü
_FBM = {}


def fbm(h, w, scale=64, octaves=5, seed=0, persistence=0.5, aspect=(1.0, 1.0)):
    """Fraktal gürültü (0..1), önbellekli. scale: en kaba katmanın piksel ölçeği. aspect: (y, x) gerilme."""
    key = (h, w, scale, octaves, seed, persistence, tuple(aspect))
    if key not in _FBM:
        _FBM[key] = _fbm(h, w, scale, octaves, seed, persistence, aspect)
    return _FBM[key]


def _fbm(h, w, scale, octaves, seed, persistence, aspect):
    r = rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, total = 1.0, 0.0
    s = scale
    for _ in range(octaves):
        gy = max(2, int(h / (s * aspect[0])) + 3)
        gx = max(2, int(w / (s * aspect[1])) + 3)
        g = r.random((gy, gx)).astype(np.float32)
        z = ndimage.zoom(g, (h / (gy - 2) * 1.0, w / (gx - 2) * 1.0), order=3, mode='reflect')
        out += z[:h, :w] * amp
        total += amp
        amp *= persistence
        s /= 2
        if s < 1:
            break
    out /= total
    out -= out.min()
    return out / (out.max() + 1e-9)


def ridge1d(w, scale=300, octaves=6, seed=0, rough=0.5):
    """Tek boyutlu fraktal çizgi (0..1): dağ sırtları için."""
    r = rng(seed)
    x = np.zeros(w)
    amp, s_ = 1.0, float(scale)
    for _ in range(octaves):
        n = int(w / s_) + 4
        z = ndimage.zoom(r.random(n), w / (n - 3), order=3)
        x += z[:w] * amp
        amp *= rough
        s_ /= 2
        if s_ < 2:
            break
    x -= x.min()
    return x / (x.max() + 1e-9)


# ---------------------------------------------------------------- maske ve çizim
def mask_poly(h, w, pts, ss=3, blur=0.0):
    """Kenar yumuşatmalı çokgen maskesi (yalnızca çokgenin kutusu çizilir)."""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    pad = int(blur * 3) + 3
    x0, y0 = max(0, int(min(xs)) - pad), max(0, int(min(ys)) - pad)
    x1, y1 = min(w, int(max(xs)) + pad + 1), min(h, int(max(ys)) + pad + 1)
    m = np.zeros((h, w), np.float32)
    if x1 <= x0 or y1 <= y0:
        return m
    bw, bh = x1 - x0, y1 - y0
    im = Image.new('L', (bw * ss, bh * ss), 0)
    ImageDraw.Draw(im).polygon([((x - x0) * ss, (y - y0) * ss) for x, y in pts], fill=255)
    im = im.resize((bw, bh), Image.LANCZOS)
    sub = np.asarray(im, np.float32) / 255
    m[y0:y1, x0:x1] = ndimage.gaussian_filter(sub, blur) if blur else sub
    return m


def mask_ellipse(h, w, cx, cy, rx, ry, blur=0.0, ring=0.0):
    """Elips (ya da ring>0 ise halka) maskesi, yalnızca kutusunda çizilir."""
    pad = int(blur * 3) + 3
    x0, y0 = max(0, int(cx - rx) - pad), max(0, int(cy - ry) - pad)
    x1, y1 = min(w, int(cx + rx) + pad + 1), min(h, int(cy + ry) + pad + 1)
    m = np.zeros((h, w), np.float32)
    if x1 <= x0 or y1 <= y0:
        return m
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    d = np.sqrt(((xx - cx) / max(rx, 1e-3)) ** 2 + ((yy - cy) / max(ry, 1e-3)) ** 2)
    edge = 1.5 / max(min(rx, ry), 1)
    sub = np.clip((1 - d) / edge + 0.5, 0, 1)
    if ring:
        sub = sub * np.clip((d - (1 - ring / max(min(rx, ry), 1))) / edge + 0.5, 0, 1)
    m[y0:y1, x0:x1] = ndimage.gaussian_filter(sub, blur) if blur else sub
    return m


def mask_draw(h, w, fn, ss=3, blur=0.0):
    """fn(draw, ss) ile serbest çizim maskesi."""
    im = Image.new('L', (w * ss, h * ss), 0)
    fn(ImageDraw.Draw(im), ss)
    im = im.resize((w, h), Image.LANCZOS)
    m = np.asarray(im, np.float32) / 255
    return ndimage.gaussian_filter(m, blur) if blur else m


def mask_text(h, w, text, xy, font, size, ss=2, angle=0.0, spacing=1.0):
    f = ImageFont.truetype(str(FONTS / font), size * ss)
    im = Image.new('L', (w * ss, h * ss), 0)
    d = ImageDraw.Draw(im)
    x, y = xy
    d.text((x * ss, y * ss), text, font=f, fill=255)
    if angle:
        im = im.rotate(angle, resample=Image.BICUBIC, center=(x * ss, y * ss))
    im = im.resize((w, h), Image.LANCZOS)
    return np.asarray(im, np.float32) / 255


def comp(img, color, mask):
    """img üstüne renk/doku bindir (mask 0..1)."""
    m = mask[..., None]
    c = np.asarray(color, np.float32)
    if c.ndim == 1:
        c = c[None, None, :]
    img *= (1 - m)
    img += c * m
    return img


def solid(h, w, color):
    return np.ones((h, w, 3), np.float32) * np.asarray(color, np.float32)


def vgrad(h, w, stops):
    """Dikey renk geçişi: stops = [(0..1, renk), ...]"""
    ys = np.linspace(0, 1, h)
    out = np.zeros((h, 3), np.float32)
    pos = [p for p, _ in stops]
    for c in range(3):
        out[:, c] = np.interp(ys, pos, [col[c] for _, col in stops])
    return np.repeat(out[:, None, :], w, 1)


def tint(tex, dark, light):
    """Gri dokuyu iki renk arasında boya."""
    d = np.asarray(dark, np.float32)
    l = np.asarray(light, np.float32)
    return d + (l - d) * tex[..., None]


# ---------------------------------------------------------------- dokular
def wood(h, w, seed=0, vertical=False, base=(0.36, 0.22, 0.13), light=(0.58, 0.40, 0.25)):
    """Ahşap: uzun lif çizgileri, kıvrılan halkalar, budak; yatay (vertical=True ise dikey)."""
    if vertical:
        return np.transpose(wood(w, h, seed, False, base, light), (1, 0, 2))
    r = rng(seed)
    warp = fbm(h, w, 260, 3, seed + 1) * 30 + fbm(h, w, 60, 2, seed + 4) * 4
    yy = np.arange(h, dtype=np.float32)[:, None] + warp
    rings = 0.5 + 0.5 * np.sin(yy * 0.09 + fbm(h, w, 200, 3, seed + 2) * 14)
    fiber = fbm(h, w, 260, 6, seed, persistence=0.55, aspect=(0.012, 1.0))
    fine = fbm(h, w, 40, 3, seed + 3, aspect=(0.05, 1.0))
    t = np.clip(0.28 * rings ** 2 + 0.52 * fiber + 0.2 * fine, 0, 1)
    img = tint(t, base, light)
    # budak
    for _ in range(2):
        cx, cy = r.uniform(0, w), r.uniform(0, h)
        k = radial(h, w, cx, cy, r.uniform(14, 26), r.uniform(8, 14), 1.5)
        img *= (1 - 0.45 * k)[..., None]
    img *= (0.93 + 0.1 * fbm(h, w, 8, 2, seed + 7))[..., None]
    return img


def stone_blocks(h, w, bw=46, bh=24, seed=0, base=(0.62, 0.56, 0.47), jitter=0.12, mortar=(0.48, 0.44, 0.38)):
    r = rng(seed)
    img = np.zeros((h, w, 3), np.float32)
    mortar_m = np.zeros((h, w), np.float32)
    rows = h // bh + 2
    for row in range(rows):
        y0 = row * bh
        off = (row % 2) * bw // 2 + r.integers(-6, 6)
        x = -off
        while x < w:
            bwi = int(bw * r.uniform(0.7, 1.35))
            c = np.asarray(base) * r.uniform(1 - jitter, 1 + jitter) + r.normal(0, 0.015, 3)
            ys, ye = max(0, y0), min(h, y0 + bh)
            xs, xe = max(0, x), min(w, x + bwi)
            if ye > ys and xe > xs:
                img[ys:ye, xs:xe] = c
                mortar_m[ys:min(h, ys + 2), xs:xe] = 1
                mortar_m[ys:ye, xs:min(w, xs + 2)] = 1
            x += bwi
    tex = fbm(h, w, 10, 4, seed + 5)
    img *= (0.82 + 0.3 * tex)[..., None]
    pits = (fbm(h, w, 3, 2, seed + 6) > 0.8).astype(np.float32)
    img *= (1 - 0.18 * pits)[..., None]
    mm = ndimage.gaussian_filter(mortar_m, 0.7)
    img = img * (1 - mm[..., None]) + np.asarray(mortar) * mm[..., None]
    return img


def plaster(h, w, seed=0, base=(0.86, 0.83, 0.76)):
    t = fbm(h, w, 120, 6, seed)
    stains = np.clip((fbm(h, w, 220, 4, seed + 1) - 0.55) * 3, 0, 1)
    img = tint(t, np.asarray(base) * 0.88, base)
    img *= (1 - 0.18 * stains)[..., None]
    img[..., 2] *= (1 - 0.06 * stains)
    return img


def crack_lines(h, w, n, seed=0, length=180):
    r = rng(seed)

    def fn(d, ss):
        for _ in range(n):
            x, y = r.uniform(0, w), r.uniform(0, h)
            a = r.uniform(0, np.pi * 2)
            pts = [(x, y)]
            for _ in range(int(length / 6)):
                a += r.normal(0, 0.45)
                x += np.cos(a) * 6
                y += np.sin(a) * 6
                pts.append((x, y))
            d.line([(px * ss, py * ss) for px, py in pts], fill=255, width=max(1, int(ss * r.uniform(0.6, 1.3))))
    return mask_draw(h, w, fn)


# ---------------------------------------------------------------- ışık ve sonrası
def radial(h, w, cx, cy, rx, ry=None, power=2.0):
    ry = ry or rx
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
    return np.clip(1 - d, 0, 1) ** power


def light(img, gain_map, color=(1, 1, 1)):
    return img * (gain_map[..., None] * np.asarray(color, np.float32))


def glow(img, cx, cy, r, color, strength=1.0):
    g = radial(img.shape[0], img.shape[1], cx, cy, r, r, 2.2) * strength
    return img + g[..., None] * np.asarray(color, np.float32)


def blur(img, s):
    return np.stack([ndimage.gaussian_filter(img[..., c], s) for c in range(3)], -1) if s > 0 else img


def depth_blur(img, mask, s):
    """mask=1 olan yerler bulanıklaşır (alan derinliği)."""
    b = blur(img, s)
    return img * (1 - mask[..., None]) + b * mask[..., None]


def phone_photo(img, seed=0, grain=0.03, vignette=0.35, warm=0.0, contrast=1.06, sharpen=0.5, noise_dark=1.0, soft=0.6):
    """Telefon kamerası hissi: lens yumuşaklığı, keskinleştirme, gölgede gürültü, kenar kararması, ton eğrisi."""
    h, w, _ = img.shape
    r = rng(seed)
    img = np.clip(img, 0, None)
    if soft:
        img = blur(img, soft)
    if sharpen:
        b = blur(img, 1.6)
        img = img + (img - b) * sharpen
    # ton eğrisi (filmik)
    # yalnızca parlak bölgeleri yumuşakça sıkıştır; karanlıklar karanlık kalır
    k = 0.72
    img = np.where(img < k, img, k + (img - k) / (1 + (img - k) / (1 - k)))
    mid = img.mean()
    img = (img - mid) * contrast + mid
    if warm:
        img[..., 0] *= 1 + warm
        img[..., 2] *= 1 - warm
    v = radial(h, w, w / 2, h / 2, w * 0.78, h * 0.78, 1.0)
    img *= (1 - vignette) + vignette * v[..., None] ** 0.8
    lum = img.mean(-1, keepdims=True)
    n = r.normal(0, 1, (h, w, 1)).astype(np.float32)
    nc = r.normal(0, 1, (h, w, 3)).astype(np.float32) * 0.35
    amount = grain * (1 + noise_dark * (1 - np.clip(lum, 0, 1)) * 1.5)
    img = img + (n + nc) * amount
    return np.clip(img, 0, 1)


def save_jpg(img, path, q=84, size=None):
    im = Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))
    if size:
        im = im.resize(size, Image.LANCZOS)
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, 'JPEG', quality=q, optimize=True, progressive=True, subsampling=1)
    return im


def to_pil(img):
    return Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))


def from_pil(im):
    return np.asarray(im.convert('RGB'), np.float32) / 255


def perspective_coeffs(src, dst):
    """PIL PERSPECTIVE dönüşümü için katsayılar (dst → src)."""
    A, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()


def warp_rgba(layer_rgba, size, dst_quad):
    """RGBA katmanı (PIL) hedef dörtgene yerleştir."""
    w0, h0 = layer_rgba.size
    src = [(0, 0), (w0, 0), (w0, h0), (0, h0)]
    co = perspective_coeffs(src, dst_quad)
    return layer_rgba.transform(size, Image.PERSPECTIVE, co, Image.BICUBIC)
