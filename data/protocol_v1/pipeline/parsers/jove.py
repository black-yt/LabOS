"""JoVE (J Vis Exp) parser.

JoVE articles on PubMed Central commonly contain:
  - a <sec><title>Protocol</title>...</sec> section with nested numbered steps
  - a <sec> whose title matches "Materials"/"Table of Materials"/"Reagents"
    OR a <table-wrap> whose caption/label contains "Materials"
Reagent tables usually have columns like: Name / Company / Catalog Number / Comments.
"""
import re
from .base import (extract_sec, extract_meta, parse_list_items,
                   parse_table, strip_tags, extract_troubleshooting)

VERSION = "jove-0.2"

_VENDOR_CAT_RX = re.compile(
    r"([A-Za-z][^\[\](),;\n<>]{2,120}?)\s*\(\s*([A-Z][\w .&'/-]{2,40}?)\s*,\s*"
    r"(?:cat(?:alog)?[\.\s#]*(?:number|no\.?|#)?\s*:?\s*)?([A-Za-z0-9][A-Za-z0-9\-/.]{2,30})\s*\)",
)


def _mine_inline_reagents(text: str) -> list[dict]:
    out, seen = [], set()
    for m in _VENDOR_CAT_RX.finditer(text):
        name = m.group(1).strip().rstrip(".,;:")
        vendor = m.group(2).strip()
        cat = m.group(3).strip()
        name = re.sub(r"^(?:using|with|from|add|the|a|an)\s+", "", name, flags=re.I)
        key = name.lower()
        if key in seen or len(name) < 3 or len(name) > 150:
            continue
        if len(cat) < 2 or cat.isalpha() and len(cat) < 4:
            continue
        seen.add(key)
        out.append({"name": name[:200], "vendor": vendor,
                    "catalog_id": cat, "rrid": "", "category": ""})
    return out


_MATERIALS_CAPTION = re.compile(
    r"table\s+of\s+materials|^\s*materials?\s*$|"
    r"^\s*reagents?(\s+and\s+equipment)?\s*$|"
    r"name\s+of\s+(material|reagent|equipment)",
    re.IGNORECASE,
)


def _find_materials_table(xml: str) -> list[list[str]]:
    """Locate the JoVE-style Table of Materials.

    Three fallback paths:
      1) <sec> titled "Table of Materials" / "Materials" / "Reagents" with a table inside.
      2) Any <table-wrap> whose caption exactly matches a JoVE materials caption.
      3) Any <table-wrap> whose first data row header looks like the JoVE schema
         (columns: Name of Material/Reagent/Equipment).
    """
    mats_sec = (extract_sec(xml, r"Table of [Mm]aterials")
                or extract_sec(xml, r"Materials")
                or extract_sec(xml, r"Reagents(?: and equipment)?"))
    if mats_sec:
        rows = parse_table(mats_sec)
        if rows:
            return rows

    for m in re.finditer(r"<table-wrap\b[^>]*>(.*?)</table-wrap>", xml, re.DOTALL):
        body = m.group(1)
        cap_m = re.search(r"<caption[^>]*>(.*?)</caption>", body, re.DOTALL)
        cap = strip_tags(cap_m.group(1)) if cap_m else ""
        if _MATERIALS_CAPTION.search(cap):
            rows = parse_table(body)
            if rows:
                return rows

    # Header-sniff fallback: column[0] looks like "Name of Material/Equipment..."
    for m in re.finditer(r"<table-wrap\b[^>]*>(.*?)</table-wrap>", xml, re.DOTALL):
        body = m.group(1)
        rows = parse_table(body)
        if not rows or not rows[0]:
            continue
        hdr0 = rows[0][0].lower() if rows[0][0] else ""
        if re.search(r"name of (material|reagent|equipment)", hdr0):
            return rows
    return []


