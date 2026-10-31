"""Elif'in telefonundan "çekilmiş" fotoğraflar. Tamamen prosedürel (dışarıdan görüntü yok).
Çıktı: www/img/foto/<anahtar>.jpg (1200×900)
Gerçek bir fotoğrafla değiştirmek için aynı adla dosyayı www/img/foto/ içine koyman yeter
(bkz. docs/GORSELLER.md); bu betik o zaman --zorla verilmedikçe dosyanın üzerine yazmaz."""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage

from gfx import (FONTS, blur, depth_blur, comp, crack_lines, fbm, from_pil, glow, light, mask_draw, mask_poly, mask_text,
                 phone_photo, plaster, radial, ridge1d, rng, save_jpg, solid, stone_blocks, tint, to_pil, vgrad,
                 warp_rgba, wood)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'www/img/foto'
W, H = 1200, 900


# ---------------------------------------------------------------- defter
def paper_base(pw, ph, seed, back_lines):
    """Çizgili defter kâğıdı: lif, sararma, kenar çizgisi, arka sayfadan sızan yazı."""
    fib = fbm(ph, pw, 3, 3, seed)
    tone = fbm(ph, pw, 260, 4, seed + 1)
    paper = tint(0.75 * tone + 0.25 * fib, (0.83, 0.79, 0.68), (0.95, 0.92, 0.84))
    # kenarlarda sararma
    edge = 1 - radial(ph, pw, pw / 2, ph / 2, pw * 0.72, ph * 0.72, 0.6)
    paper = paper * (1 - 0.12 * edge[..., None]) + np.array([0.70, 0.58, 0.36]) * 0.12 * edge[..., None]
    # çizgiler
    lines = np.zeros((ph, pw), np.float32)
    for i in range(24):
        y = 118 + i * 40
        if y < ph - 20:
            lines[y:y + 2, :] = 1
    lines = ndimage.gaussian_filter(lines, 0.6) * (0.75 + 0.25 * fib)
    paper = comp(paper, (0.55, 0.66, 0.80), lines * 0.55)
    margin = np.zeros((ph, pw), np.float32)
    margin[:, 112:114] = 1
    paper = comp(paper, (0.82, 0.46, 0.44), ndimage.gaussian_filter(margin, 0.6) * 0.6)
    # arka sayfadan sızan yazı (ayna)
    back = np.zeros((ph, pw), np.float32)
    for i, t in enumerate(back_lines):
        back = np.maximum(back, mask_text(ph, pw, t, (150, 300 + i * 120), 'Caveat_400Regular.ttf', 46))
    paper = comp(paper, (0.35, 0.40, 0.55), np.fliplr(ndimage.gaussian_filter(back, 1.6)) * 0.07)
    return paper


def finish_page(paper, pw, ph):
    gutter = np.clip(1 - np.arange(pw) / 120, 0, 1) ** 2
    paper = paper * (1 - 0.35 * gutter)[None, :, None]
    rgba = np.dstack([np.clip(paper, 0, 1), np.ones((ph, pw))])
    return Image.fromarray((rgba * 255).astype(np.uint8), 'RGBA')


def notebook_cipher(pw=820, ph=1080, seed=4):
    """Şifre sayfası: "Notu oku. Kelime, harf." ve sayı çiftleri; altta eski, karalanmış bir satır."""
    paper = paper_base(pw, ph, seed, ['Haziran 12', 'Hastane, kontrol', 'Rıza'])
    F = 'Caveat_600SemiBold.ttf'
    ink = np.zeros((ph, pw), np.float32)
    ink = np.maximum(ink, mask_text(ph, pw, "Notu oku. Kelime, harf.", (132, 162), F, 62, angle=0.7))
    rows = [["1-6", "1-7", "1-3", "8-2"], ["1-8", "5-3", "1-9", "5-1"]]
    for ri, row in enumerate(rows):
        for ci, t in enumerate(row):
            ink = np.maximum(ink, mask_text(ph, pw, t, (150 + ci * 150, 316 + ri * 120), F, 72, angle=float(np.sin(ri * 3 + ci) * 2)))
    ink = np.maximum(ink, mask_text(ph, pw, "Unutma.", (136, 600), F, 56, angle=-0.5))
    # karalanmış satır
    old = mask_text(ph, pw, "Ona söylemeliydim", (140, 760), F, 52, angle=0.3)
    scr = mask_draw(ph, pw, lambda d, ss: [d.line([(130 + k * 5) * ss, (800 - (k % 2) * 34) * ss, (560 + k * 5) * ss, (790 - (k % 2) * 30) * ss], fill=255, width=4 * ss) for k in range(5)])
    ink = np.maximum(ink, np.maximum(old, scr))
    ink_var = 0.78 + 0.22 * fbm(ph, pw, 20, 3, seed + 9)
    ink = ndimage.gaussian_filter(ink, 0.7) * ink_var
    paper = comp(paper, (0.05, 0.09, 0.30), np.clip(ink * 1.25, 0, 1) * 0.96)
    return finish_page(paper, pw, ph)


