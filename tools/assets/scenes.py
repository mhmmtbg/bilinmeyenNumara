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


# ---------------------------------------------------------------- 4. gün
SERIF = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
MONO = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'


def _text_mask(h, w, text, xy, font_path, size, angle=0.0, anchor='la'):
    from PIL import ImageDraw, ImageFont
    ss = 2
    im = Image.new('L', (w * ss, h * ss), 0)
    f = ImageFont.truetype(font_path, size * ss)
    ImageDraw.Draw(im).text((xy[0] * ss, xy[1] * ss), text, font=f, fill=255, anchor=anchor)
    if angle:
        im = im.rotate(angle, resample=Image.BICUBIC, center=(xy[0] * ss, xy[1] * ss))
    return np.asarray(im.resize((w, h), Image.LANCZOS), np.float32) / 255


def gravestone(img, cx, base, sw, sh, lines, seed=0, dim=1.0, scale=1.0):
    """Yuvarlak tepeli taş mezar; oyma yazı (koyu iç, aydınlık alt kenar)."""
    top = base - sh
    m = mask_poly(H, W, [(cx - sw / 2, base), (cx - sw / 2, top + sw / 2), (cx + sw / 2, top + sw / 2), (cx + sw / 2, base)])
    m = np.maximum(m, mask_ellipse(H, W, cx, top + sw / 2, sw / 2, sw / 2))
    stone = tint(fbm(H, W, 10, 4, seed), (0.48, 0.47, 0.44), (0.68, 0.67, 0.63))
    lichen = np.clip((fbm(H, W, 18, 4, seed + 1) - 0.62) * 4, 0, 1)
    stone = stone * (1 - lichen[..., None] * 0.5) + np.array([0.58, 0.60, 0.42]) * lichen[..., None] * 0.5
    stone *= np.clip(1.15 - (np.arange(W)[None, :] - (cx - sw / 2)) / sw * 0.35, 0.75, 1.15)[..., None]
    img = img * (1 - m[..., None]) + stone * dim * m[..., None]
    y = top + sw * 0.42
    for txt, size in lines:
        t = _text_mask(H, W, txt, (cx, y), SERIF, int(size * scale), anchor='mm') * m
        hi = np.roll(t, 2, axis=0)
        img = comp(img, np.array((0.80, 0.80, 0.76)) * dim, np.clip(hi - t, 0, 1) * 0.6)
        img = comp(img, np.array((0.22, 0.21, 0.20)) * dim, t * 0.85)
        y += size * scale * 1.45
    return img


def stake(img, x, y, h=120, dim=1.0):
    m = mask_poly(H, W, [(x - 4, y), (x + 4, y), (x + 3, y - h), (x - 3, y - h)])
    img = comp(img, np.array((0.55, 0.45, 0.30)) * dim, m)
    flag = mask_poly(H, W, [(x + 3, y - h), (x + 46, y - h + 10), (x + 3, y - h + 24)])
    band = (np.sin(np.arange(W)[None, :] * 0.4) > 0).astype(np.float32)
    img = comp(img, np.array((0.80, 0.16, 0.12)) * dim, flag * band)
    img = comp(img, np.array((0.90, 0.88, 0.84)) * dim, flag * (1 - band))
    return img


def ilgin(img, x, y, s=1.0, seed=0):
    r = rng(seed)
    stem = mask_poly(H, W, [(x, y), (x + 120 * s, y - 40 * s), (x + 122 * s, y - 36 * s), (x + 2, y + 4)])
    img = comp(img, (0.30, 0.22, 0.16), stem)
    for k in range(60):
        t = r.uniform(0.3, 1.0)
        px, py = x + 120 * s * t + r.normal(0, 8 * s), y - 40 * s * t + r.normal(0, 8 * s)
        img = comp(img, (0.86, 0.48, 0.62) if r.random() < 0.7 else (0.40, 0.48, 0.30), mask_ellipse(H, W, px, py, 5 * s, 4 * s, blur=0.8))
    return img