def _rows_to_reagents_equipment(rows: list[list[str]]):
    """Split JoVE materials table into reagents/equipment.
    Heuristic: columns are typically [Name, Company, Catalog#, Comments].
    Move items whose Name/Comments look like equipment to equipment list.
    """
    if not rows:
        return [], []
    header = [c.lower() for c in rows[0]]
    start_idx = 1 if any("name" in c or "reagent" in c or "material" in c for c in header) else 0

    EQUIP_WORDS = ("centrifuge", "microscope", "incubator", "thermocycler",
                   "cytometer", "spectrophotometer", "scanner", "pipette",
                   "pipettor", "shaker", "balance", "sonicator", "software",
                   "camera", "printer", "oven", "hood", "freezer", "analyzer",
                   "chamber", "filter holder", "system")

    reagents, equipment = [], []
    for row in rows[start_idx:]:
        cells = [c.strip() for c in row if c is not None]
        if not cells or not cells[0]:
            continue
        if len(cells) < 2:
            continue
        name = cells[0]
        vendor = cells[1] if len(cells) > 1 else ""
        catalog = cells[2] if len(cells) > 2 else ""
        if len(name) < 2 or len(name) > 300:
            continue
        low = (name + " " + (cells[-1] if len(cells) > 3 else "")).lower()
        if any(w in low for w in EQUIP_WORDS):
            equipment.append({"name": name[:200], "vendor": vendor, "model": catalog})
        else:
            reagents.append({
                "name": name[:200], "vendor": vendor, "catalog_id": catalog,
                "rrid": "", "category": "",
            })
    return reagents, equipment


def parse_steps(xml: str) -> list[dict]:
    body = extract_sec(xml, r"Protocol(?:\s+\d+)?")
    if not body:
        return []
    out = []
    for secm in re.finditer(r"<sec\b[^>]*>\s*<title[^>]*>(.*?)</title>(.*?)</sec>",
                             body, re.DOTALL):
        sec_title = strip_tags(secm.group(1))
        for num, text in parse_list_items(secm.group(2)):
            out.append({"step_no": num, "text": text[:2000],
                        "section": sec_title, "duration": ""})
    if not out:
        for num, text in parse_list_items(body):
            out.append({"step_no": num, "text": text[:2000], "section": "", "duration": ""})
    return out


def parse(xml: str) -> dict:
    meta = extract_meta(xml)
    rows = _find_materials_table(xml)
    reagents, equipment = _rows_to_reagents_equipment(rows)
    steps = parse_steps(xml)
    # Fallback: Table of Materials isn't in most JoVE PMC XMLs. Mine inline
    # `Reagent (Vendor, Cat# XXX)` citations from the Protocol + Discussion text.
    if len(reagents) < 3:
        mined = _mine_inline_reagents(strip_tags(xml))
        have = {r["name"].lower() for r in reagents}
        for r in mined:
            if r["name"].lower() not in have:
                reagents.append(r); have.add(r["name"].lower())
    mats_sec = (extract_sec(xml, r"Table of [Mm]aterials")
                or extract_sec(xml, r"Materials")
                or extract_sec(xml, r"Reagents(?: and equipment)?"))
    # Fall back to concatenating the table rows we just extracted so the gate's
    # materials_raw>=150 path can still pass when only a table-wrap is present.
    if mats_sec:
        materials_raw = strip_tags(mats_sec)[:5000]
    else:
        materials_raw = "\n".join(
            " | ".join(c for c in row if c) for row in rows if row
        )[:5000]
    if len(materials_raw) < 150 and reagents:
        materials_raw = "\n".join(
            f"{r['name']} ({r.get('vendor','')}, {r.get('catalog_id','')})"
            for r in reagents
        )[:8000]
    troubles = extract_troubleshooting(xml)
    return {
        **meta,
        "source": "jove",
        "reagents": reagents,
        "equipment": equipment,
        "materials_raw": materials_raw,
        "steps": steps,
        "troubleshooting": troubles,
        "timing": "",
        "parser_version": VERSION,
    }