def notebook_page(pw=820, ph=1080, seed=3):
    """Defter sayfası (RGBA): kâğıt lifi, çizgiler, mürekkep el yazısı, su lekesiyle dağılmış numara."""
    paper = paper_base(pw, ph, seed, ['Mart. İlaçlar sabah ikişer.', 'Ayşe aradı, cumaya gelecek.', 'Dere taşmış derler.', 'Nazlı'])

    # mürekkep
    ink = np.zeros((ph, pw), np.float32)
    F = 'Caveat_600SemiBold.ttf'  # tükenmez kalem
    ink = np.maximum(ink, mask_text(ph, pw, "Ilgındere'de başın sıkışırsa", (128, 162), F, 64, angle=0.8))
    ink = np.maximum(ink, mask_text(ph, pw, "bu numaraya yaz. O bilir.", (132, 242), F, 64, angle=0.6))
    num_mask = mask_text(ph, pw, "05", (150, 368), F, 76)
    rest = mask_text(ph, pw, "3 7  4 1 8  2 9  6 0", (252, 370), F, 76)
    rest = np.maximum(rest, mask_text(ph, pw, "/", (735, 362), F, 70))
    ink = np.maximum(ink, num_mask)
    ink = np.maximum(ink, mask_text(ph, pw, "Saat dokuzu geçe.", (134, 562), F, 62, angle=0.5))
    und = mask_draw(ph, pw, lambda d, ss: d.line([(140 * ss, 650 * ss), (300 * ss, 646 * ss), (470 * ss, 652 * ss)], fill=255, width=3 * ss))
    ink = np.maximum(ink, und)
    ink = np.maximum(ink, mask_text(ph, pw, "— K.", (560, 900), 'Caveat_400Regular.ttf', 54, angle=-2))

    # su lekesi: numaranın geri kalanını dağıtır
    stain_n = fbm(ph, pw, 70, 4, seed + 7)
    ell = radial(ph, pw, 540, 405, 380, 120, 0.6)
    stain = np.clip((stain_n * 0.6 + ell * 1.1 - 0.55) * 5, 0, 1)
    tide = np.clip(ndimage.gaussian_filter(stain, 2) - ndimage.gaussian_filter(stain, 7), 0, None)
    tide = tide / (tide.max() + 1e-9)
    # mürekkep suyla dağılmış: geniş yayılma + aşağı doğru akıntı; rakamlar okunmaz
    run = ndimage.gaussian_filter(rest, (22, 9))
    run = ndimage.shift(run, (14, 0), order=1)
    ghost = np.clip(ndimage.gaussian_filter(rest, 5.5) * 1.15, 0, 0.55)
    wash = np.clip(ndimage.gaussian_filter(rest, 30) * 7 * (0.6 + 0.6 * stain_n), 0, 0.42)
    smear = np.clip(ghost * 0.75 + wash + run * 1.2, 0, 0.8)
    smear = smear * stain + rest * (1 - stain) * 0.15
    ink = np.maximum(ink, smear)

    ink_var = 0.78 + 0.22 * fbm(ph, pw, 20, 3, seed + 9)
    ink = ndimage.gaussian_filter(ink, 0.7) * ink_var
    paper = comp(paper, (0.05, 0.09, 0.30), np.clip(ink * 1.25, 0, 1) * 0.96)
    # lekenin kâğıda etkisi: hafif koyulaşma, kenar halkası, kırışık
    paper *= (1 - 0.07 * stain)[..., None]
    paper = comp(paper, (0.55, 0.50, 0.40), tide * 0.35)
    wr = fbm(ph, pw, 14, 3, seed + 11) - 0.5
    gy, gx = np.gradient(ndimage.gaussian_filter(wr * stain, 2))
    paper *= (1 + (gx - gy) * 3)[..., None]
    return finish_page(paper, pw, ph)


