# ArchiveStream CloudStream Eklentisi

Eklenti kaynagi repoda yasar: `ArchiveStreamProvider/` (CloudStream v4 uyumlu).
GitHub Actions her push'ta otomatik derler ve `builds` dalina yukler.

## CloudStream'e ekleme (APK derlendikten sonra)
1. Telefonunda CloudStream > Ayarlar > Uzantilar > Depo Ekle
2. Su adresi yapistir:
   https://raw.githubusercontent.com/<KULLANICI>/<REPO>/main/repo.json
3. "ArchiveStream (Kamu Mali)" eklentisi listede cikar, kur.

## Notlar
- Icerik tamamen Archive.org kamu mali koleksiyonlarindan gelir.
- Depo CloudStream tarafindan erisilebilmesi icin HERKESE ACIK olmalidir
  (raw.githubusercontent.com ozel repolarda calismaz).
- Bot her tarama sonrasi degisiklikleri otomatik commit + push eder,
  Actions yeni APK'yi derler.
