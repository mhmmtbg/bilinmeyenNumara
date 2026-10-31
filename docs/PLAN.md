# Bilinmeyen Numara — Faaliyet Planı

Önce hikâye ve his doğru kurulur; reklam, satın alma ve Play Store en son gelir.

## Aşama 1 — Temel (bu sürüm)

| # | İş | Durum |
| --- | --- | --- |
| 1.1 | Hikâye anayasası (`docs/HIKAYE.md`): karakterler, sır katmanları, 7 gün, sonlar | ✅ |
| 1.2 | Senaryo dili (`.hikaye`) ve ayrıştırıcı | ✅ |
| 1.3 | Gerçek zamanlı senaryo motoru: gecikmeler, `@21:10` saat beklemeleri, kapalıyken ilerleme, kayıt | ✅ |
| 1.4 | Mesajlaşma arayüzü: yazıyor…, seçenekler, yazarak cevap, fotoğraf ve ses kaydı baloncukları, pil göstergesi | ✅ |
| 1.5 | Gün 1 senaryosu (tam, dallanan) | ✅ |
| 1.6 | Android (Capacitor 8) + yerel bildirimler (uygulama kapalıyken mesaj gelir) | ✅ |
| 1.7 | GitHub Actions: senaryo doğrulama + test APK'sı → `son-derleme` sürümü | ✅ |
| 1.8 | Geliştirici test hızı (×10, ×60, ×600, bekleme atla) | ✅ |

## Aşama 2 — Hikâyenin tamamı (onaydan sonra)

| # | İş |
| --- | --- |
| 2.1 | Gün 1 için oynanış geri bildirimi → ince ayar (tempo, ton, seçenek sayısı) |
| 2.2 | Gün 2–3 senaryosu (Bekçi, Değirmen) + defter bulmacası |
| 2.3 | Gün 4–5 (Kamulaştırma, İtiraf) + gerçek zamanlı gizlenme sahnesi |
| 2.4 | Gün 6–7 (Nazlı, Son Çan) + dört son |
| 2.5 | Senaryo denetçisi: her dal bir sona ulaşıyor mu, ölü düğüm var mı, en kısa / en uzun gerçek süre |
| 2.6 | Fotoğraf çizimleri (defter, kule, duvar, değirmen, tutanak…) |
| 2.7 | Sonlar arşivi ve "hikâyeyi baştan başlat" |

## Aşama 3 — His ve cila

| # | İş |
| --- | --- |
| 3.1 | Ses: bildirim tonu, gerçek ses kayıtları (çan, dere, rüzgâr) — ses baloncukları çalınabilir olur |
| 3.2 | Titreşim (Haptics), yazıyor animasyonu ince ayarı |
| 3.3 | Başlıktaki "son görülme", gün ayraçları, su seviyesi göstergesi |
| 3.4 | Ekran testleri (küçük/büyük ekran, yazı boyutu, açık/koyu tema) |
| 3.5 | İngilizce çeviri altyapısı |

## Aşama 4 — Gelir ve yayın

| # | İş |
| --- | --- |
| 4.1 | **Geri sar:** son seçime dön (ödüllü reklam ya da ücretli sürümde sınırsız) |
| 4.2 | **Beklemeyi atla:** uzun beklemeyi bitir (ödüllü reklam; günde sınırlı) |
| 4.3 | Reklam yalnızca gün aralarında; hikâye sahnesinin ortasında asla |
| 4.4 | Tek seferlik satın alma: reklamsız + sınırsız geri sarma + sonlar arşivi |
| 4.5 | İleride: yeni "numaralar" (ikinci hikâye) uygulama içi içerik olarak |
| 4.6 | Gizlilik politikası, Play Console, kapalı test, yayın |

## Mimari

```
www/
  index.html          giriş ekranı + sohbet ekranı + ayarlar
  css/                tokens.css (renkler), style.css (düz, gölgesiz)
  js/
    parser.js         .hikaye metnini düğümlere çevirir (saf fonksiyon)
    engine.js         gerçek zamanlı ilerleme (saf fonksiyon, zaman parametre olarak verilir)
    story.js          senaryo dosyalarını yükler ve birleştirir
    save.js           kayıt (localStorage)
    notify.js         yerel bildirim planlama (Capacitor varsa)
    photos.js         fotoğraf baloncuklarındaki SVG çizimler
    ui.js             sohbet ekranı
    main.js           başlatma, uygulama ön/arka plan olayları
    features.js       özellik bayrakları (geliştirici modu, reklam, satın alma)
  hikaye/
    gun1.hikaye …     senaryo dosyaları
tools/
  check-story.mjs     senaryo denetçisi (CI'da çalışır)
  test-engine.mjs     motor testleri
```

### Zaman modeli

Motor "şimdi"yi parametre olarak alır ve o ana kadar olması gereken her şeyi oynatır. Bu sayede:

- Uygulama kapalıyken geçen zaman açılışta yakalanır (mesajlar gerçek gönderim saatleriyle görünür).
- Uygulama arka plana geçerken motor geleceği **kopya bir durum üzerinde** simüle eder ve gelecek mesajlar için yerel bildirim kurar.
- Testlerde zaman tamamen kontrol edilebilir.

## Senaryo dili (`.hikaye`)

| Satır | Anlamı |
| --- | --- |
| `=== dugum_adi` | Düğüm başlangıcı. Düğümün sonunda atlama yoksa sıradaki düğüme geçilir. |
| `Metin` | Ece'den mesaj (yazma süresi uzunluğa göre otomatik) |
| `Nazlı: metin` | Başka bir konuşmacıdan mesaj |
| `>> metin` | Sistem notu (ortada, gri) |
| `~ 30sn` · `~ 5dk` · `~ 2sa` | Bekleme |
| `~ @21:10` · `~ @08:40 en az 6sa` | Oyuncunun yerel saatiyle bir sonraki 21:10'a kadar bekle |
| `* Seçenek -> hedef` | Oyuncu seçeneği (art arda satırlar bir seçim grubu). `* [guven>=3] Seçenek -> hedef` koşullu |
| `?? İpucu` + `= cevap1|cevap2 -> hedef` + `= * -> hedef` | Oyuncu yazarak cevap verir |
| `$ guven + 1` · `$ fener_gordu = 1` | Değişken |
| `? guven >= 5 -> hedef` | Koşullu atlama |
| `-> hedef` | Atlama |
| `!foto anahtar \| alt yazı` | Fotoğraf baloncuğu |
| `!ses 0:14 \| döküm` | Ses kaydı baloncuğu |
| `!pil 41` · `!ad Ece` · `!durum çevrimdışı` · `!gun 2 Bekçi` | Başlık ve durum |
| `!son anahtar \| Sonun adı` · `!ara` | Son / yazılmamış bölüm sınırı |

Koşullarda `saat` değişkeni Ece'nin o anki yerel saatidir (0–23).