def photo_defter(page_fn=None, seed=21, desk=((0.25, 0.15, 0.08), (0.47, 0.31, 0.18))):
    img = wood(H, W, seed, base=desk[0], light=desk[1])
    # tahta birleşim çizgileri
    for y in (180, 560):
        img[y:y + 3] *= 0.45
    # ikinci sayfa (alttaki) ve defter kapağı
    page = (page_fn or notebook_page)()
    cover = Image.new('RGBA', page.size, (34, 48, 58, 255))
    under = Image.new('RGBA', page.size, (226, 218, 196, 255))
    quad = [(250, 40), (1050, 95), (985, 905), (150, 860)]
    canvas = to_pil(img).convert('RGBA')
    sh = Image.new('L', (W, H), 0)
    ImageDraw.Draw(sh).polygon([(x + 10, y + 14) for x, y in [(236, 34), (1064, 92), (1000, 920), (130, 872)]], fill=110)
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    canvas = Image.composite(Image.new('RGBA', (W, H), (12, 8, 5, 255)), canvas, sh)
    for q, layer in (([(236, 34), (1064, 92), (1000, 920), (130, 872)], cover),
                     ([(244, 38), (1056, 96), (992, 910), (142, 864)], under),
                     (quad, page)):
        canvas.alpha_composite(warp_rgba(layer, (W, H), q))
    img = from_pil(canvas)
    # pencereden gelen gün ışığı (sol üst) ve sağ altta telefonun gölgesi
    lmap = 0.42 + 0.85 * radial(H, W, 300, 120, 1250, 1000, 1.3)
    img = light(img, lmap, (1.04, 1.0, 0.94))
    hand = mask_poly(H, W, [(1200, 600), (1060, 760), (1010, 900), (1200, 900)], blur=40)
    img *= (1 - 0.35 * hand)[..., None]
    return phone_photo(img, 5, grain=0.022, vignette=0.32, warm=0.03, sharpen=0.45, soft=0.7)


# ---------------------------------------------------------------- kapı kasası (yakın çekim, flaşlı)
def photo_duvar():
    r = rng(8)
    img = plaster(H, W, 31, base=(0.80, 0.78, 0.71))
    img *= (0.9 + 0.16 * fbm(H, W, 18, 4, 33))[..., None]
    cr = crack_lines(H, W, 4, 4, 300)
    img = comp(img, (0.40, 0.37, 0.32), cr * 0.55)
    # sol: karanlık mutfak (kapı aralığı)
    dw = 300
    dark = np.ones((H, dw, 3), np.float32) * np.array([0.07, 0.065, 0.06])
    dark *= (0.7 + 0.6 * fbm(H, dw, 200, 3, 2))[..., None]
    img[:, :dw] = dark
    img = comp(img, (0.13, 0.11, 0.09), mask_poly(H, W, [(0, 300), (210, 284), (210, 300), (0, 318)], blur=3))
    # kasa
    cw0, cw1 = 330, 800
    cwid = cw1 - cw0
    base_wood = wood(H, cwid, 41, vertical=True, base=(0.33, 0.28, 0.22), light=(0.50, 0.43, 0.34))
    paint = tint(fbm(H, cwid, 140, 6, 42, aspect=(4.0, 0.25)), (0.46, 0.58, 0.62), (0.58, 0.70, 0.73))
    cluster = np.clip((fbm(H, cwid, 220, 3, 45) - 0.45) * 3, 0, 1)
    chip = np.clip((fbm(H, cwid, 26, 5, 43) - 0.58) * 9, 0, 1) * cluster
    edge_zone = np.clip(1 - np.minimum(np.arange(cwid), cwid - 1 - np.arange(cwid)) / 60, 0, 1)[None, :]
    chip = np.maximum(chip, np.clip((fbm(H, cwid, 30, 5, 44) - 0.5) * 6, 0, 1) * edge_zone)
    casing = paint * (1 - chip[..., None]) + base_wood * chip[..., None]
    edge = np.clip(ndimage.gaussian_filter(chip, 1.0) - chip * 0.9, 0, 1)
    casing = comp(casing, (0.28, 0.32, 0.33), edge * 1.3)
    # el değen yerlerde kir
    grime = radial(H, cwid, cwid * 0.25, 520, cwid * 0.7, 260, 1.2) * (0.6 + 0.4 * fbm(H, cwid, 30, 3, 46))
    casing *= (1 - 0.28 * grime)[..., None]
    img[:, cw0:cw1] = casing
    # kasanın kenar profili (pervaz çıkıntısı)
    img[:, cw0 - 30:cw0] = img[:, cw0 - 30:cw0] * 0.35
    img[:, cw0 - 30:cw0, 2] += 0.02
    img[:, cw0:cw0 + 10] *= np.linspace(0.6, 1.0, 10)[None, :, None]
    img[:, cw1 - 8:cw1] *= np.linspace(1.0, 0.75, 8)[None, :, None]
    img[:, cw1:cw1 + 34] *= (np.linspace(0.38, 1.0, 34) ** 0.6)[None, :, None]
    # boy çizgileri ve isimler (kurşun kalem)
    marks = [(840, 'Kemal 1971'), (768, 'Nazlı 1973'), (690, 'Kemal 1974'), (622, 'Nazlı 1976'),
             (536, 'Kemal 1978'), (478, 'Nazlı 1981'), (402, 'Kemal 1983')]
    pen = np.zeros((H, W), np.float32)
    for i, (y, name) in enumerate(marks):
        y2 = y + int(r.integers(-3, 4))
        x0 = cw0 + 26 + int(r.integers(0, 20))
        x1 = cw0 + 200 + int(r.integers(0, 60))
        pen = np.maximum(pen, mask_draw(H, W, lambda d, ss, y2=y2, x0=x0, x1=x1: d.line([x0 * ss, y2 * ss, x1 * ss, (y2 + int(r.integers(-3, 3))) * ss], fill=255, width=int(3 * ss))))
        pen = np.maximum(pen, mask_text(H, W, name, (x1 + 14, y2 - 30), 'Kalam_400Regular.ttf', 38, angle=float(r.uniform(-3, 3))))
    pen = np.maximum(pen, mask_draw(H, W, lambda d, ss: d.arc([(cw0 + 330) * ss, 250 * ss, (cw0 + 380) * ss, 300 * ss], 20, 320, fill=255, width=3 * ss)))
    pen = np.maximum(pen, mask_draw(H, W, lambda d, ss: d.line([(cw0 + 340) * ss, 320 * ss, (cw0 + 372) * ss, 286 * ss], fill=255, width=3 * ss)))
    graphite = ndimage.gaussian_filter(pen, 0.6) * (0.55 + 0.45 * fbm(H, W, 3, 2, 50))
    img = comp(img, (0.16, 0.16, 0.18), np.clip(graphite * 1.1, 0, 0.92))
    # duvar dibi kiri ve çivi
    dirt = np.clip((np.arange(H) - 760) / 140, 0, 1)[:, None] * (0.5 + 0.5 * fbm(H, W, 40, 3, 60))
    img *= (1 - 0.3 * dirt)[..., None]
    img = comp(img, (0.20, 0.17, 0.14), radial(H, W, 1010, 210, 7, 7, 0.5))
    img = comp(img, (0.45, 0.40, 0.33), mask_poly(H, W, [(1010, 210), (1030, 232), (1028, 236), (1008, 214)], blur=1.5) * 0.4)
    # flaş: hafif sıcak, merkezden uzaklaştıkça kararır; düşük ışıkta gürültü
    fl = 0.42 + 0.95 * radial(H, W, 560, 460, 900, 760, 1.6)
    img = light(img, fl, (1.02, 1.0, 0.95))
    return phone_photo(img, 9, grain=0.028, vignette=0.45, warm=0.025, sharpen=0.55, soft=0.7, noise_dark=1.6, contrast=1.1)


