"""Europe PMC client with cursor-based pagination, retries, polite rate limiting."""
import json, time, urllib.request, urllib.parse, gzip, io, random, os

BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest"
UA = "labprotocol-crawler/0.1 (mailto:research@example.org)"


class EuropePMC:
    def __init__(self, rate_per_sec: float = 4.0, cache_dir: str | None = None):
        self.min_gap = 1.0 / rate_per_sec
        self._last = 0.0
        self.cache_dir = cache_dir
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)

    def _throttle(self):
        now = time.time()
        wait = self.min_gap - (now - self._last)
        if wait > 0:
            time.sleep(wait)
        self._last = time.time()

    def _get(self, url: str, retries: int = 4, timeout: int = 45) -> bytes:
        for attempt in range(retries):
            self._throttle()
            try:
                req = urllib.request.Request(url, headers={
                    "User-Agent": UA,
                    "Accept-Encoding": "gzip",
                })
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    data = r.read()
                    if r.headers.get("Content-Encoding") == "gzip":
                        data = gzip.decompress(data)
                    return data
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    raise
                if e.code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                    sleep = (2 ** attempt) + random.random()
                    time.sleep(sleep)
                    continue
                raise
            except (urllib.error.URLError, TimeoutError) as e:
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise
        raise RuntimeError(f"exhausted retries: {url}")

    def search(self, query: str, page_size: int = 100, max_results: int | None = None):
        """Yield search hit dicts, paginated via cursorMark."""
        cursor = "*"
        fetched = 0
        while True:
            params = {
                "query": query,
                "format": "json",
                "pageSize": page_size,
                "cursorMark": cursor,
                "resultType": "lite",
            }
            url = f"{BASE}/search?" + urllib.parse.urlencode(params)
            data = json.loads(self._get(url).decode("utf-8"))
            results = data.get("resultList", {}).get("result", [])
            if not results:
                return
            for r in results:
                yield r
                fetched += 1
                if max_results and fetched >= max_results:
                    return
            next_cursor = data.get("nextCursorMark")
            if not next_cursor or next_cursor == cursor:
                return
            cursor = next_cursor

    def fulltext_xml(self, pmcid: str) -> str:
        """Return XML string for a PMC article. Cached on disk if cache_dir set."""
        if self.cache_dir:
            path = os.path.join(self.cache_dir, f"{pmcid}.xml")
            if os.path.exists(path):
                with open(path, "rb") as f:
                    return f.read().decode("utf-8", "replace")
        url = f"{BASE}/{pmcid}/fullTextXML"
        raw = self._get(url)
        text = raw.decode("utf-8", "replace")
        if self.cache_dir:
            with open(os.path.join(self.cache_dir, f"{pmcid}.xml"), "wb") as f:
                f.write(raw)
        return text
