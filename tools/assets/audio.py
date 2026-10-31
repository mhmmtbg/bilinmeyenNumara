"""Oyunun bütün sesleri burada sentezlenir (kayıt dosyası yok, tamamen kodla üretilir).

Çıktı:
  www/ses/<anahtar>.ogg      Elif'in gönderdiği ses kayıtları (mono, Opus)
  www/ses/ses.json           süre ve dalga formu (baloncuk çizimi için)
  www/sinema/<anahtar>.ogg   sinematik müzik ve ortam sesleri (stereo, Opus)

Kullanım: python3 tools/assets/audio.py
"""
import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 44100
ROOT = Path(__file__).resolve().parents[2]
rng = np.random.default_rng(1987)


# ---------------------------------------------------------------- temel araçlar
def secs(s):
    return int(round(s * SR))


def silence(d):
    return np.zeros(secs(d))


def white(n):
    return rng.standard_normal(n)


def brown(n):
    x = np.cumsum(white(n))
    x = signal.lfilter([1], [1, -0.999], np.diff(x, prepend=0))
    x -= signal.savgol_filter(x, 4001 if n > 4001 else (n // 2) * 2 - 1, 1) if n > 50 else 0
    return x / (np.abs(x).max() + 1e-9)


def pink(n):
    # Voss benzeri: beyaz gürültüye 1/f eğimi
    b = [0.049922035, -0.095993537, 0.050612699, -0.004408786]
    a = [1, -2.494956002, 2.017265875, -0.522189400]
    x = signal.lfilter(b, a, white(n))
    return x / (np.abs(x).max() + 1e-9)


def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], btype='band', fs=SR, output='sos')
    return signal.sosfilt(sos, x)


def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype='low', fs=SR, output='sos'), x)


def hp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype='high', fs=SR, output='sos'), x)


def env_adsr(n, a, r, curve=1.0):
    e = np.ones(n)
    na, nr = min(secs(a), n), min(secs(r), n)
    if na:
        e[:na] = np.linspace(0, 1, na) ** curve
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr) ** curve
    return e


def reverb(x, t60=2.2, mix=0.35, pre=0.02, bright=4000):
    n = secs(t60)
    t = np.arange(n) / SR
    ir = white(n) * np.exp(-6.9 * t / t60)
    ir = lp(ir, bright)
    ir[: secs(pre)] = 0
    ir /= np.sqrt(np.sum(ir ** 2)) + 1e-9
    wet = signal.fftconvolve(x, ir)[: len(x)]
    return (1 - mix) * x + mix * wet * 0.9


def place(dst, src, at, gain=1.0):
    i = secs(at)
    j = min(len(dst), i + len(src))
    if j > i:
        dst[i:j] += src[: j - i] * gain
    return dst


def normalize(x, peak=0.89):
    m = np.abs(x).max()
    return x * (peak / m) if m > 0 else x


# ---------------------------------------------------------------- ses kaynakları
def bell_strike(base=392.0, dur=6.0, bright=1.0):
    """Kule çanı: çan partiyelleri (hum, prime, tierce, quint, nominal...) ve hafif vuruşma."""
    n = secs(dur)
    t = np.arange(n) / SR
    partials = [  # oran, genlik, sönüm süresi (s)
        (0.5, 0.55, 5.5), (1.0, 0.75, 3.8), (1.19, 0.45, 2.9), (1.50, 0.30, 2.4),
        (2.0, 0.60 * bright, 2.1), (2.51, 0.22 * bright, 1.4), (2.66, 0.18 * bright, 1.2),
        (3.01, 0.20 * bright, 0.9), (4.07, 0.10 * bright, 0.6), (5.2, 0.06 * bright, 0.35),
    ]
    out = np.zeros(n)
    for r, a, d in partials:
        f = base * r
        beat = 1 + 0.08 * np.sin(2 * np.pi * (0.7 + r * 0.31) * t)
        out += a * beat * np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28)) * np.exp(-t / d)
    # tokmağın çarpması: kısa metalik vuruş, her vuruşu ayrı duyurur
    k = secs(0.03)
    out[:k] += hp(white(k), 1800) * np.exp(-np.arange(k) / SR / 0.006) * 1.4
    for r, a in ((6.3, 0.35), (7.9, 0.25), (9.4, 0.18)):
        out += a * np.sin(2 * np.pi * base * r * t) * np.exp(-t / 0.12)
    return out * env_adsr(n, 0.002, 0.05)


