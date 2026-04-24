"""STAR Protocols parser — KRT + Materials and equipment + Step-by-step method details."""
import re
from .base import extract_sec, extract_meta, parse_table, parse_list_items, strip_tags, extract_troubleshooting

VERSION = "star-0.2"


def parse_KRT(xml: str) -> tuple[list[dict], list[dict]]:
    """Parse Key Resources Table → (reagents, equipment).
    KRT rows are labeled by category sub-headers; equipment goes to equipment, everything else to reagents.
    """
    krt = extract_sec(xml, r"Key resources table")
    if not krt:
        return [], []
    rows = parse_table(krt)
    reagents, equipment = [], []
    current_cat = ""
    EQUIP_CATS = {"software and algorithms", "other", "equipment", "instruments"}
    for row in rows:
        if not row or all(not c for c in row):
            continue
        # Header row
        if len(row) == 1 or (row and row[0] and all(not c for c in row[1:] if c is not None)):
            current_cat = row[0].lower().strip()
            continue
        # Skip title row
        if row and row[0] and "REAGENT" in row[0].upper():
            continue
        if len(row) < 3:
            continue
        name, source, ident = row[0], row[1], row[2]
        if not name:
            continue
        rrid_m = re.search(r"RRID\s*:\s*(\S+)", ident)
        # strip RRID out of ident before extracting Cat#
        ident_clean = re.sub(r"\s*;?\s*RRID\s*:\s*\S+", "", ident).strip(" ;")
        cat_m = re.search(r"Cat#?\s*([A-Za-z0-9\-/.]+)", ident_clean)
        catalog = cat_m.group(1) if cat_m else ident_clean
        entry = {
            "name": name,
            "vendor": source,
            "catalog_id": catalog,
            "rrid": rrid_m.group(1) if rrid_m else "",
            "category": current_cat,
        }
        if any(k in current_cat for k in ("software", "equipment", "instrument", "other")) or \
           any(k in name.lower() for k in ("centrifuge", "microscope", "incubator", "thermocycler",
                                            "cytometer", "spectrophotometer", "scanner")):
            equipment.append({"name": name, "vendor": source, "model": catalog})
        else:
            reagents.append(entry)
    return reagents, equipment


def parse_steps(xml: str) -> list[dict]:
    body = extract_sec(xml, r"Step-by-step method details")
    if not body:
        return []
    # collect sub-section titles to attach to each step
    out = []
    # walk: for each <sec> inside body, get its title then its list-items
    for secm in re.finditer(r"<sec\b[^>]*>\s*<title[^>]*>(.*?)</title>(.*?)</sec>", body, re.DOTALL):
        section_title = strip_tags(secm.group(1))
        section_body = secm.group(2)
        for num, text in parse_list_items(section_body):
            out.append({"step_no": num, "text": text[:2000], "section": section_title, "duration": ""})
    # fallback: flat list items if no sub-secs
    if not out:
        for num, text in parse_list_items(body):
            out.append({"step_no": num, "text": text[:2000], "section": "", "duration": ""})
    return out


def parse(xml: str) -> dict:
    meta = extract_meta(xml)
    reagents, equipment = parse_KRT(xml)
    steps = parse_steps(xml)
    me = extract_sec(xml, r"Materials and equipment")
    materials_raw = strip_tags(me)[:5000]
    # STAR fallback: when the optional "Materials and equipment" section is
    #   absent and the KRT had no rows tagged as equipment, synthesize
    #   materials_raw from the reagent list so the gate can still count a big
    #   KRT as adequate materials documentation.
    if len(materials_raw) < 150 and len(reagents) >= 5:
        materials_raw = "\n".join(
            f"{r['name']} ({r.get('vendor','')}, {r.get('catalog_id','')})"
            for r in reagents
        )[:5000]
    troubles = extract_troubleshooting(xml)
    timing_sec = extract_sec(xml, r"Timing")
    timing = strip_tags(timing_sec)[:500]
    return {
        **meta,
        "source": "star",
        "reagents": reagents,
        "equipment": equipment,
        "materials_raw": materials_raw,
        "steps": steps,
        "troubleshooting": troubles,
        "timing": timing,
        "parser_version": VERSION,
    }
