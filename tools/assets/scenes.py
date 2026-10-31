"""3.–7. günlerin sinema kareleri ve sahne tanımları (cinema.py bunları kendi listesine ekler)."""
import numpy as np
from PIL import Image
from scipy import ndimage

from gfx import (blur, comp, depth_blur, fbm, from_pil, glow, light, mask_draw, mask_ellipse, mask_poly, phone_photo,
                 radial, ridge1d, rng, stone_blocks, tint, to_pil, vgrad, warp_rgba, wood)
from cinema import H, W, mist, mountains, plane, poplar, put_tower, round_tree, stars, water, cluster_houses
from photos import mudbrick_house, sky_dusk


def smoke(img, x, y, height, seed=0, strength=0.5, col=(0.80, 0.80, 0.80)):
    n = fbm(H, W, 30, 4, seed, aspect=(0.6, 1.0))
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    t = np.clip((y - yy) / height, 0, 1)
    cx = x + (t ** 1.5) * 160 + (n - 0.5) * 60 * t
    width = 14 + t * 90
    m = np.exp(-((xx - cx) / width) ** 2) * (yy < y) * (1 - t) * (0.4 + 0.8 * n)
    m = ndimage.gaussian_filter(m, 3) * strength
    return img * (1 - m[..., None]) + np.asarray(col) * m[..., None]


def mill(img, x0, y_base, w, h, seed=0, dim=1.0, lit_window=False, lantern=False):
    """İki katlı taş değirmen, kiremit çatı, baca, yanında yosunlu su çarkı."""
    r = rng(seed)
    body = stone_blocks(h, w, 40, 22, seed, base=(0.60, 0.55, 0.47))
    body *= np.linspace(1.0, 0.78, h)[:, None, None]
    body[:, : int(w * 0.18)] *= 0.72
    y0 = y_base - h
    img[y0:y_base, x0:x0 + w] = body * dim
    roof = mask_poly(H, W, [(x0 - 24, y0 + 4), (x0 + w * 0.5, y0 - h * 0.42), (x0 + w + 24, y0 + 4)])
    tiles = tint(fbm(H, W, 7, 3, seed + 3, aspect=(1, 0.3)), (0.30, 0.15, 0.10), (0.50, 0.26, 0.17))
    img = img * (1 - roof[..., None]) + tiles * dim * roof[..., None]
    cx = int(x0 + w * 0.72)
    img = comp(img, np.array((0.42, 0.38, 0.33)) * dim, mask_poly(H, W, [(cx, y0 - h * 0.30), (cx + 34, y0 - h * 0.30), (cx + 34, y0 - h * 0.05), (cx, y0 - h * 0.05)]))
    for k, (wx, wy) in enumerate([(0.30, 0.30), (0.62, 0.30), (0.30, 0.66)]):
        wm = mask_poly(H, W, [(x0 + w * wx, y0 + h * wy), (x0 + w * wx + 46, y0 + h * wy), (x0 + w * wx + 46, y0 + h * wy + 56), (x0 + w * wx, y0 + h * wy + 56)])
        colw = (0.95, 0.62, 0.25) if (lit_window and k == 2) else (0.07, 0.07, 0.08)
        img = comp(img, colw, wm)
    dx = x0 + w * 0.62
    img = comp(img, np.array((0.22, 0.16, 0.10)) * dim, mask_poly(H, W, [(dx, y_base - 120), (dx + 60, y_base - 120), (dx + 60, y_base), (dx, y_base)]))
    # su çarkı
    wcx, wcy, wr = x0 - 70, y_base - 110, 118
    rim = mask_ellipse(H, W, wcx, wcy, wr, wr, ring=14)
    for a in np.linspace(0, np.pi, 8, endpoint=False):
        rim = np.maximum(rim, mask_poly(H, W, [(wcx + np.cos(a) * wr, wcy + np.sin(a) * wr), (wcx + np.cos(a) * wr + 6, wcy + np.sin(a) * wr + 6),
                                               (wcx - np.cos(a) * wr + 6, wcy - np.sin(a) * wr + 6), (wcx - np.cos(a) * wr, wcy - np.sin(a) * wr)]))
    moss = fbm(H, W, 8, 3, seed + 9)
    wcol = np.array([0.24, 0.20, 0.14]) * (0.7 + 0.5 * moss[..., None]) + np.array([0.0, 0.05, 0.0]) * moss[..., None]
    img = img * (1 - rim[..., None]) + wcol * dim * rim[..., None]
    img = smoke(img, cx + 17, y0 - h * 0.31, 340, seed + 5, 0.45 if dim > 0.5 else 0.25)
    if lantern:
        img = glow(img, dx - 30, y_base - 60, 160, (0.85, 0.45, 0.12), 0.9)
        img = glow(img, dx - 30, y_base - 60, 16, (1.0, 0.85, 0.5), 1.4)
    return img


