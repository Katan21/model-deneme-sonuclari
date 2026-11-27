# Yeni AI modelleri: 8 GB VRAM'de test sonuçları

Ham ölçümler `sonuclar/sonuclar.csv` dosyasında, görseller `sonuclar/files/` klasöründe. Testler tek GPU'lu taşınabilir bir ComfyUI ortamında (eklentisiz, `--vram-headroom 2`) yapıldı.

## Sistem
- Ekran kartı: 8 GB VRAM (cihaz adı verilmiyor), son sürücü
- Kart belleği: toplam 8192 MB, boşta dolu ~1250 MB (Discord + masaüstü dahil; ölçülen tepe değerler buna ~1,2 GB ekler)
- RAM: 32 GB (32678 MB)
- İşlemci: AMD Ryzen 7 5800X (8 çekirdek)
- Disk (deneme klasörü), boş alan: E: SSD (SSDPR-CX400 512 GB), ~355 GB boş → SSD deneme klasörü
- ComfyUI: v0.45.0 portable, BLA bayraklarıyla (`--vram-headroom 2`, eklentisiz)
- İndirme hızı (ölçülen): ~80 MB/s (Hugging Face)

## Modeller
Her model için ilk çalıştırma ve ikinci çalıştırma ayrı yazılır. Süreler `sonuclar/sonuclar.csv`'den; "ilk" soğuk (model ilk kez yükleme dahil), "ikinci" ısınmış çalışmadır.