# ---------------------------------------------------------------- saat kulesi (alacakaranlık, aşağıdan)
def clock_face(size=220, seed=1):
    s = size * 3
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([0, 0, s - 1, s - 1], fill=(92, 70, 52, 255))
    d.ellipse([s * .05, s * .05, s * .95, s * .95], fill=(222, 214, 192, 255))
    c = s / 2
    for i in range(60):
        a = i * 6 * np.pi / 180
        r0 = s * (0.40 if i % 5 == 0 else 0.425)
        w = 7 if i % 5 == 0 else 2
        d.line([(c + np.sin(a) * r0, c - np.cos(a) * r0), (c + np.sin(a) * s * 0.44, c - np.cos(a) * s * 0.44)], fill=(40, 34, 30, 255), width=w)

    def hand(deg, L, w):
        a = deg * np.pi / 180
        d.line([(c - np.sin(a) * s * 0.06, c + np.cos(a) * s * 0.06), (c + np.sin(a) * L, c - np.cos(a) * L)], fill=(26, 22, 20, 255), width=w)
    hand((9 + 10 / 60) * 30, s * 0.24, 16)
    hand(60, s * 0.36, 9)
    d.ellipse([c - 12, c - 12, c + 12, c + 12], fill=(26, 22, 20, 255))
    im = im.resize((size, size), Image.LANCZOS)
    a = np.asarray(im, np.float32) / 255
    # leke ve kir
    dirt = fbm(size, size, 30, 4, seed)
    a[..., :3] *= (0.78 + 0.25 * dirt)[..., None]
    streak = np.clip(1 - np.abs(np.linspace(-1, 1, size))[None, :] * 3, 0, 1) * np.linspace(0, 1, size)[:, None]
    a[..., :3] *= (1 - 0.18 * streak)[..., None]
    return Image.fromarray((a * 255).astype(np.uint8), 'RGBA')