def c_mezar(variant='aksam'):
    aksam = variant == 'aksam'
    img = sky_dusk(H, W, 61, [(0, (0.20, 0.24, 0.36)), (0.5, (0.46, 0.44, 0.50)), (0.7, (0.78, 0.58, 0.46)), (0.8, (0.82, 0.62, 0.48))]) if aksam \
        else vgrad(H, W, [(0, (0.58, 0.62, 0.66)), (0.6, (0.74, 0.75, 0.76)), (1, (0.80, 0.80, 0.78))])
    dim = 0.55 if aksam else 1.0
    img = mountains(img, [(600, 170, np.array((0.40, 0.40, 0.46)) * (1 if aksam else 1.3), 520, 0.4)], seed=111)
    ground = tint(fbm(H, W, 20, 6, 112), (0.24, 0.22, 0.17), (0.42, 0.38, 0.28)) * dim
    gm = (np.arange(H)[:, None] > 700).astype(np.float32) * np.ones((1, W))
    img = img * (1 - gm[..., None]) + ground * gm[..., None]
    r = rng(5)
    for i in range(22):  # açılmış çukurlar ve toprak yığınları
        cy = r.uniform(740, 1250)
        sc = (cy - 680) / 400
        cx = r.uniform(0, W)
        img = comp(img, np.array((0.14, 0.11, 0.08)) * dim, mask_ellipse(H, W, cx, cy, 90 * sc, 26 * sc, blur=2))
        img = comp(img, np.array((0.36, 0.30, 0.22)) * dim, mask_ellipse(H, W, cx + 110 * sc, cy - 10 * sc, 70 * sc, 34 * sc, blur=3))
        if r.random() < 0.6:
            img = stake(img, cx - 70 * sc, cy, 100 * sc, dim)
    for i in range(4):
        img = round_tree(img, r.uniform(1700, 2400), 720 + r.uniform(0, 30), r.uniform(80, 120), np.array((0.18, 0.22, 0.13)) * dim, 900 + i)
    img = gravestone(img, 1150, 1080, 260, 420, [('ORHAN AKIN', 30), ('1962 – 1987', 24), ('ÖĞRETMEN', 22)], 113, dim)
    img = ilgin(img, 1060, 1085, 1.3, 114)
    img = depth_blur(img, np.clip((700 - np.arange(H)[:, None]) / 60, 0, 1) * np.ones((1, W)), 1.5)
    return phone_photo(img, 61, grain=0.035 if aksam else 0.022, vignette=0.4, sharpen=0.4, soft=0.9, noise_dark=1.4)


def photo_mezar():
    """Yakın çekim: mezar taşı, tarih ve dibinde ılgın dalı (4:3)."""
    img = vgrad(H, W, [(0, (0.58, 0.62, 0.66)), (1, (0.76, 0.76, 0.74))])
    ground = tint(fbm(H, W, 16, 6, 121), (0.24, 0.22, 0.17), (0.44, 0.40, 0.30))
    gm = (np.arange(H)[:, None] > 560).astype(np.float32) * np.ones((1, W))
    img = img * (1 - gm[..., None]) + ground * gm[..., None]
    img = depth_blur(img, np.clip((560 - np.arange(H)[:, None]) / 40, 0, 1) * np.ones((1, W)), 6)
    img = gravestone(img, 1200, 1250, 700, 1120, [('ORHAN AKIN', 74), ('1962 – 1987', 56), ('ÖĞRETMEN', 50), ('', 30), ('Ö. 14.06.1987', 46), ('RUHUNA FATİHA', 40)], 122, 1.0, 1.0)
    img = ilgin(img, 860, 1260, 3.2, 123)
    img = stake(img, 1720, 1300, 520, 1.0)
    img = light(img, 0.8 + 0.35 * radial(H, W, 900, 300, 2000, 1600, 1.0), (1.02, 1.0, 0.97))
    return phone_photo(img, 62, grain=0.022, vignette=0.35, sharpen=0.5, soft=0.7, contrast=1.06)