| model | test | boyut / yüzey | süre ilk / ikinci (sn) | en yüksek kart belleği (MB) | en düşük boş RAM (MB) | sonuç | not |
|---|---|---|---|---|---|---|---|
| mage-flow-turbo | t2i-gol-evi | 1024² | 20,4 / 3,3–14,1 | 5462–5720 | ~8900 | ok | "Göl Evi" tabelası harfi harfine doğru |
| mage-flow-turbo | t2i-gol-evi | 1344×768 | 3,4 / 3,3 | 5558–6008 | ~8950 | ok | |
| mage-flow-turbo | t2i-portre | 1024² | 3,3 | 5688 | ~8960 | ok | portre kalitesi çok iyi (yakın plan yüz, kirli sakal, şapka) |
| mage-flow-turbo | t2i-afis | 1344×768 | 3,3 | 5720 | ~8930 | ok | başlık "Günayin Istahul" (harf hataları), "Şehrin en güzel çayı: 15 ₺" kısmen bozuk ("çary: 15 ¢") |
| mage-flow-edit-turbo | edit-kis | ~1 MP | 20,2 / 3,3 | 5568 | ~9260 | ok | |
| mage-flow-edit-turbo | edit-orgu | ~1 MP | 3,3 | 5565 | ~9220 | ok | şişman/örgü oyuncak yorumu iyi; mermer zemin korundu |
| mage-flow-edit-turbo | edit-tabela | ~1 MP | 3,3 | 5613 | ~9220 | ok | |
| flux2-klein-4b-edit | edit-kis | ~1 MP | 23,8 | 5736 | ~8500 | ok | kar/ışık değişimi mükemmel, yüz korunmuş |
| flux2-klein-4b-edit | edit-orgu | ~1 MP | 13,3 | 5834 | ~8380 | ok | |
| flux2-klein-4b-edit | edit-tabela | ~1 MP | 12,5 | 5930 | ~8410 | ok | |
| flux2-klein-4b-edit-2img | edit-iki-gorsel | ~1 MP | 31,6 | 5537 | ~8530 | ok | iki-görsel ayrı iş akışı; kişi görseli + kıyafet, yüz korunarak giydirildi |
| qwen-image-2.1-turbo | t2i-gol-evi | 1024² | 30,7 / 7,2 | 5510–5695 | ~4670 | ok | |
| qwen-image-2.1-turbo | t2i-portre | 1024² | 9,1 | 5568 | ~5320 | ok | |
| qwen-image-2.1-turbo | t2i-afis | 1344×768 | 9,5 | 5696 | ~5380 | ok | "Günaydın İstanbul" yine bozuk ("Günandin Istanhül") |
| qwen-image-2.1-turbo-edit | edit-kis | ~1 MP | 48,3 | 5384 | ~5150 | ok | |
| qwen-image-2.1-turbo-edit | edit-orgu | ~1 MP | 18,2 | 5450 | ~5080 | ok | |
| qwen-image-2.1-turbo-edit | edit-tabela | ~1 MP | 16,8 | 6170 | ~5000 | ok | |
| qwen-image-2.1-turbo-edit | edit-iki-gorsel | ~1 MP | 28,8 | 5390 | ~5050 | ok | iki-görsel refs ile; yüz tanınabilir kaldı |
| krea2-turbo (int8) | t2i-gol-evi | 1024² | 42,4 / 14,6 | 5567–5603 | ~3400 | ok | 12,6 GB int8 model 8 GB'a sığdı (ağırlık akıtmalı) |
| krea2-turbo (int8) | t2i-portre | 1024² | 16,2 | 5806 | ~3370 | ok | testlerdeki en iyi portre (doku, ışık, arka plan İstanbul) |
| krea2-turbo (int8) | t2i-afis | 1344×768 | 16,5 | 5844 | ~4140 | ok | "Günayydjn Istańbul" (harf hataları); "15 ₺" → "15 $" |
| boogu-turbo (fp8) | t2i-gol-evi | 1024² | 54,7 / 11,6 | 5441–5688 | ~5250 | ok | |
| boogu-turbo (fp8) | t2i-portre | 1024² | 12,4 | 5632 | ~5200 | ok | |
| boogu-turbo (fp8) | t2i-afis | 1344×768 | 12,1 | 5241 | ~5250 | ok | |
| boogu-edit (int8) | edit-kis | ~1 MP | 219,2 | 5231 | ~510 | ok | çok yavaş: qwen3vl-8B metin kodlayıcı + int8, RAM'e ağır biniyor |
| boogu-edit (int8) | edit-orgu | ~1 MP | 163,8 | 5560 | ~510 | ok | |
| boogu-edit (int8) | edit-tabela | ~1 MP | 173,3 | 5259 | ~800 | ok | |
| boogu-edit (int8) | edit-iki-gorsel | ~1 MP | 335,7 | 5267 | ~1900 | ok | çok yavaş; soğuk çalıştırma |
| hunyuan3d-2.1 | 3d-sandik | ~1 MP → GLB | 92,9 | 5569 | ~10700 | ok | şekil iyi, dokusuz |
| hunyuan3d-2.1 | 3d-mantar | ~1 MP → GLB | 77,9 | 5751 | ~9780 | ok | çıktı 10,7 MB (repo kuralı: 10 MB üstü CSV'de boyut olarak kayıtlı) |
| hunyuan3d-2.1 | 3d-robot | ~1 MP → GLB | 76,1 | 5590 | ~9860 | ok | |
| triposplat | 3d-sandik/mantar/robot | ~1 MP → PLY | 36,9–41,2 | 5430–5514 | ~18400 | ok | Gaussian splat PLY 17,8 MB; şekil daha kaba, hızlı |
| idol | 3d-sandik/mantar/robot | ~1 MP → PLY | 36,2–43,5 | 5089–5815 | ~18900 | ok | splat; Triposplat ile aynı bant genişliği/kalite sınıfı |
| hunyuan3d-2-mv-turbo | 3d-cok-aci-robot | 4 görünüş → GLB | 65,8 | 5671 | ~12100 | ok | 4 görsele rağmen tek görüntüden (~80 sn) hızlı; şekil tutarlı |
| pixal3d-multiview (int8) | 3d-cok-aci-robot | 4 görünüş → dokulu GLB | 477,4 | 7113 | ~3560 | ok | DOKULU tek model; 8 GB'ın sınırını zorladı (7,1 GB tepe); 8 dk; GLB 81 MB (repo'ya girmedi, boyut CSV'de) |
| wan2.2-ti2v-5b (fp16) | video-kulube | 832×480, 49 kare / 24 fps | 119,5 | 6136 | ~3550 | ok | görüntüden video; 2,4 MB mp4; 8 GB'ta akıcı |
| flux3-klein (int8) | t2i-gol-evi | 1024² | 25,1 / 7,4 (1344×768) | 5488–5600 | (CSV'de) | ok | kapılı (gated) HF deposundan indirildi |
| flux3-klein (int8) | t2i-portre | 1024² | 8,6 | 5472 | | ok | portre çok iyi (ışık/doku); gözler kapalı geldi |
| flux3-klein (int8) | t2i-afis | 1344×768 | 8,3 | 5568 | | ok | "Günaydin Istanbul" — testlerdeki EN DOĞRU Türkçe başlık (ı/ğ noktalamasız, alt yazı yok) |
| flux2-klein-4b-edit + LoRA | edit-lora-sil | ~1 MP | 47,5 | 5536 | | ok | fal.ai nesne-silme LoRA (Apache-2.0, 0,14 GB): kırmızı işaretli feneri izsiz sildi, askı halkası kaldı |

## Göze çarpanlar
- Türkçe yazı ("Göl Evi", "Günaydın İstanbul", "Şehrin en güzel çayı: 15 ₺"):
  - "Göl Evi" tabelasını yalnız mage-flow-turbo harfi harfine başardı; diğerlerinde harf/aksan bozulmaları.
  - "Günaydın İstanbul" afişinde hiçbir model tam doğru yazmadı: mage "Günayin Istahul", qwen "Günandin Istanhül", krea "Günayydjn Istańbul", boogu "Günadih İstänbül / Şehrin en bülzür çary: 15 €". Krea'da ₺ simgesi $'a, Boogu'da €'ya dönüştü. En iyisi FLUX.3 Klein: "Günaydin Istanbul" (yalnız noktalı harfler düz; alt yazı yok). Türkçe metin için yine de sonradan metin katmanı önerilir.
- Yüzler ve eller: mage portresi çok iyi; krea2 portresi en iyisi (cilt dokusu, ışık). Düzenlemelerde (kış, iki-görsel) yüzler tanınabilir kaldı; bozuk el gözlenmedi.
- Düzenleme (kış, örgü, tabela, iki görsel): flux2-klein-4b mükemmel kış atmosferi + yüz koruması; qwen-edit ve mage-edit iyi ve çok daha hızlı. İki-görsel (yüz+kıyafet) flux2-klein-2img ve qwen-edit'te başarılı; mage tek-görüntüyle sınırlı, boogu-edit iki-görsele izin veriyor ama 3 dk'yı aşıyor.
- 3B (şekil, doku, arka taraf; splat çıktısının türü): hunyuan3d-2.1 şekil açısından en temiz (~80 sn, dokusuz GLB). Triposplat/Idol hızlı splat (~37 sn, PLY, 17,8 MB) ama geometri kaba. MV-Turbo 4 görünüşten 66 sn'de tutarlı şekil. Pixal3D tek DOKULU üretici (477 sn, 7,1 GB tepe) — yavaş ama 8 GB'ta çalışıyor.
- Hata ya da bellek yetmezliği (OOM): hiç OOM yok. En ağır anlar: pixal3d 7113 MB kart; boogu-edit boş RAM'ı ~510 MB'a indirdi (çalıştı ama sınırda). Pixal3D'de üç iş akışı hatası düzeltildi: RemoveBackground'ın tek maske çıkışı, RemeshMesh'in dinamik girdilerinin API doğrulamasını hiç geçmemesi (çıkarıldı) ve BakeAmbientOcclusion'a UV-li mesh verilmesi.

## Sonuç: 8 GB kart için
- Önerilenler: mage-flow-turbo + mage-flow-edit-turbo (en hızlı, ~3 sn, 5,7 GB); flux2-klein-4b-edit (düzenleme kalitesi, 13–31 sn); flux3-klein (yeni: ~8 sn, en doğru Türkçe yazı, portre çok iyi); qwen-image-2.1-turbo(+edit); krea2-turbo (portre); hunyuan3d-2.1 ve MV-turbo (3B şekil); Triposplat/Idol (hızlı önizleme splat); wan2.2-ti2v-5b (video, 49 kare ~2 dk).
- Yavaş ama çalışanlar: boogu-edit (160–220 sn + RAM baskısı), pixal3d-multiview (8 dk, 7,1 GB tepe), hunyuan3d-2.1 (~80 sn, normal).
- BLA kataloğuna aday olanlar (lisansıyla):
  - mage-flow-turbo / mage-flow-edit-turbo — MIT → katalog + önerilen.
  - flux2-klein-4b-edit — Apache-2.0 → edit öncelik 1 adayı.
  - boogu-turbo / boogu-edit — Apache-2.0 → aday (edit yavaş).
  - pixal3d-multiview — MIT → dokulu 3B adayı (yavaş, sınırda).
  - idol — Apache-2.0; triposplat — Apache-2.0 → splat adayı.
  - flux3-klein — FLUX Kommunity v1.0 (5 M $ altı gelirle ticari serbest) → koşullu, güçlü aday (hız + Türkçe yazı + portre).
  - wan2.2-ti2v-5b — Apache-2.0 (Comfy-Org repack) → tek video adayı.
  - LoRA: fal/flux-2-klein-4B-object-remove — Apache-2.0 → LoRA altyapısı (lora_base + LoraLoaderModelOnly) 8 GB'ta çalışıyor kanıtı.
  - qwen-image-2.1-turbo(+edit) — Qwen Research (ticari DEĞİL) → yalnız ücretsiz modda.
  - krea2-turbo — Krea Community (<1 M $ gelir serbest) → koşullu.
  - hunyuan3d-2.1 / mv-turbo — Tencent Hunyuan Community (1M MAU altı ticari serbest) → koşullu.
- Önerilmeyenler (neden): boogu-edit tek başına önerilmez (kullanım deneyimi çok yavaş; turbo kısmı önerilir); Triposplat ve Idol'den yalnız biri kataloğa girsin (biri yeterli — Idol tercih, aynı hız, daha derli toplu splatlar).

## İsteğe bağlı testler
- LoRA: BAŞARILI — flux2-klein-4b-edit'e fal.ai nesne-silme LoRA'sı (Apache-2.0, 0,14 GB) bağlandı; kırmızıyla işaretlenen fener izsiz silindi (47,5 sn, 5,5 GB). `lora_base` + LoraLoaderModelOnly zinciri 8 GB'ta çalışıyor.
- Video (Wan 2.2 5B): BAŞARILI — 832×480, 49 kare, 24 fps mp4 ~2 dk'da üretildi (tepe 6,1 GB, Apache-2.0). 14 modelin ötesinde 16. model olarak eklendi.
- ~~Kapıdaki modeller~~ FLUX.3 Klein TEST EDİLDİ: HF lisans onayı sonrası indirildi (int8 5,8 GB + qwen3vl-4b int8 4,9 GB); 8 GB'ta ~8 sn. Kalan kapalı: yok.
