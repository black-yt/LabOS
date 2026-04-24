"""F1000Research parser. JATS XML fetched from f1000research.com directly.
Layout: Introduction/Methods/Results (no dedicated Reagents/Equipment/Procedure
sections). We treat the Methods section (and its sub-secs) as the procedure and
mine reagents inline from the prose.
"""
import re
from .base import (extract_sec, extract_meta, parse_list_items,
                   strip_tags, extract_troubleshooting)

VERSION = "f1000-0.1"


_VENDOR_CAT_RX = re.compile(
    r"([A-Za-z][^\[\](),;\n<>]{2,120}?)\s*\(\s*([A-Z][\w .&'/-]{2,40}?)\s*,\s*"
    r"(?:cat(?:alog)?[\.\s#]*(?:number|no\.?|#)?\s*:?\s*)?([A-Za-z0-9][A-Za-z0-9\-/.]{2,30})\s*\)",
)


def _mine_reagents(text: str) -> list[dict]:
    out, seen = [], set()
    for m in _VENDOR_CAT_RX.finditer(text):
        name = m.group(1).strip().rstrip(".,;:")
        vendor = m.group(2).strip()
        cat = m.group(3).strip()
        name = re.sub(r"^(?:using|with|from|add|the|a|an)\s+", "", name, flags=re.I)
        key = name.lower()
        if key in seen or len(name) < 3 or len(name) > 150:
            continue
        if len(cat) < 2:
            continue
        seen.add(key)
        out.append({"name": name[:200], "vendor": vendor,
                    "catalog_id": cat, "rrid": "", "category": ""})
    return out


def _collect_steps(section_body: str) -> list[dict]:
    """Treat every <list-item> OR numbered <p> inside the Methods section
    as a step, attributed to the nearest enclosing sub-sec title."""
    steps: list[dict] = []
    # First prefer numbered list-items at any depth.
    for num, text in parse_list_items(section_body):
        steps.append({"step_no": num, "text": text[:2000], "section": "", "duration": ""})
    # Then collect nested sub-sec prose as additional steps if list items weren't found.
    if not steps:
        for secm in re.finditer(r"<sec\b[^>]*>\s*<title[^>]*>(.*?)</title>(.*?)</sec>",
                                 section_body, re.DOTALL):
            sec_title = strip_tags(secm.group(1))
            body = secm.group(2)
            for num, text in parse_list_items(body):
                steps.append({"step_no": num, "text": text[:2000],
                              "section": sec_title, "duration": ""})
            if not steps:
                # Fallback: every non-trivial <p> becomes a step
                idx = 0
                for pm in re.finditer(r"<p[^>]*>(.*?)</p>", body, re.DOTALL):
                    t = strip_tags(pm.group(1))
                    if 20 < len(t) < 2000:
                        idx += 1
                        steps.append({"step_no": str(idx), "text": t[:2000],
                                      "section": sec_title, "duration": ""})
    if not steps:
        # Last resort: flat <p> scrape of the Methods body
        idx = 0
        for pm in re.finditer(r"<p[^>]*>(.*?)</p>", section_body, re.DOTALL):
            t = strip_tags(pm.group(1))
            if 20 < len(t) < 2000:
                idx += 1
                steps.append({"step_no": str(idx), "text": t[:2000],
                              "section": "", "duration": ""})
    return steps


def parse(xml: str) -> dict:
    meta = extract_meta(xml)
    mats = (extract_sec(xml, r"Materials(?:\s+and\s+reagents)?")
            or extract_sec(xml, r"Reagents(?:\s+and\s+equipment)?"))
    methods = (extract_sec(xml, r"Methods?") or extract_sec(xml, r"Protocol"))
    reagents: list[dict] = []
    if mats:
        # Each list-item / numbered paragraph in Materials is a candidate reagent
        for num, text in parse_list_items(mats):
            name = re.split(r"[\(,]", text, 1)[0].strip().rstrip(".")
            if len(name) < 3 or len(name) > 200:
                continue
            vendor, cat = "", ""
            m = _VENDOR_CAT_RX.search(text)
            if m:
                vendor, cat = m.group(2).strip(), m.group(3).strip()
            reagents.append({"name": name[:200], "vendor": vendor,
                             "catalog_id": cat, "rrid": "", "category": ""})
    if len(reagents) < 3:
        # mine inline patterns from Materials + Methods
        mined = _mine_reagents(strip_tags((mats or "") + " " + (methods or "")))
        have = {r["name"].lower() for r in reagents}
        for r in mined:
            if r["name"].lower() not in have:
                reagents.append(r); have.add(r["name"].lower())

    equipment: list[dict] = []
    eq_sec = extract_sec(xml, r"Equipment(?:\s+setup)?")
    if eq_sec:
        for num, text in parse_list_items(eq_sec):
            name = re.split(r"[\(,]", text, 1)[0].strip().rstrip(".")
            if 3 <= len(name) <= 200:
                equipment.append({"name": name[:200], "vendor": "", "model": ""})

    steps = _collect_steps(methods or "")

    materials_raw = strip_tags(mats or "")[:5000]
    if len(materials_raw) < 150 and reagents:
        materials_raw = "\n".join(
            f"{r['name']} ({r.get('vendor','')}, {r.get('catalog_id','')})"
            for r in reagents
        )[:5000]

    return {
        **meta,
        "source": "f1000",
        "reagents": reagents,
        "equipment": equipment,
        "materials_raw": materials_raw,
        "steps": steps,
        "troubleshooting": extract_troubleshooting(xml),
        "timing": "",
        "parser_version": VERSION,
    }