def photo_liste():
    """Kamyonetin torpidosunda daktilo yazısı bir liste (4:3, 2400×1350'de çizilip kırpılır)."""
    img = tint(fbm(H, W, 14, 4, 131), (0.10, 0.10, 0.11), (0.20, 0.20, 0.21))
    paper = np.ones((1000, 820, 3), np.float32) * np.array([0.92, 0.91, 0.88])
    paper *= (0.94 + 0.08 * fbm(1000, 820, 40, 3, 132))[..., None]
    pa = Image.fromarray((paper * 255).astype(np.uint8)).convert('RGBA')
    from PIL import ImageDraw, ImageFont
    d = ImageDraw.Draw(pa)
    f = ImageFont.truetype(MONO, 19)
    fb = ImageFont.truetype(MONO, 22)
    d.text((60, 60), 'T.C. ILGIN BARAJI KAMULAŞTIRMA BİRİMİ', font=fb, fill=(30, 30, 34))
    d.text((60, 96), 'ILGINDERE KÖYÜ MEZAR NAKİL LİSTESİ', font=fb, fill=(30, 30, 34))
    rows = [('24', 'Yıldız, Hasan', '1931-2004', 'Ailesi - Kayseri', 'TAŞINDI'),
            ('25', 'Yıldız, Fadime', '1936-2011', 'Ailesi - Kayseri', 'TAŞINDI'),
            ('26', 'Kaya, Mustafa', '1940-1998', 'Ailesi - Ankara', 'TAŞINDI'),
            ('27', 'Doğan, Ahmet', '1922-1993', 'Ailesi - Ankara', 'TAŞINDI'),
            ('28', 'Doğan, Zehra', '1928-1999', 'Ailesi - Ankara', 'TAŞINDI'),
            ('29', 'Sarı, İbrahim', '1919-1990', 'Ailesi - Sivas', 'TAŞINDI'),
            ('30', 'Akın, Orhan', '1962-1987', 'Öğretmen', 'SAHİPSİZ')]
    y = 170
    d.line([(60, y - 10), (760, y - 10)], fill=(60, 60, 64), width=2)
    for row in rows:
        d.text((60, y), f'{row[0]}  {row[1]:<16}{row[2]}  {row[3]}', font=f, fill=(34, 34, 38))
        d.text((640, y), row[4], font=f, fill=(34, 34, 38) if row[4] == 'TAŞINDI' else (150, 20, 20))
        y += 44
    d.text((60, y + 6), '    Ölüm: 14.06.1987 - boğulma (Ilgındere köprüsü)', font=f, fill=(34, 34, 38))
    d.text((60, y + 50), '    Kimsesizler mezarlığına nakli: İl Müd.', font=f, fill=(34, 34, 38))
    d.ellipse([560, y - 60, 790, y + 40], outline=(40, 70, 160), width=4)
    canvas = to_pil(img).convert('RGBA')
    canvas.alpha_composite(warp_rgba(pa, (W, H), [(780, 120), (1660, 170), (1620, 1260), (720, 1200)]))
    img = from_pil(canvas)
    img = light(img, 0.55 + 0.7 * radial(H, W, 1200, 600, 1300, 900, 1.2), (1.0, 0.98, 0.94))
    big = phone_photo(img, 63, grain=0.03, vignette=0.45, sharpen=0.4, soft=0.8, noise_dark=1.3)
    return big


EXTRA_FRAMES['c_mezar'] = lambda: c_mezar('aksam')
EXTRA_SCENES['gun4_son'] = {
    'baslik': 'Mezarlık',
    'ses': 'sinema/gun4_son.ogg',
    'kapak': 'sinema/c_mezar.jpg',
    'kareler': [
        ('c_mezar', 9.5, [0.30, 1.04], [0.50, 1.18], [(0.6, 4.6, 'Köyün mezarları taşındı. Biri hariç.'),
                                                     (4.8, 9.2, 'Orhan Akın. 1962–1987. Öğretmen.')]),
        ('c_gece', 6.0, [0.40, 1.05], [0.36, 1.12], [(0.5, 5.6, 'O gece postanede bir fener uzun süre yandı.')]),
        (None, 4.5, [0.5, 1], [0.5, 1], [(0.4, 4.3, '5. gün · İtiraf')]),
    ],
}


