"""ArchiveStream Otonom Bot - giris noktasi.

Kullanim:
  - Masaustu baslaticisindan ac -> "start" yaz -> tam tarama + eklenti uretimi + GitHub push
  - Test/mod: python -m bot.main --scan   (push atlanir, PAT istenmez)
"""
import json
import os
import sys

from bot import logger, config
from bot.logger import info, ok, warn, err, git
from bot.engine.http import HttpClient
from bot.engine.healer import scan_all
from bot.engine import archiveorg
from bot.engine.sources import SOURCES
from bot import providers_gen, github_sync

BANNER = """
==============================================================
   ArchiveStream OTONOM BOT  (kamu mali / CC icerik motoru)
   Kaynaklar: Archive.org resmi acik arsiv API'leri
==============================================================
"""


def ensure_desktop_launcher():
    """Masaustune 'ArchiveStream Bot' kisayolu olusturur (yoksa)."""
    home = os.environ.get("USERPROFILE")
    if not home:
        return None
    candidates = [os.path.join(home, "Desktop"), os.path.join(home, "OneDrive", "Desktop")]
    desktop = next((d for d in candidates if os.path.isdir(d)), None)
    if not desktop:
        return None
    launcher = os.path.join(desktop, "ArchiveStream Bot.bat")
    content = (
        "@echo off\r\n"
        "title ArchiveStream Otonom Bot\r\n"
        f'cd /d "{config.BASE_DIR}"\r\n'
        "call run.bat\r\n"
    )
    try:
        existing = open(launcher, encoding="utf-8").read() if os.path.exists(launcher) else ""
        if existing != content:
            with open(launcher, "w", encoding="utf-8") as f:
                f.write(content)
            info(f"Masaustu baslaticisi olusturuldu: {launcher}")
        return launcher
    except OSError as e:
        warn(f"Baslatici olusturulamadi: {e}")
        return None


def run_pipeline(auto_push: bool) -> dict:
    config.ensure_dirs()
    settings = config.load_settings()
    rows = int(settings.get("rows_per_collection", 40))

    http = HttpClient()
    info(f"Tarama basliyor: {len(SOURCES)} kaynak, kaynak basi ~{rows} icerik")

    catalog = scan_all(http, SOURCES, rows)

    # Ilk 3 icerik icin stream linklerini dogrula (ornek rapor)
    sample_links = {}
    for item in catalog["items"][:3]:
        try:
            streams = archiveorg.resolve_streams(http, item["identifier"])
            sample_links[item["identifier"]] = [s["url"] for s in streams[:2]]
            if streams:
                ok(f"Stream dogrulandi: {item['title'][:50]} ({len(streams)} link)")
            else:
                warn(f"Stream bulunamadi: {item['title'][:50]}")
        except Exception as e:
            warn(f"Stream cozumleme hatasi ({item['identifier']}): {e}")

    catalog["sample_links"] = sample_links
    data_path = config.DATA_DIR / "catalog.json"
    data_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")
    ok(f"Katalog kaydedildi: {data_path}")

    generated = providers_gen.generate_plugin(catalog)
    ok(f"{len(generated)} CloudStream dosyasi uretildi")

    # Saglik raporu
    broken = [h for h in catalog["health"] if h["status"] == "broken"]
    healed = config.load_heal_memory()
    total = sum(h["items"] for h in catalog["health"])

    report = {
        "kaynaklar": {h["name"]: h["status"] for h in catalog["health"]},
        "toplam_icerik": total,
        "bozuk_kaynak": [h["name"] for h in broken],
        "heal_hafizasi": {k: v.get("strategy") for k, v in healed.items()},
        "push": False,
    }

    print()
    ok(f"RAPOR: {len(SOURCES) - len(broken)}/{len(SOURCES)} kaynak saglikli, {total} icerik tarandi")
    if broken:
        warn(f"Bozuk kaynaklar (otomatik atlandi): {', '.join(h['name'] for h in broken)}")

    if auto_push and settings.get("auto_push", True):
        try:
            repo_url = github_sync.push_all("ArchiveStream Bot: otomatik tarama ve eklenti guncellemesi")
            report["push"] = True
            report["cloudstream_repo_link"] = repo_url
        except Exception as e:
            err(f"GitHub push basarisiz: {e}")
    return report


def main():
    ensure_desktop_launcher()

    if "--scan" in sys.argv:
        run_pipeline(auto_push=False)
        return

    print(BANNER)
    print("  ArchiveStream Otonom Bot Hazir. Baslatmak icin 'start' yazin:")
    print("  (diger komutlar: durum, cikis)")
    print()
    while True:
        try:
            cmd = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if cmd == "start":
            try:
                report = run_pipeline(auto_push=True)
                if report["push"]:
                    print("\n  BASARILI: Tarama bitti, eklenti uretildi, GitHub'a yuklendi.")
                    print(f"  CloudStream > Uzantilar > Depo Ekle su linki yapistir:")
                    print(f"  {report.get('cloudstream_repo_link')}\n")
                else:
                    print("\n  Tarama bitti; GitHub yuklemesi yapilamadi (ustteki hataya bakin).\n")
            except KeyboardInterrupt:
                print()
                warn("Kullanici iptal etti.")
            except Exception as e:
                err(f"Beklenmeyen hata: {e}")
        elif cmd == "durum":
            settings = config.load_settings()
            mem = config.load_heal_memory()
            print(f"  GitHub: {settings.get('git_user') or '(tanimsiz)'}/{settings.get('git_repo') or '(tanimsiz)'}")
            print(f"  Heal hafizasi: {json.dumps(mem, ensure_ascii=False)}")
        elif cmd in ("cikis", "exit", "cik"):
            break


if __name__ == "__main__":
    main()
