"""SELF-HEALING motoru: strateji sirasini akilli yonetir, hatayi onarir, hafizada tutar.

Calisma mantigi:
1. Kaynak icin once "heal hafizasindaki" kazanan strateji denenir.
2. Strateji hata verirse loglanir ve siradaki strateji denenir (sistem cokmez).
3. Yeni bir strateji basarili olursa hafizaya yazilir -> bir sonraki taramada ilk o denenir.
4. Hicbiri basarili olursa kaynak "broken" isaretlenir, diger kaynaklara gecilir.
"""
from bot import logger
from bot.engine import archiveorg
from bot.engine.http import HttpClient
from bot.config import load_heal_memory, save_heal_memory


def scan_source(http: HttpClient, source: dict, rows: int) -> tuple[list[dict], str | None]:
    """Bir kaynagi tum stratejilerle tarar. Donus: (items, kullanilan_strateji)."""
    collection = source["id"]
    mem = load_heal_memory()
    preferred = mem.get(collection, {}).get("strategy")

    ordered = list(archiveorg.STRATEGIES)
    if preferred:
        ordered.sort(key=lambda s: s[0] != preferred)  # hafizadaki strateji one alinir

    for name, fn in ordered:
        logger.info(f"{source['name']} taraniyor... (strateji: {name})")
        try:
            items = fn(http, collection, rows)
            if items:
                if preferred and name == preferred:
                    logger.ok(f"{source['name']}: {len(items)} icerik bulundu")
                else:
                    if preferred:
                        logger.heal(
                            f"[SELF-HEAL] {source['name']}: eski strateji '{preferred}' bozulmus, "
                            f"yeni strateji '{name}' basarili. Hafizaya yazildi."
                        )
                    logger.ok(f"{source['name']}: {len(items)} icerik bulundu (strateji: {name})")
                mem[collection] = {"strategy": name, "last_ok_items": len(items)}
                save_heal_memory(mem)
                return items, name
            raise archiveorg.ScrapeError("bos sonuc")
        except Exception as e:
            logger.heal(f"[SELF-HEAL] {source['name']}: strateji '{name}' basarisiz ({e}) -> siradaki strateji deneniyor")

    mem[collection] = {"strategy": None, "broken": True}
    save_heal_memory(mem)
    logger.err(f"{source['name']}: TUM stratejiler basarisiz. Kaynak 'broken' isaretlendi, atlaniliyor.")
    return [], None


def scan_all(http: HttpClient, sources: list[dict], rows: int) -> dict:
    """Tum kaynaklari tarar. Donus: katalog + saglik raporu."""
    catalog = {"items": [], "health": []}
    for source in sources:
        items, strategy = scan_source(http, source, rows)
        catalog["items"].extend(items)
        catalog["health"].append(
            {
                "collection": source["id"],
                "name": source["name"],
                "strategy": strategy,
                "items": len(items),
                "status": "ok" if items else "broken",
            }
        )
    return catalog