# ---------------------------------------------------------------- 5. gün
def c_meydan(variant='aksam'):
    """Meydan suyun altında: kulenin dibi suda, kapıları çarpılı evler, suda yansımalar."""
    aksam = variant == 'aksam'
    img = sky_dusk(H, W, 71, [(0, (0.18, 0.22, 0.36)), (0.45, (0.42, 0.42, 0.52)), (0.62, (0.80, 0.58, 0.46)), (0.7, (0.86, 0.64, 0.48))]) if aksam \
        else vgrad(H, W, [(0, (0.56, 0.61, 0.67)), (0.6, (0.74, 0.76, 0.78)), (1, (0.80, 0.80, 0.79))])
    dim = 0.6 if aksam else 1.0
    img = mountains(img, [(640, 200, np.array((0.40, 0.40, 0.48)) * (1 if aksam else 1.3), 520, 0.4),
                          (700, 150, np.array((0.30, 0.28, 0.30)) * (1 if aksam else 1.4), 420, 0.3)], seed=72)
    r = rng(9)
    items = [(80, 640, 420, 260, 501, True), (560, 680, 300, 200, 502, True), (1580, 670, 360, 230, 503, True), (1980, 630, 420, 270, 504, False)]
    img = cluster_houses(img, items, dim)
    img = put_tower(img, [(1060, 150), (1300, 144), (1330, 900), (1030, 906)], dim, warm_top=0.3 if aksam else 0.0)
    # su: kulenin ve evlerin alt kısmını örter
    wy = 860
    img = water(img, wy, H, None, 10, (0.22, 0.20, 0.18) if aksam else (0.42, 0.40, 0.34), 0.5, 73)
    # suda yüzen bir sandalye ve dallar
    img = comp(img, np.array((0.30, 0.24, 0.18)) * dim, mask_poly(H, W, [(700, 1000), (780, 1000), (790, 1010), (690, 1012)]))
    img = comp(img, np.array((0.30, 0.24, 0.18)) * dim, mask_poly(H, W, [(706, 960), (716, 960), (716, 1002), (706, 1002)]))
    for i in range(12):
        x, y = r.uniform(0, W), r.uniform(900, 1300)
        img = comp(img, np.array((0.20, 0.17, 0.13)) * dim, mask_poly(H, W, [(x, y), (x + r.uniform(40, 120), y + r.uniform(-8, 8)), (x + 2, y + 3)]))
    if aksam:
        return phone_photo(img, 74, grain=0.03, vignette=0.4, sharpen=0.35, soft=0.9, noise_dark=1.3)
    return phone_photo(img, 75, grain=0.022, vignette=0.3, sharpen=0.45, soft=0.8, contrast=1.05)


EXTRA_FRAMES['c_meydan'] = lambda: c_meydan('aksam')
EXTRA_SCENES['gun5_son'] = {
    'baslik': 'Meydan',
    'ses': 'sinema/gun5_son.ogg',
    'kapak': 'sinema/c_meydan.jpg',
    'kareler': [
        ('c_meydan', 9.5, [0.40, 1.02], [0.55, 1.16], [(0.6, 4.4, 'Su meydana ulaştı.'), (4.6, 9.2, 'O gece, yıllardır ilk kez, çan çalmadı.')]),
        ('c_degirmen', 6.0, [0.50, 1.10], [0.50, 1.02], [(0.5, 5.6, 'Değirmende soba sabaha kadar yandı.')]),
        (None, 4.5, [0.5, 1], [0.5, 1], [(0.4, 4.3, '6. gün · Nazlı')]),
    ],
}


# ---------------------------------------------------------------- 6. gün
def rain(img, amount=0.35, seed=0, angle=0.25):
    r = rng(seed)
    m = np.zeros((H, W), np.float32)
    n = 2600
    xs = r.uniform(0, W, n)
    ys = r.uniform(0, H, n)
    ln = r.uniform(30, 90, n)
    from PIL import ImageDraw
    im = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(im)
    for x, y, l in zip(xs, ys, ln):
        d.line([(x, y), (x + l * angle, y + l)], fill=int(r.uniform(60, 160)), width=1)
    m = np.asarray(im, np.float32) / 255
    m = ndimage.gaussian_filter(m, 0.6)
    return img * (1 - m[..., None] * amount) + np.array([0.75, 0.78, 0.82]) * m[..., None] * amount


