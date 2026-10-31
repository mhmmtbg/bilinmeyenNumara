# Görseller, sesler ve sinematikler

Oyundaki bütün fotoğraflar, sinematik kareler ve sesler **kodla üretilir**; dışarıdan alınmış görüntü ya da kayıt yoktur. Üreten betikler `tools/assets/` altındadır:

| Betik | Ürettiği |
| --- | --- |
| `audio.py` | `www/ses/*.ogg` (Ece'nin ses kayıtları), `www/sinema/*.ogg` (sinematik ses bantları), `www/ses/ses.json` (süre, dalga formu) |
| `photos.py` | `www/img/foto/*.jpg` (Ece'nin gönderdiği fotoğraflar, 1200×900) |
| `cinema.py` | `www/sinema/c_*.jpg` (panoramik kareler, 1920×1080) ve `www/sinema/sinema.json` (sahne akışı, altyazılar) |

```bash
npm run assets          # hepsini yeniden üret (photos.py var olan fotoğrafların üzerine yazmaz)
python3 tools/assets/photos.py kule --zorla   # tek bir fotoğrafı yeniden üret
```

Gerekenler: Python 3, numpy, scipy, Pillow, ffmpeg (libopus). El yazısı fontları (Caveat, Kalam — SIL OFL) `tools/assets/fonts/` içindedir.

## Gerçek fotoğrafla değiştirmek

Bir fotoğrafı gerçeğiyle değiştirmek için aynı adla `www/img/foto/` içine koy (4:3, en az 1200×900, JPEG). Oyun hiçbir değişiklik gerektirmeden onu kullanır.

| Dosya | Çekim |
| --- | --- |
| `defter.jpg` | Ahşap masada açık bir defter sayfası, gün ışığı soldan. Tükenmez kalemle el yazısı: "Ilgındere'de başın sıkışırsa / bu numaraya yaz. O bilir." Altında "05" ile başlayıp su lekesiyle dağılmış bir numara, en altta altı çizili "Saat dokuzu geçe." ve "— K." |
| `kule.jpg`, `kule_gun.jpg`, `kule_gece.jpg` | Aşağıdan çekilmiş taş saat kulesi (alacakaranlık / bulutlu öğle / gece el feneri ışığında). Saat 9:10'da durmuş, kapısı zincirli. Yanlarda kapıları kırmızı çarpılı kerpiç evler, elektrik direği ve telleri. Oyun, Ece'nin o anki saatine uyanı gösterir. |
| `defter2.jpg` | Defterin başka bir sayfası: "Notu oku. Kelime, harf." altında iki satır sayı çifti (1-6 1-7 1-3 8-2 / 1-8 5-3 1-9 5-1), "Unutma." ve üstü çizili ama okunan "Ona söylemeliydim". Sayılar değişirse 2. gün şifresi bozulur. |
| `kopru_su.jpg` | Akşamüstü, üstünden su dökülen eski taş köprü; korkuluk taşları sudan çıkıyor. |
| `duvar.jpg` | Flaşla çekilmiş, boyası dökülmüş mavi kapı kasası; kurşun kalemle boy çizgileri ve isimler: Kemal 1971, Nazlı 1973, Kemal 1974, Nazlı 1976, Kemal 1978, Nazlı 1981, Kemal 1983. |

Sinematik kareler için de aynısı geçerli: `www/sinema/c_baraj.jpg` gibi aynı adla 16:9 bir görüntü koyman yeter. Altyazı ve zamanlamalar `tools/assets/cinema.py` içindeki `SCENES` tablosundadır.