def crickets(n, density=1.0, far=1.0):
    out = np.zeros(n)
    t_all = np.arange(n) / SR
    for _ in range(int(5 * density)):
        f = rng.uniform(3900, 5200)
        rate = rng.uniform(1.6, 3.2)       # cıvıltı / sn
        pulses = rng.integers(3, 6)
        phase = rng.uniform(0, 1)
        gate = ((t_all * rate + phase) % 1.0)
        on = (gate < 0.16 * pulses / 4).astype(float)
        trem = 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * pulses / 0.16 * rate * t_all))
        tone = np.sin(2 * np.pi * f * t_all) * on * trem
        out += lp(tone, 7000) * rng.uniform(0.2, 1.0)
    out = reverb(out, 1.2, 0.5)
    return out * 0.035 * far


def wind(n, strength=1.0, low=180, high=900):
    x = bp(pink(n), low, high)
    mod = lp(np.abs(white(n)), 0.25, 1)
    mod = 0.35 + 0.65 * (mod / (mod.max() + 1e-9))
    return normalize(x * mod, 1.0) * 0.09 * strength


def river(n, strength=1.0):
    x = bp(white(n), 300, 5000) * 0.6 + bp(pink(n), 80, 600) * 0.8
    burble = 0.7 + 0.3 * np.abs(lp(white(n), 6))
    burble /= burble.max()
    return normalize(x * burble, 1.0) * 0.12 * strength


def breath(n_secs, period=3.6, gain=1.0, start=0.4):
    n = secs(n_secs)
    out = np.zeros(n)
    t = start
    while t < n_secs - 1.5:
        inh = secs(rng.uniform(0.9, 1.3))
        exh = secs(rng.uniform(1.0, 1.5))
        a = bp(white(inh), 900, 3800) * np.sin(np.linspace(0, np.pi, inh)) ** 1.5 * 0.55
        b = bp(white(exh), 400, 2200) * np.sin(np.linspace(0, np.pi, exh)) ** 1.2 * 0.75
        place(out, a, t)
        place(out, b, t + inh / SR + 0.15)
        t += period * rng.uniform(0.85, 1.15)
    return out * 0.05 * gain


def room_tone(n):
    return lp(pink(n), 1200) * 0.012 + hp(white(n), 6000) * 0.002


def hum_voice(notes, f_scale=1.0):
    """Uzaktan mırıldanan bir kadın sesi: titreşimli gırtlak sinyali + burun formantları.
    notes: [(frekans, süre)]; 0 frekans = es."""
    parts = []
    phase = 0.0
    for f0, d in notes:
        n = secs(d)
        t = np.arange(n) / SR
        if f0 <= 0:
            parts.append(np.zeros(n))
            continue
        vib = 1 + 0.012 * np.sin(2 * np.pi * 5.3 * t) * np.clip(t / 0.4, 0, 1)
        inst = f0 * f_scale * vib
        ph = phase + 2 * np.pi * np.cumsum(inst) / SR
        phase = ph[-1]
        src = sum((1 / k ** 1.6) * np.sin(k * ph) for k in range(1, 18))
        e = env_adsr(n, min(0.12, d / 3), min(0.25, d / 3), 1.4)
        parts.append(src * e)
    x = np.concatenate(parts)
    # /m/ sesi: düşük birinci formant, burun antirezonansı ~ 1 kHz
    y = bp(x, 180, 420) * 1.0 + bp(x, 2100, 2700) * 0.12 + bp(x, 600, 900) * 0.25
    return normalize(y, 1.0)


def pluck(freq, dur, bright=0.5, gain=1.0):
    """Karplus-Strong ile bağlama benzeri tel sesi."""
    n = secs(dur)
    p = max(2, int(SR / freq))
    buf = (rng.uniform(-1, 1, p) * (0.6 + bright)).tolist()
    out = np.zeros(n)
    idx = 0
    damp = 0.4975 + 0.002 * bright
    for i in range(n):
        v = buf[idx]
        out[i] = v
        nxt = buf[(idx + 1) % p]
        buf[idx] = damp * (v + nxt)
        idx = (idx + 1) % p
    body = bp(out, 180, 3200) + lp(out, 300) * 0.4
    return body * env_adsr(n, 0.001, 0.3) * gain