def goats(img, items, dim=1.0):
    for x, y, s in items:
        body = mask_ellipse(H, W, x, y, 26 * s, 14 * s)
        head = mask_ellipse(H, W, x + 26 * s, y - 12 * s, 9 * s, 7 * s)
        legs = mask_poly(H, W, [(x - 18 * s, y), (x - 14 * s, y), (x - 14 * s, y + 24 * s), (x - 18 * s, y + 24 * s)])
        legs = np.maximum(legs, mask_poly(H, W, [(x + 12 * s, y), (x + 16 * s, y), (x + 16 * s, y + 24 * s), (x + 12 * s, y + 24 * s)]))
        m = np.maximum(np.maximum(body, head), legs)
        img = comp(img, np.array((0.20, 0.17, 0.14)) * dim, m)
    return img


def c_degirmen(variant='gun'):
    aksam = variant == 'aksam'
    if aksam:
        img = sky_dusk(H, W, 41, [(0, (0.08, 0.11, 0.22)), (0.5, (0.22, 0.24, 0.36)), (0.7, (0.55, 0.40, 0.42)), (0.8, (0.72, 0.48, 0.36))])
    else:
        img = vgrad(H, W, [(0, (0.60, 0.65, 0.70)), (0.55, (0.76, 0.78, 0.79)), (1, (0.82, 0.82, 0.80))])
        img *= (0.9 + 0.15 * fbm(H, W, 300, 5, 43, aspect=(0.4, 1.0)))[..., None]
    mcol = [(0.30, 0.30, 0.38), (0.22, 0.22, 0.26)] if aksam else [(0.54, 0.57, 0.60), (0.42, 0.44, 0.42)]
    img = mountains(img, [(560, 180, mcol[0], 520, 0.5), (640, 160, mcol[1], 420, 0.3)], seed=91)
    dim = 0.38 if aksam else 1.0
    slope = mask_poly(H, W, [(0, 760), (900, 700), (1700, 720), (2400, 690), (2400, 1000), (0, 1000)], blur=2)
    st = tint(fbm(H, W, 30, 6, 92), (0.24, 0.24, 0.16), (0.42, 0.40, 0.26)) * dim
    img = img * (1 - slope[..., None]) + st * slope[..., None]
    r = rng(7)
    for i in range(8):
        img = round_tree(img, r.uniform(1700, 2400), 780 + r.uniform(0, 60), r.uniform(70, 110), np.array((0.18, 0.23, 0.13)) * dim, 700 + i)
    img = mill(img, 980, 900, 460, 300, 13, dim, lit_window=aksam, lantern=aksam)
    # çit ve keçiler
    fence = np.zeros((H, W), np.float32)
    for x in range(1500, 1900, 46):
        fence = np.maximum(fence, mask_poly(H, W, [(x, 880), (x + 7, 880), (x + 7, 950), (x, 950)]))
    fence = np.maximum(fence, mask_poly(H, W, [(1500, 900), (1900, 896), (1900, 902), (1500, 906)]))
    img = comp(img, np.array((0.28, 0.22, 0.16)) * dim, fence)
    img = goats(img, [(1580, 920, 1.0), (1690, 930, 0.9), (1790, 915, 1.05)], dim)
    img = water(img, 1000, H, None, 14, (0.30, 0.30, 0.28) if not aksam else (0.06, 0.06, 0.09), 0.55, 94)
    if aksam:
        refl = np.exp(-((np.arange(W)[None, :] - 1228) / 20) ** 2) * np.clip(1 - (np.arange(H)[:, None] - 1000) / 300, 0, 1) * (np.arange(H)[:, None] > 1000)
        img += refl[..., None] * np.array([0.45, 0.22, 0.06]) * (0.5 + 0.8 * fbm(H, W, 10, 3, 95, aspect=(0.05, 1.0)))[..., None]
        return phone_photo(img, 41, grain=0.04, vignette=0.45, sharpen=0.3, soft=1.0, noise_dark=1.6)
    img = mist(img, 640, 50, 0.3, (0.82, 0.83, 0.84), 9)
    return phone_photo(img, 42, grain=0.022, vignette=0.3, sharpen=0.4, soft=0.9, contrast=1.06)


