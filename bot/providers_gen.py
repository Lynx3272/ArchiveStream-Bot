"""Bot cikti uretimi: katalog kaydi + CloudStream repo.json guncelleme.

Eklentinin Kotlin kaynagi artik repoda yasar (ArchiveStreamProvider/); GitHub Actions
her push'ta onu derleyip 'builds' dalina .cs3 dosyasini yukler. Botun gorevi:
katalog/rapor uretimi ve repo.json icindeki GitHub linklerini gercekle eslemek.
"""
import json

from bot import logger
from bot.config import PLUGIN_DIR, DATA_DIR, BASE_DIR

REPO_JSON = BASE_DIR / "repo.json"


def update_repo_links(user: str, repo: str) -> str:
    """repo.json'daki plugin listesini jsdelivr CDN uzerinden isaretler ve depo linkini dondurur.

    raw.githubusercontent.com bazi bolgelerde (TR dahil) arada engellendigi icin
    CloudStream tarafindaki tum yuklemeler jsdelivr uzerinden yapilir.
    """
    repo_url = f"https://cdn.jsdelivr.net/gh/{user}/{repo}@main/repo.json"
    data = {
        "name": "ArchiveStream - Kamu Mali Arsiv",
        "description": "Archive.org uzerinden kamu mali ve Creative Commons film/belgesel eklentileri (ArchiveStream Bot)",
        "manifestVersion": 1,
        "pluginLists": [f"https://cdn.jsdelivr.net/gh/{user}/{repo}@builds/plugins.json"],
    }
    REPO_JSON.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")
    logger.ok(f"repo.json guncellendi (CDN linkli): {repo_url}")
    return repo_url


def generate_plugin(catalog: dict) -> list:
    """Katalog raporunu ve kullanim rehberini uretir."""
    PLUGIN_DIR.mkdir(parents=True, exist_ok=True)

    catalog_path = PLUGIN_DIR / "catalog.json"
    catalog_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.ok(f"Katalog yazildi: {catalog_path}")

    readme_path = PLUGIN_DIR / "README.md"
    readme_path.write_text(BUILD_README, encoding="utf-8")

    return [catalog_path, readme_path]


BUILD_README = """# ArchiveStream CloudStream Eklentisi

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
"""