def drone(n, f=55.0, gain=1.0):
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.5 * t + 1) + 0.25 * np.sin(2 * np.pi * f * 2.003 * t)
    x *= 0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * t)
    return lp(x, 400) * 0.06 * gain


def splash(gain=1.0):
    n = secs(1.6)
    t = np.arange(n) / SR
    x = hp(white(n), 900) * np.exp(-t / 0.18)
    x += bp(white(n), 120, 900) * np.exp(-t / 0.35) * 0.8
    for _ in range(14):  # kabarcıklar
        d = secs(rng.uniform(0.03, 0.08))
        tt = np.arange(d) / SR
        f0 = rng.uniform(500, 1600)
        b = np.sin(2 * np.pi * f0 * (1 + 3 * tt) * tt) * np.exp(-tt / 0.02)
        place(x, b * 0.4, rng.uniform(0.15, 1.2))
    return x * gain


def underwater(n):
    return lp(brown(n), 350) * 0.25 + lp(pink(n), 500) * 0.1


def footsteps_gravel(times, gain=1.0):
    out = np.zeros(secs(max(times) + 1))
    for t in times:
        d = secs(0.16)
        g = bp(white(d), 1200, 7000) * np.exp(-np.arange(d) / SR / 0.04)
        g += bp(white(d), 150, 600) * np.exp(-np.arange(d) / SR / 0.03) * 0.6
        place(out, g, t)
    return out * gain


def phone_buzz(gain=1.0):
    n = secs(0.9)
    t = np.arange(n) / SR
    g = ((t % 0.45) < 0.32).astype(float)
    x = np.sin(2 * np.pi * 170 * t) * (0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 34 * t))) * g
    return lp(x, 900) * gain


# Uşşak makamına yakın dizi (La karar; Si yarım bemol)
LA3 = 220.0
def cents(c):
    return 2 ** (c / 1200)
USSAK = {'la': LA3, 'si': LA3 * cents(150), 'do': LA3 * cents(300), 're': LA3 * cents(500),
         'mi': LA3 * cents(700), 'fa': LA3 * cents(800), 'sol': LA3 * cents(1000), 'la2': LA3 * 2,
         'sol_': LA3 * cents(-200), 'mi_': LA3 * cents(-500)}


# ---------------------------------------------------------------- Elif'in ses kayıtları
def rec_can1():
    """0:22 — Okul penceresinden, uzaktan çan: dokuz vuruş, sessizlik, on vuruş. Elif'in nefesi."""
    D = 22.0
    n = secs(D)
    bells = np.zeros(n)
    t = 0.9
    for i in range(9):
        place(bells, bell_strike(392 * rng.uniform(0.997, 1.003), 6.0), t, 0.9)
        t += 0.98
    t += 1.6
    for i in range(10):
        place(bells, bell_strike(392 * rng.uniform(0.997, 1.003), 6.0), t, 0.9)
        t += 0.98
    far = lp(bells, 2600)
    far = reverb(far, t60=3.4, mix=0.55, pre=0.06)
    mix = far * 0.5
    mix += crickets(n, 0.8) + wind(n, 0.25) + room_tone(n) * 1.5
    mix += breath(D, 3.4, 1.4, 1.2)
    # telefonun tutuşu: kısa elle oynama sesi başta ve sonda
    for at in (0.15, D - 0.7):
        k = secs(0.25)
        place(mix, bp(white(k), 200, 1800) * np.hanning(k) * 0.06, at)
    mix *= env_adsr(n, 0.05, 0.4)
    return mix


def rec_mirilti():
    """0:09 — Kaydın bir parçası: çanın son yankısı ve altında uzak bir kadın mırıltısı."""
    D = 9.0
    n = secs(D)
    tail = np.zeros(n)
    tl = bell_strike(392, 9.0)[secs(1.2):]
    place(tail, reverb(lp(tl, 2400), 3.4, 0.55), 0, 0.45)
    u = USSAK
    melody = [(u['la'], 0.7), (u['si'], 0.45), (u['do'], 0.9), (u['re'], 0.55), (u['do'], 0.45),
              (u['si'], 0.5), (u['la'], 1.1), (0, 0.25), (u['sol_'], 0.45), (u['la'], 0.6), (u['si'], 0.5), (u['la'], 0.4)]
    v = hum_voice(melody, 1.0)
    v = bp(v, 200, 2400)
    v = reverb(v, 2.8, 0.6, 0.08)
    voice = np.zeros(n)
    place(voice, v, 1.4, 0.22)
    cut = secs(8.1)              # "sonra kesiliyor"
    voice[cut:] *= np.exp(-np.arange(n - cut) / SR / 0.05)
    mix = tail * 0.8 + voice + crickets(n, 0.5) * 0.45 + room_tone(n) * 2.2 + hp(white(n), 3000) * 0.004
    mix *= env_adsr(n, 0.08, 0.3)
    return mix


