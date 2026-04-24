"""F1000Research crawler — XML comes from f1000research.com (NOT EuroPMC).

Flow:
  1) EuroPMC search for F1000Res methods-article hits → DOI.
  2) Resolve DOI through doi.org → canonical f1000research.com URL (`/articles/{id}-{issue}/v{ver}`).
  3) GET `<that URL>/xml` to retrieve the JATS XML.
  4) Parse with f1000 parser and store.
"""
from __future__ import annotations
import argparse, json, logging, os, time, urllib.request, urllib.error, gzip, re
from .europepmc import EuropePMC
from .parsers.f1000 import parse
from .schema import validate
from .pipeline import dict_to_protocol
from .storage import Storage

log = logging.getLogger(__name__)

UA = "protocol-corpus/0.1 (research)"

F1000_QUERY = 'JOURNAL:"F1000Res" OPEN_ACCESS:Y AND PUB_TYPE:"methods-article"'


def _get(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept-Encoding": "gzip",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            data = gzip.decompress(data)
        return data


def resolve_f1000_url(doi: str) -> str | None:
    """doi.org redirects to f1000research.com/articles/{id}-{issue}/v{ver}."""
    try:
        req = urllib.request.Request(f"https://doi.org/{doi}",
                                     headers={"User-Agent": UA})
        req.get_method = lambda: "HEAD"
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.geturl()
    except urllib.error.HTTPError as e:
        if e.code in (301, 302):
            return e.headers.get("location")
        log.warning("doi resolve %s: %s", doi, e)
    except Exception as e:
        log.warning("doi resolve %s: %s", doi, e)
    return None


def fetch_xml(doi: str, cache_dir: str | None) -> str | None:
    if cache_dir:
        safe = re.sub(r"[^A-Za-z0-9]+", "_", doi)
        cached = os.path.join(cache_dir, f"{safe}.xml")
        if os.path.exists(cached):
            return open(cached, encoding="utf-8", errors="replace").read()
    url = resolve_f1000_url(doi)
    if not url or "f1000research.com/articles/" not in url:
        return None
    xml_url = url.rstrip("/") + "/xml"
    try:
        data = _get(xml_url)
        xml = data.decode("utf-8", errors="replace")
    except Exception as e:
        log.warning("xml fetch %s: %s", doi, e)
        return None
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
        safe = re.sub(r"[^A-Za-z0-9]+", "_", doi)
        with open(os.path.join(cache_dir, f"{safe}.xml"), "w",
                  encoding="utf-8") as f:
            f.write(xml)
    return xml


def run(limit: int, storage: Storage, rate: float,
        cache_dir: str | None = None) -> dict:
    client = EuropePMC(rate_per_sec=4.0)
    min_gap = 1.0 / rate
    last = 0.0
    stats = {"fetched": 0, "pass": 0, "fail": 0, "errors": 0, "skipped": 0}
    for hit in client.search(F1000_QUERY, page_size=100, max_results=limit):
        doi = hit.get("doi")
        pmcid = hit.get("pmcid", "")
        pid = f"f1000:{pmcid or doi}"
        if not doi:
            stats["skipped"] += 1; continue
        if storage.seen(pid):
            stats["skipped"] += 1; continue
        gap = min_gap - (time.time() - last)
        if gap > 0:
            time.sleep(gap)
        last = time.time()
        try:
            xml = fetch_xml(doi, cache_dir)
            if not xml:
                stats["errors"] += 1; continue
            d = parse(xml)
            d["source"] = "f1000"
            # Europe-PMC-provided metadata overrides parsed meta when present
            d.setdefault("doi", doi)
            d.setdefault("pmcid", pmcid)
            d["id"] = pid  # pipeline will keep this via dict_to_protocol
            proto = dict_to_protocol(d)
            proto.id = pid
            validate(proto)
            storage.save(proto.to_dict())
            stats["fetched"] += 1
            stats["pass" if proto.qc_pass else "fail"] += 1
            if (stats["pass"] + stats["fail"]) % 10 == 0:
                log.info("  progress: %s", stats)
        except Exception as e:
            stats["errors"] += 1
            log.warning("  err doi=%s: %s", doi, str(e)[:140])
    return stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--rate", type=float, default=2.0)
    ap.add_argument("--data-dir",
                    default=os.path.join(os.path.dirname(__file__), "..", "data"))
    ap.add_argument("--cache-dir",
                    default=os.path.join(os.path.dirname(__file__), "..", "data", "raw_f1000"))
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    storage = Storage(os.path.abspath(args.data_dir))
    s = run(args.limit, storage, args.rate, cache_dir=os.path.abspath(args.cache_dir))
    print(json.dumps(s, indent=2))


if __name__ == "__main__":
    main()
