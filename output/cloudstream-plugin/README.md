# ArchiveStream CloudStream Eklentisi

Bu klasor ArchiveStream Otonom Bot tarafindan uretilmistir. Tum icerik Archive.org
kamu mali / Creative Commons kaynaklarindan gelir (resmi API'ler uzerinden).

## Dosyalar
- `ArchiveOrgProvider.kt` : CloudStream v4 provider kaynagi (search / main page / load / links)
- `manifest.json`         : Eklenti manifesti
- `catalog.json`          : Botun son taramasindan cikan katalog (rapor amacli)

## Eklentiyi CloudStream'e yukleme (APK derleme)
1. https://github.com/Blatzar/cloudstream-template-hexated (veya resmi
   cloudstream-extensions template'i) bir depo olarak acin.
2. `ArchiveOrgProvider.kt` dosyasini `app/src/main/java/com/archivestream/plugin/`
   altina kopyalayin.
3. `Plugin.kt` icinde provider'i kaydedin:
   `registerMainAPI(ArchiveOrgProvider())`
4. `gradlew assembleRelease` ile APK'yi derleyin.
5. CloudStream > Ayarlar > Uzantilar > Yukle (offline) ile APK'yi secin.

## Notlar
- Icerik tamamen yasal kamuya mal olmus (public domain) yapitlardir.
- Bot her calistiginda bu klasor guncellenir ve GitHub'a otomatik push edilir.
