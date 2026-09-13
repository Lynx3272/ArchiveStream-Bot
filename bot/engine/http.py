"""Dayanikli HTTP katmani: UA rotasyonu, retry/backoff, cloudscraper ve opsiyonel Playwright fallback."""
import random
import time

import requests

try:
    import cloudscraper
except Exception:
    cloudscraper = None

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]


class ScrapeError(Exception):
    """Strateji basarisizliginda firlatilir; self-healing motoru bunu yakalar."""


class HttpClient:
    def __init__(self, timeout: int = 25):
        self.timeout = timeout
        self.session = requests.Session()
        self._scraper = None
        if cloudscraper is not None:
            try:
                self._scraper = cloudscraper.create_scraper()
            except Exception:
                self._scraper = None

    def _headers(self) -> dict:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/json,*/*",
            "Accept-Language": "tr,en;q=0.8",
        }

    def _backoff(self, attempt: int):
        time.sleep(min(2 ** attempt, 8))

    def get_text(self, url: str, retries: int = 3) -> str:
        last = None
        for attempt in range(retries):
            try:
                r = self.session.get(url, headers=self._headers(), timeout=self.timeout)
                if r.status_code == 200:
                    return r.text
                last = f"HTTP {r.status_code}"
            except Exception as e:
                last = repr(e)
            self._backoff(attempt)
        raise ScrapeError(f"get_text basarisiz: {url} ({last})")

    def get_json(self, url: str, retries: int = 3):
        last = None
        for attempt in range(retries):
            try:
                r = self.session.get(url, headers=self._headers(), timeout=self.timeout)
                if r.status_code == 200:
                    return r.json()
                last = f"HTTP {r.status_code}"
            except ValueError:
                # JSON parse edilemedi -> cloudscraper ile tekrar dene
                try:
                    if self._scraper is not None:
                        r = self._scraper.get(url, timeout=self.timeout)
                        if r.status_code == 200:
                            return r.json()
                        last = f"HTTP {r.status_code} (cloudscraper)"
                except Exception as e:
                    last = repr(e)
            except Exception as e:
                last = repr(e)
            self._backoff(attempt)
        raise ScrapeError(f"get_json basarisiz: {url} ({last})")

    def get_playwright_text(self, url: str) -> str:
        """JS-gerektiren sayfalar icin opsiyonel fallback. Playwright kurulu degilse ScrapeError firlatir."""
        try:
            from playwright.sync_api import sync_playwright
        except Exception as e:
            raise ScrapeError(f"Playwright kurulu degil: {e}")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(2500)
                html = page.content()
                browser.close()
                return html
        except Exception as e:
            raise ScrapeError(f"Playwright yukleme hatasi: {e}")
