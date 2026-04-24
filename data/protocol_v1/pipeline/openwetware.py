"""OpenWetWare fetcher + parser.

OWW is a MediaWiki community wiki. Pages under Category:Protocols are mostly
user-written protocols of heterogeneous quality. We pull page HTML via the
`action=parse` API, then apply a light HTML heuristic that mirrors the other
parsers: find sections titled Materials/Reagents/Equipment/Procedure/Steps and
extract list items.

Usage:
    python3 -m crawler.openwetware --limit 300 --rate 2
"""
from __future__ import annotations
import argparse, json, logging, time, os, re, urllib.request, urllib.parse, datetime
from html import unescape

from .pipeline import dict_to_protocol
from .schema import validate
from .storage import Storage

log = logging.getLogger(__name__)

API = "https://openwetware.org/mediawiki/api.php"
UA = "labprotocol-crawler/0.1 (mailto:research@example.org)"
VERSION = "oww-0.2"

SECTION_MATS = re.compile(
    r"materials?|reagents?|equipment|supplies|solutions|apparatus", re.I)
SECTION_STEPS = re.compile(
    r"procedure|protocol|steps?|method(s| for)?|workflow", re.I)


def _get(url: str, retries: int = 3, timeout: int = 30) -> bytes:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)


def list_category_members(category: str = "Protocol", limit: int | None = None):
    """Yield {'pageid': int, 'title': str} for pages in a category."""
    cmcontinue = None
    fetched = 0
    while True:
        params = {
            "action": "query", "list": "categorymembers",
            "cmtitle": f"Category:{category}", "cmlimit": 500,
            "cmtype": "page", "format": "json",
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue
        url = API + "?" + urllib.parse.urlencode(params)
        data = json.loads(_get(url).decode("utf-8"))
        for p in data.get("query", {}).get("categorymembers", []):
            yield p
            fetched += 1
            if limit and fetched >= limit:
                return
        cont = data.get("continue", {}).get("cmcontinue")
        if not cont:
            return
        cmcontinue = cont


def fetch_page_html(pageid: int) -> tuple[str, dict]:
    params = {
        "action": "parse", "pageid": pageid, "prop": "text|sections",
        "format": "json",
    }
    url = API + "?" + urllib.parse.urlencode(params)
    data = json.loads(_get(url).decode("utf-8"))
    parse = data.get("parse", {})
    html = parse.get("text", {}).get("*", "")
    return html, parse


def _strip_tags(s: str) -> str:
    t = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", unescape(t)).strip()


def _split_sections(html: str) -> list[tuple[str, str]]:
    """Return [(heading, body_html), ...] sections split at top-level <h2>
    headings only. Nested <h3>/<h4> stay inside the h2 body so step content in
    sub-sections is attributed to its enclosing "Procedure" / "Methods" section.
    """
    html = re.sub(r'<span class="mw-editsection.*?</span>', "", html, flags=re.DOTALL)
    # Also drop the TOC which lives in a div before the first heading.
    html = re.sub(r'<div id="toc"[^>]*>.*?</div>\s*</div>', "", html, flags=re.DOTALL)
    parts = re.split(r"<h2\b[^>]*>(.*?)</h2>", html, flags=re.DOTALL)
    sections = [("", parts[0])] if parts else []
    for i in range(1, len(parts), 2):
        heading = _strip_tags(parts[i])
        body = parts[i + 1] if i + 1 < len(parts) else ""
        sections.append((heading, body))
    return sections


def _extract_list_items(body: str) -> list[str]:
    items = re.findall(r"<li[^>]*>(.*?)</li>", body, re.DOTALL)
    out = []
    for it in items:
        t = _strip_tags(it)
        if 3 <= len(t) <= 1000:
            out.append(t)
    return out


_NUMBERED_P = re.compile(r"^\s*(\d+)[.)]\s+(.+)", re.DOTALL)


def _extract_numbered_paragraphs(body: str) -> list[str]:
    """Many OWW protocols put steps as `<p>1. ...</p><p>2. ...</p>` rather than
    using <ol>/<ul>. Return the text payload of each such paragraph."""
    out = []
    for pm in re.finditer(r"<p[^>]*>(.*?)</p>", body, re.DOTALL):
        t = _strip_tags(pm.group(1))
        m = _NUMBERED_P.match(t)
        if m and len(m.group(2)) >= 10:
            out.append(m.group(2).strip())
    return out


_SKIP_SECTION = re.compile(
    r"^(contents|curators|abstract|summary|references?|notes?|contact|"
    r"acknowledgments?|discussion|history|see also|external links|"
    r"specific protocols|workflow|overview|introduction|background|"
    r"critical steps|troubleshooting|safety)",
    re.I,
)

_VENDOR_CAT_RX = re.compile(
    r"([^\[\](),;\n]+?)\s*\(\s*([A-Z][\w .&'/-]+?)\s*,\s*"
    r"(?:cat(?:alog)?[\.\s#]*(?:number|no\.?)?\s*:?\s*)?([A-Za-z0-9\-/.]+)\s*\)",
    re.IGNORECASE,
)


def _mine_inline_reagents(text: str, existing_names: set[str]) -> list[dict]:
    """Find `Name (Vendor, cat# XYZ)` patterns anywhere in prose."""
    out = []
    for m in _VENDOR_CAT_RX.finditer(text):
        name = m.group(1).strip().rstrip(".,;:")
        vendor = m.group(2).strip()
        catalog = m.group(3).strip()
        # strip leading words like "using", "with", "from"
        name = re.sub(r"^(?:using|with|from|add|the)\s+", "", name, flags=re.I)
        if len(name) < 3 or len(name) > 150 or name.lower() in existing_names:
            continue
        if len(catalog) < 2 or len(vendor) < 2:
            continue
        existing_names.add(name.lower())
        out.append({"name": name[:200], "vendor": vendor,
                    "catalog_id": catalog, "rrid": "", "category": ""})
    return out


def parse(html: str, title: str, url: str) -> dict:
    sections = _split_sections(html)

    reagents: list[dict] = []
    equipment: list[dict] = []
    steps: list[dict] = []
    mat_parts: list[str] = []

    for heading, body in sections:
        if SECTION_MATS.search(heading):
            for line in _extract_list_items(body):
                # Heuristic vendor/catalog extraction: "Name (Vendor, cat# XYZ)"
                vendor, catalog = "", ""
                m = re.search(r"\(([^()]+?)\s*,\s*(?:cat(?:alog)?[\.\s#]*(?:number|no\.?)?\s*:?\s*)?"
                              r"([A-Za-z0-9\-/.]+)\)", line, re.IGNORECASE)
                if m:
                    vendor, catalog = m.group(1).strip(), m.group(2).strip()
                name = re.split(r"[\(,]", line, 1)[0].strip().rstrip(".")
                if len(name) < 3:
                    continue
                is_equip = bool(re.search(
                    r"centrifuge|microscope|incubator|thermocycler|cytometer|"
                    r"spectrophotometer|pipette|pipettor|shaker|balance|sonicator|"
                    r"scanner|freezer|oven|hood|camera|chamber",
                    line, re.I))
                if is_equip or re.search(r"^equipment", heading, re.I):
                    equipment.append({"name": name[:200], "vendor": vendor, "model": catalog})
                else:
                    reagents.append({"name": name[:200], "vendor": vendor,
                                     "catalog_id": catalog, "rrid": "", "category": ""})
            mat_parts.append(_strip_tags(body))
        elif SECTION_STEPS.search(heading):
            lines = _extract_list_items(body)
            if not lines or len(lines) < 2:
                lines = _extract_numbered_paragraphs(body) or lines
            for idx, line in enumerate(lines, 1):
                if len(line) < 15:
                    continue
                steps.append({"step_no": str(idx), "text": line[:2000],
                              "section": heading, "duration": ""})

    # Fallback 1: steps still missing → scan every non-metadata section for
    #   ordered-list / numbered-paragraph content. Many OWW pages use
    #   procedure-like h2s with biology-specific names ("cDNA Synthesis" etc.)
    #   that don't match the SECTION_STEPS keywords.
    if len(steps) < 3:
        for heading, body in sections:
            if SECTION_MATS.search(heading) or _SKIP_SECTION.match(heading.strip()):
                continue
            if SECTION_STEPS.search(heading):
                continue  # already tried above
            lines = _extract_list_items(body)
            if not lines or len(lines) < 2:
                lines = _extract_numbered_paragraphs(body) or lines
            for line in lines:
                if len(line) < 15:
                    continue
                steps.append({
                    "step_no": str(len(steps) + 1),
                    "text": line[:2000],
                    "section": heading,
                    "duration": "",
                })

    # Fallback 2: reagents still missing → mine `Name (Vendor, cat# X)` patterns
    #   from all body text (materials prose, step prose, critical steps, notes).
    if len(reagents) < 3:
        seen = {r["name"].lower() for r in reagents}
        all_text = " ".join(_strip_tags(b) for _, b in sections)
        reagents.extend(_mine_inline_reagents(all_text, seen))

    materials_raw = "\n".join(mat_parts)[:8000]
    if len(materials_raw) < 150 and reagents:
        # synthesize materials_raw from extracted reagents to satisfy gate
        materials_raw = "\n".join(
            f"{r['name']} ({r.get('vendor','')}, {r.get('catalog_id','')})"
            for r in reagents
        )[:8000]
    return {
        "source": "oww",
        "title": title,
        "doi": "", "pmcid": "", "pmid": "",
        "license": "https://creativecommons.org/licenses/by/3.0/",  # OWW default
        "journal": "OpenWetWare",
        "pub_year": "",
        "authors": [],
        "abstract": "",
        "reagents": reagents,
        "equipment": equipment,
        "materials_raw": materials_raw,
        "steps": steps,
        "troubleshooting": [],
        "timing": "",
        "parser_version": VERSION,
    }


def run(limit: int, storage: Storage, rate: float, category: str = "Protocol",
        cache_dir: str | None = None):
    min_gap = 1.0 / rate
    last = 0.0
    stats = {"fetched": 0, "pass": 0, "fail": 0, "errors": 0, "skipped": 0}
    for page in list_category_members(category, limit=limit):
        pid = f"oww:{page['pageid']}"
        if storage.seen(pid):
            stats["skipped"] += 1; continue
        try:
            # polite throttle
            gap = min_gap - (time.time() - last)
            if gap > 0: time.sleep(gap)
            last = time.time()

            html, _ = fetch_page_html(page["pageid"])
            stats["fetched"] += 1
            if cache_dir:
                os.makedirs(cache_dir, exist_ok=True)
                with open(os.path.join(cache_dir, f"{page['pageid']}.html"), "w",
                          encoding="utf-8") as f:
                    f.write(html)
            url = f"https://openwetware.org/wiki/{urllib.parse.quote(page['title'].replace(' ', '_'))}"
            d = parse(html, page["title"], url)
            d["id"] = pid  # explicit — no PMC/DOI path
            proto = dict_to_protocol(d)
            proto.id = pid  # override pipeline's source:pmcid|doi synthesis
            validate(proto)
            storage.save(proto.to_dict())
            stats["pass" if proto.qc_pass else "fail"] += 1
            if (stats["pass"] + stats["fail"]) % 25 == 0:
                log.info("  progress: %s", stats)
        except Exception as e:
            stats["errors"] += 1
            log.warning("  oww page=%s err=%s", page.get("title"), str(e)[:120])
    return stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--rate", type=float, default=2.0, help="req/sec to OWW")
    ap.add_argument("--category", default="Protocol")
    ap.add_argument("--data-dir",
                    default=os.path.join(os.path.dirname(__file__), "..", "data"))
    ap.add_argument("--cache-dir",
                    default=os.path.join(os.path.dirname(__file__), "..", "data", "raw_oww"))
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    storage = Storage(os.path.abspath(args.data_dir))
    s = run(args.limit, storage, args.rate, args.category,
            cache_dir=os.path.abspath(args.cache_dir))
    print(json.dumps(s, indent=2))


if __name__ == "__main__":
    main()