# ---------------------------------------------------------------- sinematik ses bandı
def stereo(l, r=None, width=0.0):
    if r is None:
        r = l
    return np.stack([l * (1 - width) + r * width, r * (1 - width) + l * width], 1)


def pan(x, p):
    """p: -1 sol, +1 sağ"""
    a = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], 1)


def melody_plucks(seq, start, tempo=0.9, gain=0.5, p=0.0, total=None):
    """seq: [(nota_adı, vuruş)]"""
    out = np.zeros((secs(total), 2))
    t = start
    for name, beats in seq:
        if name:
            pl = pluck(USSAK[name], min(3.5, beats * tempo + 1.6), 0.45, gain)
            out[secs(t): secs(t) + len(pl)] += pan(pl, p + rng.uniform(-0.15, 0.15))[: len(out) - secs(t)]
        t += beats * tempo
    return out


def cine_prolog():
    """Prolog (~38 sn): baraj uğultusu, rüzgâr, dere, bağlama; köprüde düşen telefon ve su altı."""
    D = 38.0
    n = secs(D)
    out = np.zeros((n, 2))
    # zemin: düşük baraj uğultusu ve drone
    out += stereo(drone(n, 49, 1.2) * env_adsr(n, 3, 3))
    out += stereo(wind(n, 0.9), wind(n, 0.9), 0.0) * env_adsr(n, 2, 2)[:, None]
    # dere: 7. saniyeden itibaren yükselir, telefon düşünce kesilir
    rv = river(n, 1.0)
    renv = np.clip((np.arange(n) / SR - 6) / 6, 0, 1)
    renv[secs(25.0):] *= np.exp(-np.arange(n - secs(25.0)) / SR / 0.15)
    out += stereo(rv * renv * 1.6, river(n, 1.0) * renv * 1.6)
    # bağlama ezgisi (özgün)
    seq = [('la', 2), ('si', 1), ('do', 1), ('re', 2), ('do', 1), ('si', 1), ('la', 3), (None, 1),
           ('do', 1), ('re', 1), ('mi', 2), ('re', 1), ('do', 1), ('si', 2), ('la', 3)]
    out += melody_plucks(seq, 2.5, 0.78, 0.55, -0.1, D) * env_adsr(n, 0.1, 14)[:, None]
    # ayak sesleri köprüde (15-21 sn)
    steps = footsteps_gravel([15.2 + i * 0.58 for i in range(10)], 0.05)
    out[secs(0): secs(0) + len(steps)] += pan(steps, 0.2)
    # ayak kayıyor (ıslak taşta sürtünme), nefes kesilmesi, sonra sıçrama 24.4 sn
    k = secs(0.45)
    scrape = bp(white(k), 600, 4000) * np.sin(np.linspace(0, np.pi, k)) ** 0.7 * 0.35
    out[secs(23.75): secs(23.75) + k] += pan(scrape, 0.1)
    g = secs(0.35)
    gasp = bp(white(g), 900, 3500) * np.sin(np.linspace(0, np.pi, g)) ** 2 * 0.18
    out[secs(23.95): secs(23.95) + g] += stereo(gasp)
    out[secs(24.4): secs(24.4) + secs(1.6)] += stereo(splash(0.55))
    # su altı (26-32 sn) — boğuk uğultu
    uw = underwater(secs(6.0)) * env_adsr(secs(6.0), 0.1, 1.8)
    out[secs(26.0): secs(26.0) + len(uw)] += stereo(uw * 1.3)
    # karanlık: tek bir telefon titreşimi (33 sn)
    out[secs(33.4): secs(33.4) + secs(0.9)] += stereo(phone_buzz(0.18))
    out = reverb_st(out, 1.6, 0.18)
    return out * env_adsr(n, 0.5, 0.8)[:, None]