def c_firtina():
    """Fırtına gecesi: kabarmış dere, yağmur, değirmenin yanan penceresi."""
    img = vgrad(H, W, [(0, (0.05, 0.06, 0.09)), (0.5, (0.10, 0.12, 0.16)), (0.66, (0.16, 0.17, 0.21))])
    cl = fbm(H, W, 260, 6, 141, aspect=(0.4, 1.0))
    img *= (0.7 + 0.6 * cl)[..., None]
    img = mountains(img, [(620, 160, (0.08, 0.09, 0.12), 520, 0.0)], seed=142)
    img = mill(img, 1300, 860, 380, 250, 13, 0.22, lit_window=True, lantern=False)
    wy = 860
    flow = plane(fbm(1024, 1024, 26, 5, 143, aspect=(0.1, 1.0)), wy, 800, 90, 1.0)
    w = tint(flow, (0.05, 0.05, 0.06), (0.20, 0.20, 0.22))
    foam = np.clip((plane(fbm(1024, 1024, 10, 4, 144, aspect=(0.12, 1.0)), wy, 800, 90, 1.0) - 0.6) * 3, 0, 1)
    w = w * (1 - foam[..., None] * 0.6) + np.array([0.45, 0.46, 0.48]) * foam[..., None] * 0.6
    img[wy:] = w
    refl = np.exp(-((np.arange(W)[None, :] - 1440) / 26) ** 2) * np.clip(1 - (np.arange(H)[:, None] - wy) / 260, 0, 1) * (np.arange(H)[:, None] > wy)
    ff = np.zeros((H, W), np.float32)
    ff[wy:] = flow
    img += refl[..., None] * np.array([0.40, 0.22, 0.06]) * (0.4 + 0.8 * ff)[..., None]
    img = rain(img, 0.35, 145)
    return phone_photo(img, 146, grain=0.04, vignette=0.5, sharpen=0.25, soft=1.1, noise_dark=1.6)


EXTRA_FRAMES['c_firtina'] = c_firtina
EXTRA_SCENES['gun6_son'] = {
    'baslik': 'Fırtına',
    'ses': 'sinema/gun6_son.ogg',
    'kapak': 'sinema/c_firtina.jpg',
    'kareler': [
        ('c_firtina', 10.0, [0.55, 1.04], [0.62, 1.18], [(0.6, 4.6, 'Gece fırtına koptu.'), (5.0, 9.6, 'Su saatte bir karış yükseldi.')]),
        ('c_meydan', 5.5, [0.48, 1.12], [0.48, 1.20], [(0.4, 5.2, 'Saat kulesinin kapısı artık suyun altındaydı.')]),
        (None, 4.5, [0.5, 1], [0.5, 1], [(0.4, 4.3, '7. gün · Son Çan')]),
    ],
}


# ---------------------------------------------------------------- 7. gün ve sonlar
def boat(img, x, y, s=1.0, dim=1.0, lantern=True, people=3):
    hull = mask_poly(H, W, [(x - 120 * s, y), (x + 120 * s, y), (x + 95 * s, y + 26 * s), (x - 95 * s, y + 26 * s)])
    img = comp(img, np.array((0.20, 0.14, 0.09)) * dim, hull)
    for k in range(people):
        px = x - 60 * s + k * 60 * s
        body = mask_poly(H, W, [(px - 14 * s, y), (px + 14 * s, y), (px + 10 * s, y - 50 * s), (px - 10 * s, y - 50 * s)])
        body = np.maximum(body, mask_ellipse(H, W, px, y - 62 * s, 10 * s, 11 * s))
        img = comp(img, np.array((0.06, 0.06, 0.07)), body)
    if lantern:
        img = glow(img, x + 100 * s, y - 40 * s, 140 * s, (0.85, 0.45, 0.12), 0.8)
        img = glow(img, x + 100 * s, y - 40 * s, 14 * s, (1.0, 0.85, 0.5), 1.4)
    return img


def c_son_can():
    """Gece: kule suyun ortasında, postanenin penceresinin önünde fenerli bir kayık."""
    img = vgrad(H, W, [(0, (0.03, 0.04, 0.09)), (0.5, (0.08, 0.10, 0.17)), (0.62, (0.16, 0.16, 0.24))])
    img = stars(img, 2200, 15)
    img = mountains(img, [(700, 200, (0.07, 0.08, 0.11), 520, 0.0), (760, 150, (0.05, 0.05, 0.07), 420, 0.0)], seed=151)
    img = put_tower(img, [(1060, 150), (1300, 144), (1330, 900), (1030, 906)], 0.25)
    post = mask_poly(H, W, [(1340, 720), (1700, 720), (1700, 900), (1340, 900)])
    img = comp(img, (0.06, 0.06, 0.07), post)
    img = comp(img, (0.30, 0.18, 0.06), mask_poly(H, W, [(1420, 780), (1480, 780), (1480, 840), (1420, 840)]) * 0.8)
    wy = 860
    img = water(img, wy, H, None, 12, (0.03, 0.035, 0.06), 0.55, 152)
    img = boat(img, 1520, 900, 1.0, 0.3)
    refl = np.exp(-((np.arange(W)[None, :] - 1620) / 24) ** 2) * np.clip(1 - (np.arange(H)[:, None] - 930) / 300, 0, 1) * (np.arange(H)[:, None] > 930)
    img += refl[..., None] * np.array([0.45, 0.24, 0.06]) * (0.5 + 0.8 * fbm(H, W, 10, 3, 153, aspect=(0.05, 1.0)))[..., None]
    return phone_photo(img, 154, grain=0.04, vignette=0.5, sharpen=0.25, soft=1.0, noise_dark=1.6)


