"""Archive.org provider mantigi: 3 bagimsiz veri cikarma stratejisi + stream cozumleme.

Tum kaynaklar Archive.org'un resmi, acik API'lerinden beslenir (kamu mali / CC icerik).
Her strateji birbirinden bagimsizdir; biri bozulursa self-healing motoru digerine gecer.
"""
import re

from bot.logger import warn
from bot.engine.http import HttpClient, ScrapeError

SEARCH_URL = "https://archive.org/advancedsearch.php"
SCRAPE_V1_URL = "https://archive.org/services/search/v1/scrape"
METADATA_URL = "https://archive.org/metadata/{identifier}"

FIELDS = ["identifier", "title", "year", "collection", "downloads"]

VIDEO_FORMAT_HINTS = ("h.264 ia", "h.264", "mpeg4", "512kb mpeg4", "ogg video", "mp4")
BAD_FILENAME_HINTS = (".png", ".jpg", ".gif", ".txt", ".xml", ".srt", ".pdf", ".zip")


def _normalize_item(raw: dict, collection: str) -> dict | None:
    identifier = raw.get("identifier")
    if not identifier:
        return None
    title = raw.get("title") or identifier
    if isinstance(title, list):
        title = title[0] if title else identifier
    year = raw.get("year") or raw.get("date") or ""
    return {
        "identifier": identifier,
        "title": str(title).strip(),
        "year": str(year)[:4] if year else "",
        "collection": collection,
        "downloads": raw.get("downloads") or 0,
        "page_url": f"https://archive.org/details/{identifier}",
    }


def _query_for(collection: str) -> str:
    return f'collection:({collection}) AND mediatype:(movies)'


# --------------------------------------------------------------------------
# Strateji 1: advancedsearch JSON API (birincil yol)
# --------------------------------------------------------------------------
def strategy_api_json(http: HttpClient, collection: str, rows: int) -> list[dict]:
    params = (
        f"?q={_query_for(collection).replace(' ', '+')}"
        f"&fl[]={FIELDS[0]}&fl[]={FIELDS[1]}&fl[]={FIELDS[2]}&fl[]={FIELDS[3]}&fl[]={FIELDS[4]}"
        f"&rows={rows}&page=1&output=json&sort[]=downloads+desc"
    )
    data = http.get_json(SEARCH_URL + params)
    docs = (data.get("response") or {}).get("docs") or []
    items = [i for i in (_normalize_item(d, collection) for d in docs) if i]
    if not items:
        raise ScrapeError("API bos sonuc dondu")
    return items


# --------------------------------------------------------------------------
# Strateji 2: Search v1 Scraping API (ikincil yol)
# --------------------------------------------------------------------------
def strategy_scrape_v1(http: HttpClient, collection: str, rows: int) -> list[dict]:
    url = (
        f"{SCRAPE_V1_URL}?q={_query_for(collection).replace(' ', '+')}"
        f"&fields=identifier,title,year,downloads&count={min(rows, 100)}"
    )
    data = http.get_json(url)
    items_raw = data.get("items") or []
    items = [i for i in (_normalize_item(d, collection) for d in items_raw) if i]
    if not items:
        raise ScrapeError("Scrape v1 bos sonuc dondu")
    return items


# --------------------------------------------------------------------------
# Strateji 3: HTML + regex (sayfa icine gomulu JSON'dan kurtarma)
# --------------------------------------------------------------------------
def strategy_html_regex(http: HttpClient, collection: str, rows: int) -> list[dict]:
    html = http.get_text(f"https://archive.org/details/{collection}")
    ids = []
    for m in re.finditer(r'"identifier"\s*:\s*"([^"]+)"', html):
        if m.group(1) not in ids:
            ids.append(m.group(1))
    if not ids:
        # son care: item linklerinden topla
        for m in re.finditer(r'href="/details/([^"?/]+)"', html):
            if m.group(1) not in ids:
                ids.append(m.group(1))
    ids = [i for i in ids if not i.startswith("_")]
    if not ids:
        raise ScrapeError("HTML icinden identifier cikarilamadi")
    items = []
    for ident in ids[:rows]:
        try:
            meta = http.get_json(METADATA_URL.format(identifier=ident)) or {}
            md = meta.get("metadata") or {}
            item = _normalize_item(
                {"identifier": ident, "title": md.get("title"), "year": md.get("year"), "downloads": 0},
                collection,
            )
            if item:
                items.append(item)
        except Exception as e:
            warn(f"  metadata atlandi ({ident}): {e}")
    if not items:
        raise ScrapeError("HTML stratejisi bos sonuc dondu")
    return items


STRATEGIES = [
    ("api_json", strategy_api_json),
    ("scrape_v1", strategy_scrape_v1),
    ("html_regex", strategy_html_regex),
]


# --------------------------------------------------------------------------
# Stream cozumleme: identifier -> dogrudan izlenebilir MP4 linkleri
# --------------------------------------------------------------------------
def resolve_streams(http: HttpClient, identifier: str) -> list[dict]:
    data = http.get_json(METADATA_URL.format(identifier=identifier)) or {}
    files = data.get("files") or []
    server = data.get("server") or "https://archive.org"
    dir_path = data.get("dir") or f"/download/{identifier}"
    streams = []
    for f in files:
        name = f.get("name") or ""
        fmt = (f.get("format") or "").lower()
        if any(h in fmt for h in VIDEO_FORMAT_HINTS) and not name.lower().endswith(BAD_FILENAME_HINTS):
            quality = "720p" if "h.264" in fmt else "480p"
            streams.append(
                {
                    "url": f"{server}{dir_path}/{name}",
                    "quality": quality,
                    "format": f.get("format"),
                    "size": f.get("size", ""),
                }
            )
    return streams