def cine_gun1_son():
    """Gün 1 sonu (~22 sn): gece, cırcır böcekleri, uzak çan yankısı, sabah su."""
    D = 22.0
    n = secs(D)
    out = np.zeros((n, 2))
    night = np.clip(1 - (np.arange(n) / SR - 9) / 2.5, 0, 1)
    out += stereo(crickets(n, 1.2) * 1.4 * night, crickets(n, 1.2) * 1.4 * night)
    out += stereo(drone(n, 55, 1.0) * env_adsr(n, 2, 3))
    far = np.zeros(n)
    place(far, reverb(lp(bell_strike(392, 7), 1800), 4.0, 0.7), 1.0, 0.18)
    out += pan(far, -0.4)
    # sabah: su sesi, kuş
    morning = np.clip((np.arange(n) / SR - 9.5) / 2, 0, 1) * env_adsr(n, 0.1, 5)
    lap = bp(pink(n), 120, 1400) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.35 * np.arange(n) / SR)) * 0.10
    out += stereo(lap * morning, bp(pink(n), 120, 1400) * morning * 0.08)
    seq = [('mi', 2), ('re', 1), ('do', 1), ('si', 2), ('la', 4)]
    out += melody_plucks(seq, 10.5, 0.85, 0.45, 0.1, D)
    out = reverb_st(out, 1.8, 0.2)
    return out * env_adsr(n, 0.6, 1.2)[:, None]


def cine_gun2_son():
    """Gün 2 sonu (~20 sn): köprünün üstünden dökülen su, gece, uzak fener, tel."""
    D = 20.0
    n = secs(D)
    out = np.zeros((n, 2))
    roar = np.clip(1 - (np.arange(n) / SR - 7.5) / 2.0, 0, 1)
    out += stereo(river(n, 2.2) * roar, river(n, 2.2) * roar)
    out += stereo(bp(brown(n), 40, 200) * 0.25 * roar)
    night = np.clip((np.arange(n) / SR - 7.5) / 1.5, 0, 1) * env_adsr(n, 0.1, 4)
    out += stereo(crickets(n, 1.0) * 1.2 * night, crickets(n, 1.0) * 1.2 * night)
    out += stereo(river(n, 0.5) * night)
    out += stereo(drone(n, 52, 1.1) * env_adsr(n, 2, 3))
    seq = [('la', 2), ('do', 1), ('si', 1), ('la', 2), (None, 1), ('sol_', 1), ('la', 3)]
    out += melody_plucks(seq, 8.5, 0.85, 0.45, -0.1, D)
    out = reverb_st(out, 1.8, 0.2)
    return out * env_adsr(n, 0.6, 1.2)[:, None]


def rec_kopru_sesi():
    """0:12 — köprünün üstünden akan suyun gürültüsü, yakın; ortada Elif'in kısık sesi yok, sadece bir öksürük/nefes."""
    D = 12.0
    n = secs(D)
    x = river(n, 2.6) + bp(brown(n), 40, 220) * 0.35 + hp(white(n), 2500) * 0.03
    for _ in range(30):  # taşlara çarpan su
        place(x, bp(white(secs(0.08)), 800, 6000) * np.hanning(secs(0.08)) * 0.08, rng.uniform(0, D - 0.2))
    x += breath(D, 4.0, 1.0, 2.0) * 0.8
    k = secs(0.3)
    place(x, bp(white(k), 200, 1800) * np.hanning(k) * 0.08, 0.1)
    return x * env_adsr(n, 0.08, 0.4)


def rec_kiyi():
    """0:14 — gece dere kıyısı: güçlü akış, çanın son yankısı, karşı yakadan kısık mırıltı."""
    D = 14.0
    n = secs(D)
    x = river(n, 1.6) + crickets(n, 0.6) * 0.6
    tl = bell_strike(392, 8.0)[secs(1.5):]
    place(x, reverb(lp(tl, 2000), 3.6, 0.65), 0, 0.22)
    u = USSAK
    melody = [(u['re'], 0.6), (u['do'], 0.45), (u['si'], 0.6), (u['la'], 1.0), (0, 0.3), (u['la'], 0.5), (u['si'], 0.45),
              (u['do'], 0.8), (u['si'], 0.5), (u['la'], 1.2), (0, 0.4), (u['sol_'], 0.5), (u['la'], 1.0)]
    v = reverb(bp(hum_voice(melody), 220, 2000), 2.6, 0.65, 0.1)
    place(x, v, 3.0, 0.16)
    return x * env_adsr(n, 0.1, 0.6)


