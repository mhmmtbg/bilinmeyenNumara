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
| `kule.jpg` | Alacakaranlıkta, aşağıdan çekilmiş taş saat kulesi. Saat 9:10'da durmuş. Yanlarda kapıları kırmızı çarpılı kerpiç evler, elektrik direği ve telleri. |
| `duvar.jpg` | Flaşla çekilmiş, boyası dökülmüş mavi kapı kasası; kurşun kalemle boy çizgileri ve isimler: Kemal 1971, Nazlı 1973, Kemal 1974, Nazlı 1976, Kemal 1978, Nazlı 1981, Kemal 1983. |

Sinematik kareler için de aynısı geçerli: `www/sinema/c_baraj.jpg` gibi aynı adla 16:9 bir görüntü koyman yeter. Altyazı ve zamanlamalar `tools/assets/cinema.py` içindeki `SCENES` tablosundadır.
