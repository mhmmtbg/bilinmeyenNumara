"""Sinematik sahnelerin panoramik kareleri (2400×1350) ve sahne tanımları.
Çıktı: www/sinema/<kare>.jpg ve www/sinema/sinema.json
Kullanım: python3 tools/assets/cinema.py [kare_adı ...]"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

from gfx import (blur, comp, mask_ellipse, depth_blur, fbm, from_pil, glow, light, mask_draw, mask_poly, phone_photo, radial,
                 ridge1d, rng, save_jpg, stone_blocks, tint, to_pil, vgrad, warp_rgba, wood)
from photos import mudbrick_house, sky_dusk, tower_layer, utility_pole

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'www/sinema'
W, H = 2400, 1350


# ---------------------------------------------------------------- ortak parçalar
def mountains(img, layers, seed=0):
    for i, (base, amp, col, scale, haze) in enumerate(layers):
        rid = ridge1d(W, scale, 8, seed + i * 7, 0.52)
        ys = base - rid * amp
        m = ndimage.gaussian_filter((np.arange(H)[:, None] > ys[None, :]).astype(np.float32), 1.0)
        tex = tint(fbm(H, W, 60, 6, seed + 30 + i), np.asarray(col) * 0.78, col)
        # yamaçlarda ışık/gölge: sırt eğimi
        slope = ndimage.gaussian_filter1d(np.gradient(ys), 25)
        shade = np.clip(0.92 + slope[None, :] * 0.05, 0.75, 1.1)
        tex = tex * shade[..., None]
        img = img * (1 - m[..., None]) + tex * m[..., None]
        if haze:
            hz = np.clip(1 - (np.arange(H)[:, None] - ys[None, :]) / 220, 0, 1) * m * haze
            img = img * (1 - hz[..., None]) + np.array(layers[0][2]) * 1.2 * hz[..., None]
    return img


def poplar(img, x, y_base, height, width, col=(0.13, 0.15, 0.10), seed=0, lightc=None):
    r = rng(seed)
    pts = []
    for t in np.linspace(0, 1, 30):
        wv = width * (np.sin(np.pi * (t ** 0.8)) * (1 - t * 0.35)) * (0.85 + 0.3 * r.random())
        pts.append((x - wv / 2, y_base - t * height))
    for t in np.linspace(1, 0, 30):
        wv = width * (np.sin(np.pi * (t ** 0.8)) * (1 - t * 0.35)) * (0.85 + 0.3 * r.random())
        pts.append((x + wv / 2, y_base - t * height))
    m = mask_poly(H, W, pts)
    leaf = fbm(H, W, 6, 3, 1 + seed % 3)
    m *= np.clip(leaf * 1.6, 0, 1) * 0.5 + 0.5
    c = np.asarray(col, np.float32)
    tex = c[None, None, :] * (0.7 + 0.6 * leaf[..., None])
    if lightc is not None:
        side = np.clip((np.arange(W)[None, :] - x) / (width / 2), -1, 1)
        tex = tex * (1 + 0.35 * side[..., None] * np.asarray(lightc))
    return img * (1 - m[..., None]) + tex * m[..., None]


def water(img, y0, y1, reflect_src=None, ripple=6, tint_col=(0.35, 0.40, 0.42), mix=0.55, seed=0, mask=None):
    """y0..y1 arası yatay su; üstteki görüntüyü ters yansıtır."""
    h = y1 - y0
    src = img[max(0, y0 - h):y0][::-1] if reflect_src is None else reflect_src
    src = src[:h]
    if src.shape[0] < h:
        src = np.pad(src, ((0, h - src.shape[0]), (0, 0), (0, 0)), mode='edge')
    rip = fbm(h, W, 30, 4, seed, aspect=(0.08, 1.0))
    dx = ((rip - 0.5) * ripple).astype(np.int32)
    xs = np.clip(np.arange(W)[None, :] + dx, 0, W - 1)
    refl = src[np.arange(h)[:, None], xs]
    refl = blur(refl, 2.6)
    out = refl * (1 - mix) + np.asarray(tint_col) * mix
    streak = np.clip((fbm(h, W, 14, 3, seed + 1, aspect=(0.05, 1.0)) - 0.6) * 3, 0, 1)
    out = out * (1 + 0.25 * streak[..., None])
    m = np.ones((h, W), np.float32) if mask is None else mask[y0:y1]
    img[y0:y1] = img[y0:y1] * (1 - m[..., None]) + out * m[..., None]
    return img


def mist(img, y, thick, strength, col=(0.85, 0.83, 0.80), seed=0):
    n = fbm(H, W, 180, 4, seed, aspect=(0.3, 1.0))
    band = np.exp(-((np.arange(H)[:, None] - y) / thick) ** 2) * (0.5 + 0.8 * n)
    m = np.clip(band * strength, 0, 1)
    return img * (1 - m[..., None]) + np.asarray(col) * m[..., None]


def fields(img, y0, seed=0, cols=((0.42, 0.40, 0.24), (0.50, 0.44, 0.28), (0.34, 0.36, 0.20), (0.56, 0.50, 0.34))):
    r = rng(seed)
    h = H - y0
    reg = fbm(h, W, 120, 2, seed, aspect=(0.25, 1.0))
    q = np.floor(reg * len(cols) * 1.999).astype(int) % len(cols)
    base = np.asarray(cols, np.float32)[q]
    furrow = 0.5 + 0.5 * np.sin(np.arange(W)[None, :] * 0.25 + np.arange(h)[:, None] * 0.8 + reg * 20)
    tex = base * (0.86 + 0.14 * furrow[..., None]) * (0.85 + 0.3 * fbm(h, W, 10, 3, seed + 1))[..., None]
    img[y0:] = tex
    return img


def cluster_houses(img, items, dim=1.0):
    for (x0, y0, ww, hh, sd, xm) in items:
        house = mudbrick_house(ww, hh, sd, x_mark=xm) * dim
        ys, ye = max(0, y0), min(H, y0 + hh)
        xs, xe = max(0, x0), min(W, x0 + ww)
        if ye > ys and xe > xs:
            img[ys:ye, xs:xe] = house[ys - y0:ye - y0, xs - x0:xe - x0]
    return img


def put_tower(img, quad, dim=1.0, warm_top=0.0):
    tw, th = 300, 760
    t_img, t_a = tower_layer(tw, th, 2)
    if warm_top:
        lit = np.clip(1 + warm_top - np.linspace(0, 1, th) * (warm_top + 0.5), 0.4, 1.4)[:, None]
        t_img = t_img * lit[..., None] * np.array([1.0, 0.88, 0.75])
    t_img = t_img * dim
    layer = Image.fromarray((np.dstack([np.clip(t_img, 0, 1), t_a]) * 255).astype(np.uint8), 'RGBA')
    canvas = to_pil(img).convert('RGBA')
    canvas.alpha_composite(warp_rgba(layer, (W, H), quad))
    return from_pil(canvas)


def stars(img, n, seed=0, max_y=0.6):
    r = rng(seed)
    m = np.zeros((H, W), np.float32)
    ys = (r.random(n) ** 1.4 * H * max_y).astype(int)
    xs = r.integers(0, W, n)
    m[ys, xs] = r.random(n) ** 3 * 1.6
    m = ndimage.gaussian_filter(m, 0.7) * 4
    return img + np.clip(m, 0, 1)[..., None] * np.array([0.9, 0.92, 1.0])


def plane_uv(y0, horizon, depth=160.0):
    """Yer düzlemi koordinatları (u yatay, v derinlik) y0..H satırları için."""
    ys = np.arange(y0, H, dtype=np.float32)
    z = depth / np.maximum(ys - horizon, 1.0)
    u = (np.arange(W, dtype=np.float32) - W / 2)[None, :] * z[:, None]
    v = z[:, None] * W * 0.5 * np.ones((1, W), np.float32)
    return u, v


def plane(tile, y0, horizon, depth=160.0, xscale=1.0, shift=(0.0, 0.0)):
    """Yer düzlemi dokusu: tile (kare gürültü) perspektifle y0..H aralığına yayılır."""
    from scipy.ndimage import map_coordinates
    n = tile.shape[0]
    ys = np.arange(y0, H, dtype=np.float32)
    z = depth / np.maximum(ys - horizon, 1.0)
    xs = (np.arange(W, dtype=np.float32) - W / 2)
    u = (xs[None, :] * z[:, None] * xscale + shift[0] + n / 2) % n
    v = (z[:, None] * W * 0.5 + shift[1]) * np.ones((1, W)) % n
    return map_coordinates(tile, [v, u], order=1, mode='wrap')


def round_tree(img, x, y, r_, col, seed=0):
    """Söğüt/dut gibi yuvarlak tepeli ağaç: birkaç elips öbeği + gövde."""
    rr = rng(seed)
    img = comp(img, (0.14, 0.11, 0.08), mask_poly(H, W, [(x - 5, y), (x + 5, y), (x + 3, y - r_ * 0.9), (x - 3, y - r_ * 0.9)]))
    leaf = fbm(H, W, 7, 3, 2)
    for k in range(7):
        cx = x + rr.normal(0, r_ * 0.45)
        cy = y - r_ * 1.1 + rr.normal(0, r_ * 0.3)
        m = mask_ellipse(H, W, cx, cy, r_ * rr.uniform(0.45, 0.75), r_ * rr.uniform(0.35, 0.6), blur=1.5)
        m *= np.clip(0.55 + leaf * 0.9, 0, 1)
        shade = (0.75 + 0.5 * leaf) * (1.1 if k % 2 else 0.85)
        c = np.asarray(col) * shade[..., None]
        img = img * (1 - m[..., None]) + c * m[..., None]
    return img


# ---------------------------------------------------------------- kareler
def c_baraj():
    """Şafak: vadinin aşağısında baraj duvarı, önünde dolmaya başlayan göl, kavaklar, sis."""
    img = vgrad(H, W, [(0, (0.36, 0.48, 0.64)), (0.35, (0.62, 0.68, 0.76)), (0.52, (0.92, 0.80, 0.66)), (0.6, (0.96, 0.84, 0.70))])
    img = glow(img, 1650, 640, 900, (0.25, 0.15, 0.05), 1.0)
    img = mountains(img, [(640, 220, (0.55, 0.58, 0.66), 600, 0.6), (700, 260, (0.44, 0.45, 0.50), 520, 0.4),
                          (760, 180, (0.47, 0.43, 0.36), 420, 0.2)], seed=11)
    # baraj duvarı: uzakta, gri beton, sağ yanı gölgede
    dq = [(1520, 642), (1930, 634), (1900, 742), (1550, 748)]
    dam = mask_poly(H, W, dq)
    concrete = tint(fbm(H, W, 14, 4, 5, aspect=(1.0, 0.12)), (0.50, 0.50, 0.50), (0.66, 0.65, 0.62))
    concrete *= np.clip(1.08 - (np.arange(W)[None, :] - 1520) / 900, 0.7, 1.1)[..., None]
    img = img * (1 - dam[..., None]) + concrete * dam[..., None]
    img = comp(img, (0.26, 0.26, 0.27), mask_poly(H, W, [(1520, 638), (1930, 630), (1930, 646), (1520, 652)]))
    img = comp(img, (0.40, 0.40, 0.40), mask_poly(H, W, [(1700, 646), (1740, 646), (1736, 744), (1704, 744)]) * 0.7)
    # vadi tabanı: perspektifli tarla parselleri
    y0, hz = 800, 760
    u, v = plane_uv(y0, hz, 120)
    u = u + 37 + (fbm(1, 2048, 400, 2, 2)[0][None, :1].repeat(1, 1) * 0)
    cu = np.floor(u / 70).astype(np.int64)
    cv = np.floor(v / 260).astype(np.int64)
    hsh = ((cu * 73856093) ^ (cv * 19349663)) % 9
    cols = np.array([(0.44, 0.40, 0.25), (0.52, 0.46, 0.30), (0.36, 0.37, 0.22), (0.58, 0.52, 0.36), (0.47, 0.43, 0.27),
                     (0.40, 0.42, 0.25), (0.55, 0.49, 0.33), (0.33, 0.33, 0.21), (0.50, 0.44, 0.28)], np.float32)
    base = cols[hsh]
    furrow = 0.5 + 0.5 * np.sin(u * (2.2 + (hsh % 3) * 0.6))
    base *= (0.88 + 0.12 * furrow)[..., None]
    base *= (0.85 + 0.3 * plane(fbm(1024, 1024, 30, 4, 8), y0, hz, 120))[..., None]
    edge = (np.abs((u / 70) - np.round(u / 70)) < 0.02 / np.maximum(v / 400, 0.2)) | (np.abs((v / 260) - np.round(v / 260)) < 0.015)
    base[edge] *= 0.8
    base *= np.linspace(0.85, 1.05, H - y0)[:, None, None]
    img[y0:] = base
    hill = mask_poly(H, W, [(0, 760), (500, 730), (900, 780), (1300, 770), (1520, 790), (1520, 815), (0, 840)], blur=2)
    img = img * (1 - hill[..., None]) + tint(fbm(H, W, 40, 5, 9), (0.30, 0.27, 0.20), (0.44, 0.39, 0.28)) * hill[..., None]
    # göl: barajın önünde biriken su
    lake = mask_poly(H, W, [(1180, 790), (2100, 772), (2400, 790), (2400, 880), (1600, 875), (1000, 840)], blur=3)
    lk = water(img.copy(), 760, 920, img[600:760][::-1], 12, (0.58, 0.62, 0.68), 0.4, 4)
    img = img * (1 - lake[..., None]) + lk * lake[..., None]
    # dere: perspektifle daralan kıvrım
    pts = [(-60, 1350), (260, 1200), (560, 1110), (820, 1010), (1000, 930), (1180, 850)]
    river = np.zeros((H, W), np.float32)
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        wa, wb = 30 + (ya - 800) * 0.18, 30 + (yb - 800) * 0.18
        river = np.maximum(river, mask_poly(H, W, [(xa - wa, ya), (xa + wa, ya), (xb + wb, yb), (xb - wb, yb)], blur=2))
    rv = np.array([0.50, 0.55, 0.62]) * (0.8 + 0.35 * fbm(H, W, 18, 3, 7, aspect=(0.15, 1.0)))[..., None]
    img = img * (1 - river[..., None]) + rv * river[..., None]
    # kavaklar: öbek öbek, rastgele aralıklarla
    r = rng(17)
    groups = [(140, 1010, 5), (430, 960, 4), (900, 990, 6), (1250, 900, 4), (1650, 960, 7), (2050, 1010, 5), (2280, 920, 3)]
    for gi, (gx, gy, n) in enumerate(groups):
        for k in range(n):
            x = gx + k * r.uniform(28, 46) + r.normal(0, 8)
            y = gy + r.uniform(-8, 14)
            sc = (y - 760) / 260
            img = poplar(img, x, y, r.uniform(150, 220) * sc, r.uniform(24, 34) * sc, (0.16, 0.19, 0.11), 100 + gi * 10 + k, lightc=1.0)
    for i in range(9):
        x = 1240 + i * r.uniform(40, 90)
        img = poplar(img, x, 840, r.uniform(60, 95), 14, (0.14, 0.17, 0.11), 200 + i)
    img = mist(img, 800, 50, 0.85, (0.92, 0.88, 0.82), 3)
    img = mist(img, 1000, 120, 0.25, (0.90, 0.86, 0.80), 4)
    img = light(img, 0.85 + 0.3 * radial(H, W, 1650, 640, 2200, 1400, 1.0), (1.05, 1.0, 0.94))
    return phone_photo(img, 21, grain=0.022, vignette=0.3, warm=0.03, sharpen=0.35, soft=1.0, contrast=1.04, noise_dark=0.6)


def c_koy():
    """Akşam: yamaçta kerpiç evler ve saat kulesi, önde dere."""
    img = sky_dusk(H, W, 31, [(0, (0.24, 0.32, 0.50)), (0.45, (0.52, 0.52, 0.62)), (0.62, (0.90, 0.66, 0.50)), (0.7, (0.95, 0.74, 0.55))])
    img = glow(img, 300, 820, 900, (0.30, 0.16, 0.04), 1.0)
    img = mountains(img, [(700, 230, (0.42, 0.40, 0.48), 520, 0.6), (820, 220, (0.36, 0.32, 0.30), 420, 0.3)], seed=21)
    slope = mask_poly(H, W, [(0, 900), (700, 760), (1500, 720), (2400, 820), (2400, 1350), (0, 1350)], blur=2)
    st = tint(fbm(H, W, 30, 6, 41), (0.28, 0.24, 0.18), (0.46, 0.38, 0.26))
    img = img * (1 - slope[..., None]) + st * slope[..., None]
    r = rng(5)
    items = []
    for i in range(26):
        x = int(r.uniform(300, 2100))
        y = int(760 + (x - 1300) ** 2 / 9000 + r.uniform(-40, 120))
        s = r.uniform(0.6, 1.0)
        items.append((x, y, int(170 * s), int(110 * s), 300 + i, r.random() < 0.4))
    items.sort(key=lambda t: t[1])
    img = cluster_houses(img, items[:13], 0.82)
    img = put_tower(img, [(1180, 330), (1300, 326), (1318, 790), (1160, 794)], 0.9, warm_top=0.35)
    img = cluster_houses(img, items[13:], 0.85)
    for i in range(14):
        x = r.uniform(100, 2300)
        img = poplar(img, x, 1010 + r.uniform(0, 40), r.uniform(200, 320), r.uniform(30, 44), (0.12, 0.14, 0.09), 400 + i, lightc=-1.0)
    img = water(img, 1080, 1350, None, 22, (0.22, 0.23, 0.26), 0.58, 9)
    img = light(img, 0.8 + 0.35 * radial(H, W, 300, 800, 2400, 1500, 1.0), (1.06, 0.98, 0.9))
    return phone_photo(img, 22, grain=0.026, vignette=0.32, warm=0.02, sharpen=0.35, soft=1.0, noise_dark=0.9)


def c_kopru():
    """Bulutlu öğleden sonra: taş kemer köprü, taşkın dere, köprünün ortasında küçük bir figür."""
    img = vgrad(H, W, [(0, (0.58, 0.62, 0.66)), (0.5, (0.74, 0.76, 0.77)), (1, (0.80, 0.80, 0.79))])
    cl = fbm(H, W, 300, 6, 3, aspect=(0.4, 1.0))
    img *= (0.85 + 0.25 * cl)[..., None]
    img = mountains(img, [(560, 200, (0.50, 0.53, 0.56), 520, 0.6), (640, 190, (0.36, 0.38, 0.36), 420, 0.3)], seed=61)
    banks = mask_poly(H, W, [(0, 660), (700, 700), (900, 820), (0, 900)], blur=2)
    banks = np.maximum(banks, mask_poly(H, W, [(1500, 820), (1800, 700), (2400, 660), (2400, 900)], blur=2))
    img = img * (1 - banks[..., None]) + tint(fbm(H, W, 30, 5, 62), (0.20, 0.22, 0.15), (0.36, 0.36, 0.24)) * banks[..., None]
    r = rng(4)
    for i in range(14):  # söğütler
        x = r.uniform(0, 620) if i < 7 else r.uniform(1820, 2400)
        img = round_tree(img, x, 770 + r.uniform(0, 40), r.uniform(70, 120), (0.20, 0.25, 0.14), 500 + i)
    # su: bulanık kahverengi, akıntı çizgileri ve köpük
    wy = 860
    flow = plane(fbm(1024, 1024, 40, 5, 66, aspect=(0.1, 1.0)), wy, 820, 90, 1.0)
    wcol = tint(flow, (0.30, 0.25, 0.17), (0.55, 0.48, 0.36))
    foam = np.clip((plane(fbm(1024, 1024, 14, 4, 67, aspect=(0.12, 1.0)), wy, 820, 90, 1.0) - 0.64) * 4, 0, 1)
    wcol = wcol * (1 - foam[..., None]) + np.array([0.78, 0.76, 0.70]) * foam[..., None]
    img[wy:] = wcol * np.linspace(1.0, 0.8, H - wy)[:, None, None]
    # köprü
    deck_top, deck_bot = 700, 760
    br = np.zeros((H, W), np.float32)
    br = np.maximum(br, mask_poly(H, W, [(560, deck_top + 10), (1200, deck_top - 40), (1840, deck_top + 10), (1840, 900), (560, 900)]))
    arches = mask_draw(H, W, lambda d, ss: [d.ellipse([cx0 * ss, ay * ss, cx1 * ss, (ay + (cx1 - cx0)) * ss], fill=255) for cx0, cx1, ay in
                                            ((700, 980, 790), (1040, 1360, 740), (1420, 1700, 790))])
    arches = np.maximum(arches, mask_draw(H, W, lambda d, ss: [d.rectangle([cx0 * ss, (ay + (cx1 - cx0) / 2) * ss, cx1 * ss, 1000 * ss], fill=255) for cx0, cx1, ay in
                                                               ((700, 980, 790), (1040, 1360, 740), (1420, 1700, 790))]))
    bridge = br * (1 - arches)
    stone = stone_blocks(H, W, 34, 18, 70, base=(0.58, 0.54, 0.47))
    stone *= np.linspace(1.05, 0.7, H)[:, None, None]
    img = img * (1 - bridge[..., None]) + stone * bridge[..., None]
    # kemerlerin içi ve altta su
    inside = arches * br
    img = img * (1 - inside[..., None] * 0.55)
    # korkuluk
    img = comp(img, (0.40, 0.37, 0.33), mask_poly(H, W, [(560, deck_top - 4), (1200, deck_top - 54), (1840, deck_top - 4), (1840, deck_top + 10), (1200, deck_top - 40), (560, deck_top + 10)]))
    # figür: sırt çantalı Ece
    fx, fy = 1260, 652
    fig = mask_draw(H, W, lambda d, ss: (d.ellipse([(fx - 7) * ss, (fy - 52) * ss, (fx + 7) * ss, (fy - 38) * ss], fill=255),
                                         d.polygon([((fx - 10) * ss, (fy - 38) * ss), ((fx + 10) * ss, (fy - 38) * ss), ((fx + 9) * ss, (fy - 8) * ss), ((fx - 9) * ss, (fy - 8) * ss)], fill=255),
                                         d.rectangle([(fx - 18) * ss, (fy - 36) * ss, (fx - 6) * ss, (fy - 14) * ss], fill=255),
                                         d.line([(fx - 4) * ss, (fy - 8) * ss, (fx - 7) * ss, fy * ss], fill=255, width=5 * ss),
                                         d.line([(fx + 4) * ss, (fy - 8) * ss, (fx + 8) * ss, fy * ss], fill=255, width=5 * ss)))
    img = comp(img, (0.12, 0.11, 0.11), fig)
    img = comp(img, (0.55, 0.20, 0.15), fig * mask_poly(H, W, [(fx - 18, fy - 36), (fx - 6, fy - 36), (fx - 6, fy - 14), (fx - 18, fy - 14)]) * 0.8)
    # suda köprünün yansıması
    img = depth_blur(img, np.clip((np.arange(H)[:, None] - 1100) / 200, 0, 1) * np.ones((1, W)), 1.5)
    img = mist(img, 600, 60, 0.35, (0.80, 0.81, 0.82), 5)
    return phone_photo(img, 23, grain=0.022, vignette=0.3, warm=-0.01, sharpen=0.4, soft=0.9, contrast=1.08)


def c_telefon():
    """Su altında taşların üstünde çatlak ekranlı telefon; ekran hâlâ yanıyor."""
    r = rng(8)
    img = np.ones((H, W, 3), np.float32) * np.array([0.16, 0.20, 0.18])
    # çakıl taşları
    for i in range(220):
        cx, cy = r.uniform(-50, W + 50), r.uniform(-50, H + 50)
        rx, ry = r.uniform(40, 150), r.uniform(30, 110)
        m = mask_ellipse(H, W, cx, cy, rx, ry, blur=2)
        col = np.array([0.42, 0.40, 0.34]) * r.uniform(0.5, 1.2) + r.normal(0, 0.03, 3)
        tex = col * (0.8 + 0.4 * fbm(H, W, 16, 3, 900 + i % 9))[..., None]
        sh = radial(H, W, cx - rx * 0.3, cy - ry * 0.3, rx * 1.2, ry * 1.2, 1.0)
        tex = tex * (0.7 + 0.5 * sh[..., None])
        img = img * (1 - m[..., None]) + tex * m[..., None]
    # telefon
    ph = Image.new('RGBA', (520, 1060), (0, 0, 0, 0))
    d = ImageDraw.Draw(ph)
    d.rounded_rectangle([0, 0, 519, 1059], 70, fill=(18, 20, 22, 255))
    d.rounded_rectangle([18, 18, 501, 1041], 54, fill=(14, 19, 22, 255))
    scr = np.zeros((1060, 520, 3), np.float32)
    # ekran: koyu sohbet, alt yarısı yanık
    scr[:] = (0.06, 0.08, 0.09)
    scr[560:1041] = (0.10, 0.13, 0.15)
    sc = Image.fromarray((scr * 255).astype(np.uint8))
    sd = ImageDraw.Draw(sc)
    sd.rounded_rectangle([60, 640, 330, 720], 30, fill=(46, 92, 80))
    sd.rounded_rectangle([60, 900, 460, 980], 36, outline=(70, 90, 95), width=4)
    sd.rectangle([18, 18, 501, 540], fill=(5, 5, 6))
    mask = Image.new('L', (520, 1060), 0)
    ImageDraw.Draw(mask).rounded_rectangle([18, 18, 501, 1041], 54, fill=255)
    ph.paste(sc, (0, 0), mask)
    # çatlaklar
    cd = ImageDraw.Draw(ph)
    for k in range(18):
        x, y = 260 + r.normal(0, 30), 520 + r.normal(0, 40)
        a = r.uniform(0, 2 * np.pi)
        pts = [(x, y)]
        for _ in range(40):
            a += r.normal(0, 0.25)
            x += np.cos(a) * 14
            y += np.sin(a) * 14
            pts.append((x, y))
        cd.line(pts, fill=(170, 190, 195, 150), width=2)
    quad = [(980, 300), (1400, 380), (1260, 1180), (820, 1080)]
    canvas = to_pil(img).convert('RGBA')
    canvas.alpha_composite(warp_rgba(ph, (W, H), quad))
    img = from_pil(canvas)
    img = glow(img, 1080, 900, 420, (0.04, 0.10, 0.09), 1.0)
    # su: yeşilimsi renk, kostik ışık, kabarcıklar
    caus = fbm(H, W, 40, 3, 81)
    caus = np.clip(1 - np.abs(caus - 0.5) * 9, 0, 1) ** 2
    img = img * np.array([0.70, 0.88, 0.85]) + caus[..., None] * np.array([0.10, 0.14, 0.12])
    for i in range(60):
        bx, by, br_ = r.uniform(700, 1600), r.uniform(100, 1200), r.uniform(4, 16)
        ring = mask_ellipse(H, W, bx, by, br_, br_, ring=1.5)
        img = comp(img, (0.75, 0.85, 0.85), ring * 0.5)
    img = depth_blur(img, 1 - radial(H, W, 1110, 740, 900, 700, 1.0), 6)
    img = light(img, 0.5 + 0.7 * radial(H, W, 1100, 500, 1800, 1300, 1.0), (0.95, 1.0, 1.0))
    return phone_photo(img, 24, grain=0.03, vignette=0.5, sharpen=0.3, soft=1.4, noise_dark=1.2)


def c_gece():
    """Gece: yıldızlar, kule ve evlerin siluetleri, derenin karşısında tek bir fener ve yansıması."""
    img = vgrad(H, W, [(0, (0.03, 0.04, 0.09)), (0.45, (0.08, 0.10, 0.18)), (0.66, (0.17, 0.17, 0.25))])
    img = stars(img, 2600, 5)
    img = mountains(img, [(760, 200, (0.08, 0.09, 0.13), 520, 0.0), (820, 150, (0.05, 0.055, 0.075), 420, 0.0)], seed=71)
    # karşı yaka ve değirmen silueti
    img = comp(img, (0.025, 0.028, 0.035), mask_poly(H, W, [(1500, 880), (1900, 830), (2400, 850), (2400, 960), (1500, 960)]))
    mill = mask_poly(H, W, [(1860, 840), (2060, 840), (2060, 760), (1960, 710), (1860, 760)])
    img = comp(img, (0.03, 0.03, 0.035), mill)
    img = comp(img, (0.03, 0.03, 0.035), mask_draw(H, W, lambda d, ss: d.ellipse([1990 * ss, 760 * ss, 2120 * ss, 890 * ss], outline=255, width=8 * ss)))
    # fener
    lx, ly = 1800, 905
    img = glow(img, lx, ly, 120, (0.9, 0.45, 0.12), 0.9)
    img = glow(img, lx, ly, 18, (1.0, 0.85, 0.5), 1.6)
    # bu yaka: evler ve kule siluetleri
    sil = np.zeros((H, W), np.float32)
    r = rng(3)
    for i in range(10):
        x = r.uniform(0, 1450)
        y = 860 + r.uniform(-30, 40)
        sil = np.maximum(sil, mask_poly(H, W, [(x, y), (x + r.uniform(120, 220), y), (x + r.uniform(120, 220), 1000), (x, 1000)]))
    sil = np.maximum(sil, mask_poly(H, W, [(900, 300), (1010, 300), (1030, 1000), (880, 1000)]))
    sil = np.maximum(sil, mask_poly(H, W, [(886, 300), (955, 250), (1024, 300)]))
    img = img * (1 - sil[..., None]) + np.array([0.012, 0.013, 0.018]) * sil[..., None]
    # kulede saat camı ay ışığını yakalar
    img = comp(img, (0.10, 0.11, 0.13), mask_draw(H, W, lambda d, ss: d.ellipse([920 * ss, 420 * ss, 990 * ss, 490 * ss], outline=255, width=3 * ss)))
    # okulun penceresinde Ece'nin telefon ışığı
    img = comp(img, (0.12, 0.20, 0.22), mask_poly(H, W, [(380, 905), (410, 905), (410, 930), (380, 930)]) * 0.9)
    # dere: koyu, fenerin uzun yansıması
    img = water(img, 980, H, None, 14, (0.02, 0.025, 0.04), 0.6, 72)
    refl = np.exp(-((np.arange(W)[None, :] - lx) / 22) ** 2) * np.clip(1 - (np.arange(H)[:, None] - 980) / 330, 0, 1)
    refl *= (np.arange(H)[:, None] > 980) * (0.5 + 0.8 * fbm(H, W, 10, 3, 73, aspect=(0.05, 1.0)))
    img += refl[..., None] * np.array([0.55, 0.28, 0.08])
    return phone_photo(img, 25, grain=0.045, vignette=0.5, sharpen=0.2, soft=1.0, noise_dark=1.8, contrast=1.0)


def c_su():
    """Şafak: aşağı tarlaları basmış durgun su, yarı batık çit direkleri ve ağaç, uzakta köy."""
    img = vgrad(H, W, [(0, (0.46, 0.55, 0.68)), (0.4, (0.72, 0.74, 0.78)), (0.56, (0.95, 0.86, 0.74)), (0.6, (0.97, 0.88, 0.76))])
    img = glow(img, 1600, 780, 800, (0.25, 0.14, 0.04), 1.0)
    img = mountains(img, [(700, 200, (0.56, 0.58, 0.66), 600, 0.5), (770, 150, (0.44, 0.43, 0.46), 420, 0.3)], seed=81)
    # uzak köy ve kule silueti
    sil = np.zeros((H, W), np.float32)
    r = rng(12)
    for i in range(14):
        x = 300 + r.uniform(0, 900)
        y = 770 + r.uniform(-10, 10)
        sil = np.maximum(sil, mask_poly(H, W, [(x, y), (x + r.uniform(30, 60), y), (x + r.uniform(30, 60), 800), (x, 800)]))
    sil = np.maximum(sil, mask_poly(H, W, [(700, 660), (726, 660), (730, 800), (696, 800)]))
    sil = np.maximum(sil, mask_poly(H, W, [(696, 662), (713, 648), (730, 662)]))
    img = img * (1 - sil[..., None] * 0.85) + np.array([0.30, 0.30, 0.34]) * sil[..., None] * 0.85
    shore = mask_poly(H, W, [(0, 790), (2400, 780), (2400, 815), (0, 820)], blur=2)
    img = comp(img, (0.30, 0.30, 0.26), shore)
    for i in range(18):
        img = poplar(img, 100 + i * 130 + r.uniform(-30, 30), 805, r.uniform(80, 140), 20, (0.22, 0.24, 0.20), 600 + i)
    img = mist(img, 800, 30, 0.7, (0.92, 0.88, 0.82), 6)
    # su: ayna gibi, hafif dalgacık
    img = water(img, 815, H, None, 4, (0.55, 0.58, 0.60), 0.18, 83)
    # çit direkleri ve tel
    posts = np.zeros((H, W), np.float32)
    for i in range(12):
        x = 200 + i * 190 + r.uniform(-10, 10)
        top = 1000 + i * 6 + r.uniform(-20, 0)
        posts = np.maximum(posts, mask_poly(H, W, [(x - 8, top), (x + 8, top + 3), (x + 9, 1120 + i * 8), (x - 9, 1120 + i * 8)]))
    img = comp(img, (0.20, 0.17, 0.14), posts)
    img = comp(img, (0.20, 0.18, 0.16), mask_draw(H, W, lambda d, ss: d.line([(200 * ss, 1040 * ss), (2400 * ss, 1100 * ss)], fill=255, width=2 * ss)) * 0.8)
    # yarı batık ağaç
    def tree(d, ss):
        x0, y0 = 1880, 1060
        d.line([x0 * ss, y0 * ss, (x0 + 10) * ss, 820 * ss], fill=255, width=18 * ss)
        for k in range(26):
            a = r.uniform(-2.8, -0.3)
            L = r.uniform(60, 220)
            sy = r.uniform(820, 960)
            d.line([(x0 + 5) * ss, sy * ss, (x0 + 5 + np.cos(a) * L) * ss, (sy + np.sin(a) * L) * ss], fill=255, width=int(r.uniform(2, 6) * ss))
    img = comp(img, (0.14, 0.13, 0.12), mask_draw(H, W, tree))
    # direklerin ve ağacın yansıması (basitçe aşağıya ters)
    img = light(img, 0.85 + 0.3 * radial(H, W, 1600, 780, 2200, 1400, 1.0), (1.05, 1.0, 0.95))
    return phone_photo(img, 26, grain=0.02, vignette=0.32, warm=0.02, sharpen=0.3, soft=1.0, contrast=1.04)


FRAMES = {'c_baraj': c_baraj, 'c_koy': c_koy, 'c_kopru': c_kopru, 'c_telefon': c_telefon, 'c_gece': c_gece, 'c_su': c_su}

# Sahne tanımları. Zamanlar ses bandıyla (tools/assets/audio.py) eşleşir.
# kare: (dosya ya da None=siyah, süre sn, başlangıç [x 0..1, ölçek], bitiş [x, ölçek], altyazılar [(başla, bitir, metin)])
SCENES = {
    'prolog': {
        'baslik': 'Ilgındere',
        'ses': 'sinema/prolog.ogg',
        'kapak': 'sinema/c_baraj.jpg',
        'kareler': [
            ('c_baraj', 7.0, [0.62, 1.04], [0.72, 1.12], [(0.8, 6.4, 'Ilgın Barajı’nın kapakları dün kapandı.')]),
            ('c_koy', 7.0, [0.40, 1.12], [0.52, 1.04], [(0.4, 6.4, 'Yedi gün içinde Ilgındere suyun altında kalacak.')]),
            ('c_kopru', 10.4, [0.36, 1.0], [0.53, 1.22], [(0.6, 5.4, 'Ece Doğan, 27. Dedesinin köyüne ilk kez geliyor.'),
                                                        (5.8, 10.0, 'Köprü eski. Su her saat biraz daha yükseliyor.')]),
            ('c_telefon', 7.1, [0.47, 1.18], [0.45, 1.05], []),
            (None, 6.5, [0.5, 1], [0.5, 1], [(0.4, 3.0, 'Ekranın yarısı karardı.'), (3.2, 6.3, 'Açık kalan tek konuşma: bir defterdeki numara.')]),
        ],
    },
    'gun1_son': {
        'baslik': 'Gece',
        'ses': 'sinema/gun1_son.ogg',
        'kapak': 'sinema/c_gece.jpg',
        'kareler': [
            ('c_gece', 9.5, [0.42, 1.0], [0.70, 1.1], [(0.8, 4.6, 'Gece. Ilgındere’de tek bir ışık yanıyor.'), (5.0, 9.0, 'Derenin öbür yakasında.')]),
            ('c_su', 8.0, [0.30, 1.1], [0.62, 1.02], [(0.6, 7.4, 'Sabah. Su aşağı tarlalara ulaştı.')]),
            (None, 4.5, [0.5, 1], [0.5, 1], [(0.4, 4.3, '2. gün · Bekçi')]),
        ],
    },
}


def write_scenes():
    data = {}
    for key, sc in SCENES.items():
        frames = [{'img': f'sinema/{f}.jpg' if f else None, 'sure': d, 'bas': a, 'son': b,
                   'yazi': [{'bas': s0, 'son': s1, 'metin': t} for s0, s1, t in caps]} for f, d, a, b, caps in sc['kareler']]
        data[key] = {'baslik': sc['baslik'], 'ses': sc['ses'], 'kapak': sc['kapak'],
                     'sure': round(sum(f['sure'] for f in frames), 2), 'kareler': frames}
    (OUT / 'sinema.json').write_text(json.dumps(data, ensure_ascii=False, indent=1))


def main():
    only = [a for a in sys.argv[1:] if not a.startswith('--')]
    for key, fn in FRAMES.items():
        if only and key not in only:
            continue
        p = OUT / f'{key}.jpg'
        save_jpg(fn(), p, 80, size=(1920, 1080))
        print(f'sinema/{key}.jpg  {p.stat().st_size // 1024} KB')
    write_scenes()
    print('sinema/sinema.json')


if __name__ == '__main__':
    main()
