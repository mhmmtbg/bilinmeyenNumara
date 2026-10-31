# Bilinmeyen Numara

Gerçek zamanlı bir mesajlaşma macera oyunu (Android).

Telefonuna bilinmeyen bir numaradan mesaj gelir: Elif, dedesinin defterindeki numaraya yazmıştır ve baraj suları altında kalmak üzere olan bir köyde, Ilgındere'de, mahsur kalmıştır. Hikâye senin saatinle akar; Elif "yarım saate yazarım" derse gerçekten yarım saat sonra yazar, mesajları bildirim olarak gelir. Her cevabın hikâyeyi değiştirir.

## Belgeler

- [Hikâye kurgusu](docs/HIKAYE.md): karakterler, sır katmanları, 7 gün, sonlar
- [Faaliyet planı](docs/PLAN.md): aşamalar, mimari, senaryo dili

## Geliştirme

```bash
npm ci
npm test          # motor testleri + senaryo denetimi (bütün dallar)
npm run serve     # http://localhost:8080 — tarayıcıda oyna
```

Senaryo `www/hikaye/*.hikaye` dosyalarındadır (dil tanımı: `docs/PLAN.md`). Geliştirme sürümünde ayarlardaki **Test araçları** ile zamanı hızlandırabilir (×10–×600), beklemeyi atlayabilir ve son seçimi geri alabilirsin.

## Derleme

`main` dalına her gönderimde GitHub Actions senaryoyu doğrular, test APK'sını derler ve **son-derleme** sürümüne koyar. APK her seferinde aynı test anahtarıyla imzalanır; eskisinin üstüne kurulur.
