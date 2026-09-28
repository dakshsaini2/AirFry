"""Live collector skeleton (Playwright). Ethical by design:
robots.txt check, rate limiting, identified UA, backoff. It does NOT bypass CAPTCHAs/bot walls: on a challenge it
stops and logs, so use airline/OTA partner APIs or written permission for those sources.
Run: pip install -r requirements-scraper.txt && playwright install chromium && python -m backend.scraper"""
import time, random, urllib.robotparser as rp
from urllib.parse import urlparse
from datetime import date, timedelta

UA = "APIxResearchBot/1.0 (+contact: your-email@domain)"
DELAY = (4, 9)  # seconds between requests
SITES = {  # fill URL templates + selectors per site after reviewing its ToS
    "IndiGo": {"url": "https://www.goindigo.in/", "price_sel": "TODO"},
    "Akasa Air": {"url": "https://www.akasaair.com/", "price_sel": "TODO"},
}

def allowed(url):
    p = urlparse(url); r = rp.RobotFileParser(f"{p.scheme}://{p.netloc}/robots.txt")
    try: r.read()
    except Exception: return False
    return r.can_fetch(UA, url)

def collect(origin, dest, lead, site):
    from playwright.sync_api import sync_playwright
    cfg = SITES[site]
    if not allowed(cfg["url"]): return None
    dep = date.today() + timedelta(days=lead)
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True); pg = b.new_context(user_agent=UA).new_page()
        for attempt in range(3):
            try:
                pg.goto(cfg["url"], timeout=30000); pg.wait_for_load_state("networkidle")
                if "captcha" in pg.content().lower(): b.close(); return None  # stop, never bypass
                # TODO: fill search form for origin/dest/dep, then parse cfg["price_sel"]
                break
            except Exception: time.sleep(2 ** attempt)
        b.close()
    time.sleep(random.uniform(*DELAY))

if __name__ == "__main__":
    print(allowed(SITES["IndiGo"]["url"]))