def c_gecit():
    """Söğütlerin altında geniş, sığ geçit; dipte düz taşlar görünüyor."""
    img = vgrad(H, W, [(0, (0.62, 0.66, 0.70)), (0.6, (0.78, 0.79, 0.80)), (1, (0.84, 0.83, 0.80))])
    img = mountains(img, [(520, 160, (0.56, 0.58, 0.62), 520, 0.5), (600, 140, (0.42, 0.44, 0.42), 420, 0.3)], seed=101)
    far = mask_poly(H, W, [(0, 640), (2400, 620), (2400, 700), (0, 720)], blur=2)
    img = img * (1 - far[..., None]) + tint(fbm(H, W, 30, 5, 102), (0.26, 0.28, 0.18), (0.42, 0.42, 0.28)) * far[..., None]
    r = rng(11)
    for i in range(10):
        x = r.uniform(0, 500) if i < 5 else r.uniform(1900, 2400)
        img = round_tree(img, x, 700 + r.uniform(0, 30), r.uniform(120, 180), (0.22, 0.28, 0.15), 800 + i)
    # sığ su: dipteki taşlar görünür, taşların akış yönünde beyaz köpük
    y0 = 700
    hh = H - y0
    bed = np.ones((hh, W, 3), np.float32) * np.array([0.34, 0.31, 0.24])
    bed *= (0.8 + 0.3 * fbm(hh, W, 20, 4, 104))[..., None]
    foam = np.zeros((hh, W), np.float32)
    for i in range(170):
        v = r.random() ** 0.6
        cy = v * hh
        sc = 0.15 + v * 1.5
        cx = r.uniform(0, W)
        rx, ry = r.uniform(26, 60) * sc, r.uniform(12, 24) * sc
        m = mask_ellipse(hh, W, cx, cy, rx, ry, blur=1.0 + sc)
        hl = mask_ellipse(hh, W, cx - rx * 0.2, cy - ry * 0.35, rx * 0.6, ry * 0.45, blur=2 + sc * 2)
        c = np.array([0.46, 0.42, 0.34]) * r.uniform(0.7, 1.15)
        bed = bed * (1 - m[..., None]) + (c * (0.75 + 0.5 * hl[..., None])) * m[..., None]
        if r.random() < 0.5:
            foam = np.maximum(foam, mask_ellipse(hh, W, cx + rx * 0.9, cy, rx * 0.7, ry * 0.25, blur=2 + sc * 2) * 0.7)
    tile = fbm(1024, 1024, 30, 4, 103, aspect=(0.12, 1.0))
    ripples = plane(tile, y0, 640, 90)
    streak = np.clip((plane(fbm(1024, 1024, 10, 3, 105, aspect=(0.1, 1.0)), y0, 640, 90) - 0.6) * 3, 0, 1)
    surface = np.array([0.62, 0.66, 0.68]) * (0.8 + 0.3 * ripples)[..., None]
    depth = np.clip(0.75 - np.linspace(0, 0.5, hh), 0.22, 0.75)[:, None, None]
    # su yüzeyinin kırılması: dip görüntüsü dalgalarla kayar
    dx = ((ripples - 0.5) * 10).astype(np.int32)
    bed = bed[np.arange(hh)[:, None], np.clip(np.arange(W)[None, :] + dx, 0, W - 1)]
    water_img = bed * (1 - depth) * np.array([0.92, 1.0, 0.95]) + surface * depth
    water_img = water_img * (1 - foam[..., None] * 0.7) + np.array([0.86, 0.86, 0.82]) * foam[..., None] * 0.7
    water_img = water_img * (1 - streak[..., None] * 0.25) + np.array([0.80, 0.82, 0.82]) * streak[..., None] * 0.25
    img[y0:] = water_img
    img = depth_blur(img, np.clip((np.arange(H)[:, None] - 1150) / 150, 0, 1) * np.ones((1, W)), 2.0)
    return phone_photo(img, 43, grain=0.022, vignette=0.3, sharpen=0.45, soft=0.8, contrast=1.06)


EXTRA_FRAMES = {
    'c_degirmen': lambda: c_degirmen('aksam'),
    'c_degirmen_gun': lambda: c_degirmen('gun'),
    'c_gecit': c_gecit,
}

EXTRA_SCENES = {
    'gun3_son': {
        'baslik': 'Değirmen',
        'ses': 'sinema/gun3_son.ogg',
        'kapak': 'sinema/c_degirmen.jpg',
        'kareler': [
            ('c_degirmen', 9.0, [0.48, 1.12], [0.52, 1.02], [(0.6, 4.4, 'Değirmenin penceresinde gece geç saate kadar ışık yandı.'),
                                                            (4.6, 8.6, 'Su okulun bahçe duvarına ulaştı.')]),
            ('c_gece', 6.5, [0.60, 1.05], [0.75, 1.12], [(0.5, 6.0, 'Çan yine dokuzu on geçe çaldı.')]),
            (None, 4.5, [0.5, 1], [0.5, 1], [(0.4, 4.3, '4. gün · Kamulaştırma')]),
        ],
    },
}