def crackle(n, rate=6.0, gain=1.0):
    """Soba çıtırtısı: rastgele kısa tıkırtılar."""
    x = np.zeros(n)
    t = 0.0
    D = n / SR
    while t < D - 0.05:
        k = secs(rng.uniform(0.003, 0.012))
        place(x, hp(white(k), 1500) * np.exp(-np.arange(k) / SR / 0.003) * rng.uniform(0.1, 0.6), t)
        t += rng.exponential(1 / rate)
    return x * gain + lp(pink(n), 300) * 0.02 * gain


def rec_hatice():
    """0:16 — değirmenin içi: soba, yakından yaşlı bir kadının mırıltısı (aynı ezgi), örgü şişleri."""
    D = 16.0
    n = secs(D)
    x = crackle(n, 5, 1.0) + room_tone(n) * 2
    u = USSAK
    melody = [(u['la'], 0.8), (u['si'], 0.5), (u['do'], 1.0), (u['re'], 0.6), (u['do'], 0.5), (u['si'], 0.6), (u['la'], 1.3),
              (0, 0.4), (u['sol_'], 0.5), (u['la'], 0.7), (u['si'], 0.6), (u['la'], 1.2), (0, 0.5),
              (u['do'], 0.7), (u['re'], 0.6), (u['mi'], 1.0), (u['re'], 0.6), (u['do'], 0.6), (u['si'], 1.4)]
    v = hum_voice(melody, 0.93)
    v = reverb(bp(v, 150, 3000), 0.6, 0.2, 0.01)
    place(x, v, 1.0, 0.5)
    for t in np.arange(0.6, D - 0.5, 0.42):  # örgü şişlerinin tıkırtısı
        k = secs(0.01)
        place(x, bp(white(k), 3000, 8000) * 0.05, t + rng.uniform(-0.05, 0.05))
    return x * env_adsr(n, 0.1, 0.5)


def cine_gun3_son():
    """Gün 3 sonu (~20 sn): değirmen gecesi, soba, uzak çan, gece."""
    D = 20.0
    n = secs(D)
    out = np.zeros((n, 2))
    out += stereo(crickets(n, 1.0) * 1.2, crickets(n, 1.0) * 1.2)
    out += stereo(river(n, 0.6) * env_adsr(n, 1, 3))
    out += stereo(drone(n, 49, 1.0) * env_adsr(n, 2, 3))
    far = np.zeros(n)
    t = 9.6
    for i in range(9):
        place(far, lp(bell_strike(392, 5.0), 1600), t, 0.12)
        t += 0.98
    out += pan(reverb(far, 4.0, 0.7), -0.3)
    seq = [('la', 2), ('si', 1), ('do', 2), ('si', 1), ('la', 3)]
    out += melody_plucks(seq, 1.5, 0.9, 0.4, 0.1, D)
    out = reverb_st(out, 1.8, 0.2)
    return out * env_adsr(n, 0.6, 1.2)[:, None]


def creak(dur=0.5, gain=1.0):
    """Tahta/ip gıcırtısı: hızla titreşen dar bant sürtünme."""
    n = secs(dur)
    t = np.arange(n) / SR
    f = 300 + 180 * np.sin(2 * np.pi * 1.3 * t)
    pulses = (np.sin(2 * np.pi * np.cumsum(f) / SR * 0.12) > 0.6).astype(float)
    x = bp(white(n), 500, 2500) * pulses * np.hanning(n)
    return x * gain


def whisper(dur=1.4, gain=1.0):
    """Anlaşılmaz bir fısıltı: hece hece şekillenmiş gürültü."""
    n = secs(dur)
    x = np.zeros(n)
    t = 0.05
    while t < dur - 0.15:
        k = secs(rng.uniform(0.08, 0.2))
        syl = bp(white(k), rng.uniform(1200, 2200), rng.uniform(3500, 6000)) * np.hanning(k)
        place(x, syl * rng.uniform(0.5, 1.0), t)
        t += k / SR + rng.uniform(0.02, 0.08)
    return x * gain


