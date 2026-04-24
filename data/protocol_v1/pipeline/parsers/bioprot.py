"""Bio-protocol parser. Prose-based; reagents and steps live in numbered <p> tags."""
import re
from .base import extract_sec, extract_meta, parse_list_items, strip_tags, extract_troubleshooting

VERSION = "bioprot-0.3"

_INLINE_VENDOR_CAT = re.compile(
    r"([A-Za-z][^\[\](),;\n<>]{2,120}?)\s*\(\s*([A-Z][\w .&'/-]{2,40}?)\s*,\s*"
    r"(?:cat(?:alog)?[\.\s#]*(?:number|no\.?|#)?\s*:?\s*)?([A-Za-z0-9][A-Za-z0-9\-/.]{2,30})\s*\)",
)


def _mine_inline(text: str) -> list[dict]:
    out, seen = [], set()
    for m in _INLINE_VENDOR_CAT.finditer(text):
        name = m.group(1).strip().rstrip(".,;:")
        name = re.sub(r"^(?:using|with|from|add|the|a|an)\s+", "", name, flags=re.I)
        key = name.lower()
        if key in seen or len(name) < 3 or len(name) > 150:
            continue
        seen.add(key)
        out.append({"name": name[:200], "vendor": m.group(2).strip(),
                    "catalog_id": m.group(3).strip(), "rrid": "", "category": ""})
    return out

# A bioprot <p> looks like one of:
#   "A. Section heading"       -> header, skip
#   "1. Reagent X (Vendor, catalog number: ABC)"  -> entry
#   "3. Anesthetize mice by..."  -> step
_NUMBERED_P = re.compile(r"^\s*(\d+)\.\s+(.+)", re.DOTALL)
_LETTER_HEADER = re.compile(r"^\s*[A-Z]\.\s+[A-Z]")  # "A. Stereotaxic surgery..."


def parse_entity_list(section_body: str) -> list[dict]:
    """Parse a Materials/Reagents or Equipment section into entries.
    Each <list-item> or numbered <p> is one entity; skip header-like paragraphs.
    """
    entries = []
    items = re.findall(r"<list-item[^>]*>(.*?)</list-item>", section_body, re.DOTALL)
    if not items:
        items = re.findall(r"<p[^>]*>(.*?)</p>", section_body, re.DOTALL)
    for it in items:
        t = strip_tags(it)
        if len(t) < 5 or len(t) > 600:
            continue
        # Drop header-like lines: "Reagents", "Equipment", "A. Foo", all-caps labels
        if re.match(r"^[A-Z]\.\s", t): continue
        if len(t.split()) <= 3 and t[0].isupper(): continue
        # strip leading "N. " numbering
        t_clean = re.sub(r"^\s*\d+\.\s+", "", t)
        vendor, catalog = "", ""
        m = re.search(r"\(([^()]+?)\s*,\s*(?:cat(?:alog)?[\.\s#]*(?:number|no\.?)?\s*:?\s*)?([A-Za-z0-9\-/.]+)\)", t_clean, re.IGNORECASE)
        if m:
            vendor = m.group(1).strip()
            catalog = m.group(2).strip()
        else:
            m2 = re.search(r"catalog\s*(?:number|no\.?|#)\s*[:\s]*([A-Za-z0-9\-/.]+)", t_clean, re.IGNORECASE)
            if m2:
                catalog = m2.group(1)
        name = re.split(r"[\(,]", t_clean, 1)[0].strip().rstrip(".")
        if not name or len(name) < 3:
            continue
        entries.append({"name": name[:200], "vendor": vendor, "catalog_id": catalog, "raw": t_clean[:400]})
    return entries


def parse_numbered_steps(section_body: str) -> list[dict]:
    """Bio-protocol procedures use flat <p> tags with 'N.' numbering and letter-prefixed sub-headings."""
    current_section = ""
    steps = []
    for pm in re.finditer(r"<p[^>]*>(.*?)</p>", section_body, re.DOTALL):
        t = strip_tags(pm.group(1))
        if not t: continue
        if _LETTER_HEADER.match(t) and len(t) < 200:
            current_section = t
            continue
        nm = _NUMBERED_P.match(t)
        if nm:
            steps.append({
                "step_no": nm.group(1),
                "text": nm.group(2).strip()[:2000],
                "section": current_section,
                "duration": "",
            })
    return steps


def parse(xml: str) -> dict:
    meta = extract_meta(xml)
    mats_body = extract_sec(xml, r"Materials and reagents") or extract_sec(xml, r"Materials")
    eq_body = extract_sec(xml, r"Equipment")
    proc_body = extract_sec(xml, r"Procedure")

    reagents_raw = parse_entity_list(mats_body)
    # Convert to schema reagents
    reagents = [{"name": e["name"], "vendor": e["vendor"], "catalog_id": e["catalog_id"],
                 "rrid": "", "category": ""} for e in reagents_raw]
    equipment = [{"name": e["name"], "vendor": e["vendor"], "model": e["catalog_id"]}
                 for e in parse_entity_list(eq_body)]

    # Steps: try (a) list-items, (b) nested sub-secs, (c) flat numbered paragraphs
    steps = []
    for num, text in parse_list_items(proc_body):
        steps.append({"step_no": num, "text": text[:2000], "section": "", "duration": ""})
    if not steps:
        for secm in re.finditer(r"<sec\b[^>]*>\s*<title[^>]*>(.*?)</title>(.*?)</sec>",
                                 proc_body, re.DOTALL):
            sec_title = strip_tags(secm.group(1))
            for num, text in parse_list_items(secm.group(2)):
                steps.append({"step_no": num, "text": text[:2000], "section": sec_title, "duration": ""})
    if not steps:
        steps = parse_numbered_steps(proc_body)

    # Fallback: mine inline `Reagent (Vendor, cat# X)` mentions from the whole
    #   article if the Materials section didn't yield enough entries.
    if len(reagents) < 3:
        have = {r["name"].lower() for r in reagents}
        for r in _mine_inline(strip_tags(xml)):
            if r["name"].lower() not in have:
                reagents.append(r); have.add(r["name"].lower())

    materials_raw = strip_tags(mats_body)[:5000]
    if len(materials_raw) < 150 and reagents:
        materials_raw = "\n".join(
            f"{r['name']} ({r.get('vendor','')}, {r.get('catalog_id','')})"
            for r in reagents
        )[:5000]
    troubles_sec = extract_sec(xml, r"(?:General notes and )?[Tt]roubleshooting")
    troubles = []
    if troubles_sec:
        # split by heading or numbered items
        for num, text in parse_list_items(troubles_sec):
            troubles.append({"problem": text[:300], "solution": ""})

    return {
        **meta,
        "source": "bioprot",
        "reagents": reagents,
        "equipment": equipment,
        "materials_raw": materials_raw,
        "steps": steps,
        "troubleshooting": troubles,
        "timing": "",
        "parser_version": VERSION,
    }