def tower_layer(w, h, seed=2, dusk=True):
    """Kule (RGBA, kendi tuvalinde): taş gövde, saat, çan katı, piramit çatı."""
    img = np.zeros((h, w, 3), np.float32)
    alpha = np.zeros((h, w), np.float32)
    bx0, bx1 = int(w * 0.18), int(w * 0.82)
    top_body = int(h * 0.30)
    body = stone_blocks(h, bx1 - bx0, 44, 23, seed, base=(0.66, 0.58, 0.47))
    # sağ yan yüz (hafif perspektif) daha koyu
    img[top_body:, bx0:bx1] = body[top_body:]
    alpha[top_body:, bx0:bx1] = 1
    side = int((bx1 - bx0) * 0.16)
    img[top_body:, bx1 - side:bx1] *= 0.68
    # kornişler
    for y in (top_body, int(h * 0.55)):
        img[y - 8:y + 6, bx0 - 10:bx1 + 10] = (0.58, 0.51, 0.42)
        img[y + 6:y + 12, bx0 - 10:bx1 + 10] = (0.30, 0.26, 0.21)
        alpha[y - 8:y + 12, bx0 - 10:bx1 + 10] = 1
    # çan katı
    bel0 = int(h * 0.12)
    img[bel0:top_body, bx0:bx1] = stone_blocks(top_body - bel0, bx1 - bx0, 44, 23, seed + 1, base=(0.62, 0.55, 0.45))
    alpha[bel0:top_body, bx0:bx1] = 1
    aw = (bx1 - bx0) // 5
    for k in (1, 3):
        ax0 = bx0 + aw * k - aw // 4
        ax1 = ax0 + int(aw * 1.5)
        arch = mask_draw(h, w, lambda d, ss, ax0=ax0, ax1=ax1: (d.rectangle([ax0 * ss, (bel0 + 50) * ss, ax1 * ss, (top_body - 12) * ss], fill=255),
                                                                 d.ellipse([ax0 * ss, (bel0 + 18) * ss, ax1 * ss, (bel0 + 18 + (ax1 - ax0)) * ss], fill=255)))
        img = comp(img, (0.07, 0.07, 0.08), arch)
    # çan (bronz) ortada, açıklıkların arasından görünür
    bcx = (bx0 + bx1) // 2
    bell = mask_draw(h, w, lambda d, ss: d.polygon([((bcx - 34) * ss, (top_body - 30) * ss), ((bcx - 22) * ss, (bel0 + 60) * ss),
                                                    ((bcx + 22) * ss, (bel0 + 60) * ss), ((bcx + 34) * ss, (top_body - 30) * ss)], fill=255))
    img = comp(img, (0.40, 0.28, 0.13), bell * mask_draw(h, w, lambda d, ss: [d.rectangle([(bx0 + aw * k - aw // 4) * ss, (bel0 + 18) * ss, (bx0 + aw * k - aw // 4 + int(aw * 1.5)) * ss, top_body * ss], fill=255) for k in (1, 3)]))
    # çatı
    roof = mask_poly(h, w, [(bx0 - 22, bel0 + 4), (bcx, 0), (bx1 + 22, bel0 + 4)])
    tiles = tint(fbm(h, w, 8, 3, seed + 4, aspect=(1, 0.3)), (0.32, 0.16, 0.10), (0.52, 0.27, 0.17))
    img = img * (1 - roof[..., None]) + tiles * roof[..., None]
    alpha = np.maximum(alpha, roof)
    # saat
    cs = int((bx1 - bx0) * 0.56)
    cf = clock_face(cs, seed + 9)
    cy = int(h * 0.42)
    canvas = Image.fromarray((np.dstack([np.clip(img, 0, 1), alpha]) * 255).astype(np.uint8), 'RGBA')
    canvas.alpha_composite(cf, (bcx - cs // 2 - side // 2, cy - cs // 2))
    # kapı
    a = np.asarray(canvas, np.float32) / 255
    img, alpha = a[..., :3].copy(), a[..., 3].copy()
    dw = int((bx1 - bx0) * 0.28)
    door = mask_draw(h, w, lambda d, ss: (d.rectangle([(bcx - dw // 2 - side // 2) * ss, (h - 200) * ss, (bcx + dw // 2 - side // 2) * ss, h * ss], fill=255),
                                          d.ellipse([(bcx - dw // 2 - side // 2) * ss, (h - 200 - dw // 2) * ss, (bcx + dw // 2 - side // 2) * ss, (h - 200 + dw // 2) * ss], fill=255)))
    img = comp(img, wood(h, w, seed + 7, True, (0.18, 0.12, 0.08), (0.30, 0.21, 0.14)), door)
    # zincir ve asma kilit
    ch = mask_draw(h, w, lambda d, ss: [d.ellipse([(bcx - side // 2 - 50 + i * 14) * ss, (h - 120 + (i % 2) * 3) * ss, (bcx - side // 2 - 36 + i * 14) * ss, (h - 110 + (i % 2) * 3) * ss], outline=255, width=3 * ss) for i in range(7)])
    img = comp(img, (0.32, 0.25, 0.20), ch)
    img = comp(img, (0.36, 0.24, 0.14), mask_poly(h, w, [(bcx - side // 2 - 8, h - 110), (bcx - side // 2 + 12, h - 110), (bcx - side // 2 + 12, h - 84), (bcx - side // 2 - 8, h - 84)]))
    # nem ve kir: alttan yükselen koyuluk, yağmur izleri
    damp = np.clip(1 - (np.arange(h) / h - 0.72) * -3, 0, 1)[:, None] * 0.0
    rain = fbm(h, w, 40, 3, seed + 12, aspect=(4.0, 0.15))
    img *= (0.86 + 0.18 * rain)[..., None]
    img *= np.linspace(1.0, 0.82, h)[:, None, None]
    return img, alpha


def mudbrick_house(w, h, seed, roof=(0.36, 0.29, 0.22), wall=(0.70, 0.60, 0.47), x_mark=True, window=True):
    r = rng(seed)
    img = tint(fbm(h, w, 30, 5, seed), np.asarray(wall) * 0.82, wall)
    straw = fbm(h, w, 2, 2, seed + 1)
    img *= (0.92 + 0.12 * straw)[..., None]
    # düz toprak dam ve uçları
    img[:12] = tint(fbm(12, w, 6, 3, seed + 2), np.asarray(roof) * 0.7, roof)
    img[12:16] *= 0.55
    # direk uçları
    for x in range(10, w - 10, 34):
        img[12:20, x:x + 8] = (0.22, 0.16, 0.11)
    if window:
        wx = int(w * 0.62)
        img[int(h * 0.30):int(h * 0.58), wx:wx + int(w * 0.18)] = (0.07, 0.07, 0.08)
        img[int(h * 0.30):int(h * 0.58), wx + int(w * 0.09) - 2:wx + int(w * 0.09) + 2] = (0.30, 0.24, 0.18)
    dx = int(w * 0.18)
    door_w = int(w * 0.20)
    img[int(h * 0.34):, dx:dx + door_w] = tint(fbm(h - int(h * 0.34), door_w, 8, 3, seed + 3, aspect=(1, 0.2)), (0.22, 0.30, 0.34), (0.35, 0.45, 0.50))
    if x_mark:
        m = mask_draw(h, w, lambda d, ss: (d.line([dx * ss, int(h * 0.38) * ss, (dx + door_w) * ss, int(h * 0.80) * ss], fill=255, width=6 * ss),
                                           d.line([(dx + door_w) * ss, int(h * 0.36) * ss, dx * ss, int(h * 0.82) * ss], fill=255, width=6 * ss)), blur=0.6)
        img = comp(img, (0.70, 0.10, 0.08), m * (0.75 + 0.25 * fbm(h, w, 4, 2, seed + 4)))
    img *= np.linspace(0.92, 1.0, h)[:, None, None]
    return img


def sky_dusk(h, w, seed=0, stops=None):
    stops = stops or [(0, (0.22, 0.30, 0.46)), (0.55, (0.52, 0.55, 0.62)), (0.85, (0.86, 0.66, 0.50)), (1, (0.93, 0.74, 0.55))]
    sky = vgrad(h, w, stops)
    cl = fbm(h, w, 220, 6, seed, aspect=(0.35, 1.0))
    cl = np.clip((cl - 0.52) * 2.2, 0, 1) * np.linspace(1, 0.3, h)[:, None]
    sky = sky * (1 - cl[..., None] * 0.45) + np.array([0.80, 0.66, 0.62]) * cl[..., None] * 0.45
    return sky


def utility_pole(img, x, y_top, y_bot, wires_to, seed=0):
    h, w, _ = img.shape
    pole = mask_poly(h, w, [(x - 6, y_bot), (x - 4, y_top), (x + 4, y_top), (x + 6, y_bot)])
    img = comp(img, (0.18, 0.15, 0.13), pole)
    img = comp(img, (0.18, 0.15, 0.13), mask_poly(h, w, [(x - 40, y_top + 22), (x + 40, y_top + 18), (x + 40, y_top + 26), (x - 40, y_top + 30)]))
    for i, (tx, ty) in enumerate(wires_to):
        sx = x - 34 + i * 34

        def fn(d, ss, sx=sx, tx=tx, ty=ty):
            pts = []
            for t in np.linspace(0, 1, 40):
                px = sx + (tx - sx) * t
                py = (y_top + 22) + (ty - y_top - 22) * t + np.sin(t * np.pi) * 40
                pts.append((px * ss, py * ss))
            d.line(pts, fill=255, width=max(1, int(1.6 * ss)))
        img = comp(img, (0.12, 0.11, 0.11), mask_draw(h, w, fn) * 0.9)
    return img


def photo_kule(variant='aksam'):
    """Saat kulesi; variant: 'gun' (bulutlu öğle), 'aksam' (alacakaranlık), 'gece' (fener/flaş ışığında)."""
    r = rng(91)
    if variant == 'gun':
        img = sky_dusk(H, W, 13, [(0, (0.52, 0.62, 0.74)), (0.5, (0.72, 0.76, 0.80)), (1, (0.84, 0.84, 0.82))])
    elif variant == 'gece':
        img = vgrad(H, W, [(0, (0.02, 0.03, 0.06)), (0.6, (0.05, 0.06, 0.11)), (1, (0.08, 0.08, 0.13))])
        rr = rng(5)
        st = np.zeros((H, W), np.float32)
        n = 900
        st[(rr.random(n) ** 1.3 * 620).astype(int), rr.integers(0, W, n)] = rr.random(n) ** 3 * 2
        img += np.clip(ndimage.gaussian_filter(st, 0.6) * 4, 0, 1)[..., None] * 0.8
    else:
        img = sky_dusk(H, W, 13, [(0, (0.10, 0.15, 0.30)), (0.45, (0.27, 0.32, 0.48)), (0.72, (0.62, 0.48, 0.50)),
                                  (0.86, (0.92, 0.60, 0.40)), (1, (0.96, 0.70, 0.45))])
        img = glow(img, 980, 640, 700, (0.30, 0.14, 0.02), 1.0)
    # uzak dağlar
    mcols = {'gun': [(0.55, 0.57, 0.62), (0.44, 0.45, 0.46)], 'gece': [(0.05, 0.055, 0.08), (0.03, 0.035, 0.05)],
             'aksam': [(0.36, 0.33, 0.42), (0.22, 0.21, 0.27)]}[variant]
    for (base, amp, sd), col in zip([(600, 130, 3), (640, 90, 4)], mcols):
        rid = ridge1d(W, 380, 7, sd, 0.5)
        ys = base - rid * amp
        m = ndimage.gaussian_filter((np.arange(H)[:, None] > ys[None, :]).astype(np.float32), 0.8)
        tex = tint(fbm(H, W, 30, 4, sd + 10), np.asarray(col) * 0.85, col)
        img = img * (1 - m[..., None]) + tex * m[..., None]
    # zemin: toprak yol, tekerlek izleri
    gy0 = 700
    gl = {'gun': ((0.30, 0.26, 0.20), (0.52, 0.45, 0.35)), 'gece': ((0.03, 0.03, 0.03), (0.08, 0.07, 0.06)),
          'aksam': ((0.10, 0.09, 0.08), (0.24, 0.20, 0.16))}[variant]
    ground = tint(fbm(H, W, 30, 6, 70, aspect=(0.4, 1.0)), *gl)
    ruts = np.zeros((H, W), np.float32)
    for xb, xt in ((520, 590), (760, 640)):
        ruts = np.maximum(ruts, mask_poly(H, W, [(xt - 4, gy0), (xt + 4, gy0), (xb + 40, H), (xb - 40, H)], blur=6))
    ground *= (1 - 0.35 * ruts)[..., None]
    gm = (np.arange(H)[:, None] > gy0).astype(np.float32) * np.ones((1, W))
    img = img * (1 - gm[..., None]) + ground * gm[..., None]
    # evler
    hdim = {'gun': 0.88, 'gece': 0.10, 'aksam': 0.42}[variant]
    for (x0, y0, ww, hh, sd) in [(-60, 560, 330, 260, 81), (930, 585, 330, 230, 82), (250, 640, 150, 100, 83)]:
        house = mudbrick_house(ww, hh, sd, x_mark=sd != 83) * hdim
        house *= np.linspace(1.15, 0.7, ww)[None, :, None] if x0 > 600 else np.linspace(0.75, 1.1, ww)[None, :, None]
        xs, xe = max(0, x0), min(W, x0 + ww)
        img[y0:y0 + hh, xs:xe] = house[:H - y0, xs - x0:xe - x0][: H - y0]
    # kule
    tw, th = 300, 760
    t_img, t_a = tower_layer(tw, th, 2)
    if variant == 'aksam':
        lit = np.clip(1.25 - np.linspace(0, 1, th) * 1.15, 0.38, 1.25)[:, None]
        t_img = t_img * lit[..., None] * np.array([1.0, 0.86, 0.72])
        t_img[:, : int(tw * 0.28)] *= 0.55
    elif variant == 'gun':
        t_img = t_img * 0.95
        t_img[:, : int(tw * 0.28)] *= 0.72
    else:
        t_img = t_img * 0.12
    layer = Image.fromarray((np.dstack([np.clip(t_img, 0, 1), t_a]) * 255).astype(np.uint8), 'RGBA')
    canvas = to_pil(img).convert('RGBA')
    tw_layer = warp_rgba(layer, (W, H), [(478, 30), (722, 22), (770, 805), (424, 812)])
    tower_m = np.asarray(tw_layer, np.float32)[..., 3] / 255
    canvas.alpha_composite(tw_layer)
    img = from_pil(canvas)
    img = utility_pole(img * 1.0, 1015, 250, 650, [(0, 330), (-20, 360), (-40, 390)])
    def shrub(d, ss):
        for i in range(90):
            a = r.uniform(-2.7, -0.4)
            L = r.uniform(60, 210)
            x0 = r.uniform(20, 190)
            d.line([(x0 * ss, 905 * ss), ((x0 + np.cos(a) * L) * ss, (905 + np.sin(a) * L) * ss)], fill=255, width=int(r.uniform(1.5, 3.5) * ss))
    shc = {'gun': (0.26, 0.20, 0.15), 'gece': (0.02, 0.02, 0.02), 'aksam': (0.05, 0.045, 0.045)}[variant]
    img = comp(img, shc, mask_draw(H, W, shrub))
    if variant == 'gece':
        # el fenerinin ışığı kulenin gövdesine düşer
        beam = radial(H, W, 600, 560, 330, 420, 1.3) * np.maximum(tower_m, gm * 0.6)
        img = img + img * beam[..., None] * 9.0 * np.array([1.0, 0.92, 0.78]) + beam[..., None] * np.array([0.03, 0.028, 0.022])
    img = depth_blur(img, np.clip((np.arange(H)[:, None] - 820) / 80, 0, 1) * np.ones((1, W)), 2.0)
    if variant == 'gun':
        return phone_photo(img, 13, grain=0.02, vignette=0.25, warm=0.0, sharpen=0.5, soft=0.7, noise_dark=0.8, contrast=1.04)
    if variant == 'gece':
        return phone_photo(img, 13, grain=0.03, vignette=0.5, warm=0.02, sharpen=0.3, soft=1.0, noise_dark=1.6, contrast=1.0)
    return phone_photo(img, 13, grain=0.04, vignette=0.4, warm=0.0, sharpen=0.5, soft=0.8, noise_dark=1.8, contrast=1.05)


def photo_kopru_su():
    """Sinema karesinden (köprü su altında) telefonla çekilmiş 4:3 bir kesit."""
    from cinema import c_kopru
    big = c_kopru(True)
    h, w, _ = big.shape
    cw = int(h * 4 / 3)
    x0 = int(w * 0.5 - cw / 2)
    crop = big[:, x0:x0 + cw]
    return np.asarray(to_pil(crop).resize((W, H), Image.LANCZOS), np.float32) / 255


def photo_crop(frame_fn, cx=0.5):
    """Bir sinema karesinden 4:3 kesit (Elif'in telefonla çektiği hâli)."""
    big = frame_fn()
    h, w, _ = big.shape
    cw = int(h * 4 / 3)
    x0 = int(np.clip(w * cx - cw / 2, 0, w - cw))
    return np.asarray(to_pil(big[:, x0:x0 + cw]).resize((W, H), Image.LANCZOS), np.float32) / 255


def _scene(name, *args):
    import scenes
    return lambda: getattr(scenes, name)(*args)


PHOTOS = {'defter': photo_defter, 'duvar': photo_duvar, 'kule': photo_kule,
          'defter2': lambda: photo_defter(notebook_cipher, 23, ((0.30, 0.24, 0.18), (0.50, 0.42, 0.32))),
          'kopru_su': photo_kopru_su,
          'gecit': lambda: photo_crop(_scene('c_gecit'), 0.45),
          'degirmen': lambda: photo_crop(_scene('c_degirmen', 'gun'), 0.5),
          'mezar': lambda: photo_crop(_scene('photo_mezar'), 0.5),
          'liste': lambda: photo_crop(_scene('photo_liste'), 0.5),
          'kule_gun': lambda: photo_kule('gun'), 'kule_gece': lambda: photo_kule('gece')}


def main():
    force = '--zorla' in sys.argv
    only = [a for a in sys.argv[1:] if not a.startswith('--')]
    for key, fn in PHOTOS.items():
        if only and key not in only:
            continue
        p = OUT / f'{key}.jpg'
        if p.exists() and not force and not only:
            print(f'atlandı (var): {p.name}')
            continue
        save_jpg(fn(), p, 84)
        print(f'img/foto/{key}.jpg  {p.stat().st_size // 1024} KB')


if __name__ == '__main__':
    main()