def rec_postane():
    """0:24 — postanenin içinden, çok yakından: ip gıcırtısı, 9+10 vuruş, sonunda fısıltı."""
    D = 24.0
    n = secs(D)
    x = room_tone(n) * 2.5
    t = 0.8
    for k in range(19):
        if k == 9:
            t += 1.5
        place(x, creak(0.35, 0.10), t - 0.25)
        place(x, lp(bell_strike(392 * rng.uniform(0.998, 1.002), 5.0), 4500), t, 0.55)
        t += 0.98
    x = reverb(x, 1.6, 0.35)
    place(x, whisper(1.3, 0.05), 21.6)
    x += breath(D, 3.2, 0.7, 1.0)
    return x * env_adsr(n, 0.05, 0.4)


def cine_gun4_son():
    """Gün 4 sonu (~20 sn): rüzgârlı mezarlık, sonra postanede tek çan yankısı."""
    D = 20.0
    n = secs(D)
    out = np.zeros((n, 2))
    out += stereo(wind(n, 1.4), wind(n, 1.4))
    out += stereo(drone(n, 46, 1.2) * env_adsr(n, 2, 3))
    out += stereo(crickets(n, 0.6) * np.clip((np.arange(n) / SR - 9) / 2, 0, 1))
    far = np.zeros(n)
    place(far, reverb(lp(bell_strike(392, 7.0), 2200), 3.5, 0.6), 10.2, 0.25)
    out += pan(far, -0.2)
    seq = [('mi', 2), ('re', 1), ('do', 1), ('si', 2), ('do', 1), ('si', 1), ('la', 4)]
    out += melody_plucks(seq, 1.0, 0.95, 0.42, 0.0, D)
    out = reverb_st(out, 1.8, 0.2)
    return out * env_adsr(n, 0.6, 1.2)[:, None]


def reverb_st(x, t60, mix):
    return np.stack([reverb(x[:, 0], t60, mix), reverb(x[:, 1], t60 * 1.07, mix)], 1)


# ---------------------------------------------------------------- yazma
def loudness(x, rms_target):
    """Ortalama ses düzeyini hedefe getirir, tepeleri yumuşak sınırlar (tek bir sıçrama her şeyi kısmasın)."""
    rms = np.sqrt(np.mean(x ** 2)) + 1e-9
    x = x * (rms_target / rms)
    return np.tanh(x * 1.1) / np.tanh(1.1) * 0.92


def write_ogg(path, x, mono=True, bitrate='64k', rms=0.14):
    x = loudness(x, rms)
    with tempfile.NamedTemporaryFile(suffix='.wav') as f:
        wavfile.write(f.name, SR, (x * 32767).astype(np.int16))
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', f.name, '-c:a', 'libopus', '-b:a', bitrate,
                        '-ac', '1' if mono else '2', str(path)], check=True)


def peaks(x, bars=44):
    x = np.abs(x if x.ndim == 1 else x.mean(1))
    chunks = np.array_split(x, bars)
    v = np.array([np.sqrt(np.mean(c ** 2)) for c in chunks])
    v = v / (v.max() + 1e-9)
    return [round(float(max(0.08, a ** 0.6)), 2) for a in v]


RECORDINGS = {'can1': rec_can1, 'mirilti': rec_mirilti, 'kopru_sesi': rec_kopru_sesi, 'kiyi': rec_kiyi, 'hatice': rec_hatice, 'postane': rec_postane}
CINEMA = {'prolog': cine_prolog, 'gun1_son': cine_gun1_son, 'gun2_son': cine_gun2_son, 'gun3_son': cine_gun3_son, 'gun4_son': cine_gun4_son}


def main():
    meta = {}
    for key, fn in RECORDINGS.items():
        x = fn()
        write_ogg(ROOT / 'www/ses' / f'{key}.ogg', x, mono=True, bitrate='48k')
        meta[key] = {'sure': round(len(x) / SR, 2), 'dalga': peaks(x)}
        print(f'ses/{key}.ogg  {len(x) / SR:.1f} sn')
    (ROOT / 'www/ses/ses.json').write_text(json.dumps(meta, ensure_ascii=False))
    for key, fn in CINEMA.items():
        x = fn()
        write_ogg(ROOT / 'www/sinema' / f'{key}.ogg', x, mono=False, bitrate='96k')
        print(f'sinema/{key}.ogg  {len(x) / SR:.1f} sn')


if __name__ == '__main__':
    main()
