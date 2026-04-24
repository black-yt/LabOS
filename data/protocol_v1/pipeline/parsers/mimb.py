"""Methods in Molecular Biology parser.

MiMB chapters share Bio-protocol's prose style but use different section names:
  - "Materials" (with nested numbered <list list-type="order"> sub-sections)
  - "Methods" (not "Procedure") with <list list-type="order"> steps
"""
import re
from .base import (extract_sec, extract_meta, parse_list_items, strip_tags,
                   extract_troubleshooting)
from .bioprot import parse_entity_list, parse_numbered_steps, _mine_inline

VERSION = "mimb-0.2"


def parse(xml: str) -> dict:
    meta = extract_meta(xml)
    mats_body = extract_sec(xml, r"Materials(?:\s+and\s+[Rr]eagents)?")
    methods_body = (extract_sec(xml, r"Methods")
                    or extract_sec(xml, r"Procedure"))

    reagents_raw = parse_entity_list(mats_body)
    reagents = [{"name": e["name"], "vendor": e["vendor"], "catalog_id": e["catalog_id"],
                 "rrid": "", "category": ""} for e in reagents_raw]
    equipment = []  # MiMB rarely separates; items live under Materials

    steps = []
    # First pass: numbered <list-item>s anywhere in methods (covers <list list-type="order">)
    for num, text in parse_list_items(methods_body):
        steps.append({"step_no": num, "text": text[:2000], "section": "", "duration": ""})
    # Second pass: nested sub-secs (procedure with sub-headings)
    if not steps:
        for secm in re.finditer(
            r"<sec\b[^>]*>\s*(?:<label[^>]*>[^<]*</label>\s*)?"
            r"<title[^>]*>(.*?)</title>(.*?)</sec>",
            methods_body, re.DOTALL,
        ):
            sec_title = strip_tags(secm.group(1))
            for num, text in parse_list_items(secm.group(2)):
                steps.append({"step_no": num, "text": text[:2000],
                              "section": sec_title, "duration": ""})
    # Fallback: flat numbered paragraphs (Bio-protocol-style)
    if not steps:
        steps = parse_numbered_steps(methods_body)

    if len(reagents) < 3:
        have = {r["name"].lower() for r in reagents}
        for r in _mine_inline(strip_tags(xml)):
            if r["name"].lower() not in have:
                reagents.append(r); have.add(r["name"].lower())

    if not steps:
        # Last resort: flat <p> in Methods body, one paragraph per step
        idx = 0
        for pm in re.finditer(r"<p[^>]*>(.*?)</p>", methods_body, re.DOTALL):
            t = strip_tags(pm.group(1))
            if 20 < len(t) < 2000:
                idx += 1
                steps.append({"step_no": str(idx), "text": t[:2000],
                              "section": "", "duration": ""})

    materials_raw = strip_tags(mats_body)[:5000]
    if len(materials_raw) < 150 and reagents:
        materials_raw = "\n".join(
            f"{r['name']} ({r.get('vendor','')}, {r.get('catalog_id','')})"
            for r in reagents
        )[:5000]
    troubles = extract_troubleshooting(xml)
    if not troubles:
        notes = extract_sec(xml, r"Notes?")
        if notes:
            for num, text in parse_list_items(notes):
                troubles.append({"problem": text[:300], "solution": ""})

    return {
        **meta,
        "source": "mimb",
        "reagents": reagents,
        "equipment": equipment,
        "materials_raw": materials_raw,
        "steps": steps,
        "troubleshooting": troubles,
        "timing": "",
        "parser_version": VERSION,
    }