def c_safak():
    """Şafak: durgun göl, yalnızca kulenin çatısı sudan çıkıyor, uzakta küçük bir kayık."""
    img = vgrad(H, W, [(0, (0.42, 0.52, 0.66)), (0.4, (0.70, 0.72, 0.78)), (0.56, (0.96, 0.84, 0.70)), (0.6, (0.98, 0.88, 0.74))])
    img = glow(img, 1500, 780, 900, (0.30, 0.16, 0.05), 1.0)
    img = mountains(img, [(720, 200, (0.56, 0.58, 0.66), 600, 0.5), (780, 150, (0.44, 0.43, 0.46), 420, 0.3)], seed=161)
    roof = mask_poly(H, W, [(1110, 812), (1180, 740), (1250, 812)])
    img = comp(img, (0.30, 0.18, 0.13), roof)
    img = comp(img, (0.40, 0.36, 0.32), mask_poly(H, W, [(1120, 812), (1240, 812), (1240, 822), (1120, 822)]))
    img = mist(img, 810, 30, 0.6, (0.94, 0.90, 0.84), 6)
    img = water(img, 822, H, None, 3, (0.60, 0.62, 0.66), 0.15, 162)
    img = boat(img, 1800, 900, 0.45, 0.4, lantern=False)
    return phone_photo(img, 163, grain=0.02, vignette=0.32, warm=0.03, sharpen=0.3, soft=1.0, contrast=1.04)


EXTRA_FRAMES['c_son_can'] = c_son_can
EXTRA_FRAMES['c_safak'] = c_safak
EXTRA_SCENES['son_can'] = {
    'baslik': 'Son Çan',
    'ses': 'sinema/son_can.ogg',
    'kapak': 'sinema/c_son_can.jpg',
    'kareler': [
        ('c_son_can', 11.0, [0.50, 1.10], [0.58, 1.02], [(0.6, 5.0, 'Dokuzu on geçe, Ilgındere’de son kez çan çaldı.'),
                                                       (5.4, 10.6, 'Bu sefer gelmesi için değil. Gitmesi için.')]),
        ('c_safak', 10.0, [0.45, 1.12], [0.55, 1.02], [(0.6, 4.8, 'Sabah göl durgundu.'), (5.0, 9.6, 'Saat kulesinin yalnızca çatısı görünüyordu.')]),
        (None, 6.0, [0.5, 1], [0.5, 1], [(0.4, 5.8, 'Son Çan')]),
    ],
}
EXTRA_SCENES['son_kuru'] = {
    'baslik': 'Kuru Toprak',
    'ses': 'sinema/son_kuru.ogg',
    'kapak': 'sinema/c_safak.jpg',
    'kareler': [
        ('c_baraj', 8.0, [0.70, 1.10], [0.62, 1.02], [(0.6, 7.6, 'Ilgın Barajı’nın gölü yedinci günün gecesi doldu.')]),
        ('c_safak', 9.0, [0.48, 1.04], [0.52, 1.14], [(0.6, 4.4, 'Ilgındere suyun altında kaldı.'), (4.6, 8.6, 'O gece çan çalmadı.')]),
        (None, 5.0, [0.5, 1], [0.5, 1], [(0.4, 4.8, 'Kuru Toprak')]),
    ],
}
EXTRA_SCENES['son_sinyal'] = {
    'baslik': 'Sinyal Yok',
    'ses': 'sinema/son_sinyal.ogg',
    'kapak': 'sinema/c_telefon.jpg',
    'kareler': [
        ('c_telefon', 7.0, [0.47, 1.05], [0.47, 1.20], [(0.6, 6.6, 'Telefon ikinci kez suya düştü.')]),
        ('c_safak', 9.0, [0.48, 1.04], [0.52, 1.14], [(0.6, 4.4, 'Ilgındere suyun altında kaldı.'), (4.6, 8.6, 'Son çan hiç çalınmadı.')]),
        (None, 5.0, [0.5, 1], [0.5, 1], [(0.4, 4.8, 'Sinyal Yok')]),
    ],
}
