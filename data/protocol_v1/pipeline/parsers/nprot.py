"""Nature Protocols parser. Sections: Reagents, Equipment, Reagent setup, Equipment setup, Procedure, Timing, Troubleshooting."""
from .base import extract_sec, extract_meta, parse_list_items, strip_tags, extract_troubleshooting
from .bioprot import parse_entity_list
import re

VERSION = "nprot-0.1"


def parse(xml: str) -> dict:
    meta = extract_meta(xml)
    reagents_body = extract_sec(xml, r"Reagents")
    equip_body = extract_sec(xml, r"Equipment")
    proc_body = extract_sec(xml, r"Procedure")
    reagent_setup = extract_sec(xml, r"Reagent setup")
    equip_setup = extract_sec(xml, r"Equipment setup")

    reagents = [{"name": e["name"], "vendor": e["vendor"], "catalog_id": e["catalog_id"],
                 "rrid": "", "category": ""} for e in parse_entity_list(reagents_body)]
    equipment = [{"name": e["name"], "vendor": e["vendor"], "model": e["catalog_id"]}
                 for e in parse_entity_list(equip_body)]

    steps = []
    # procedure often has sub-sections
    for secm in re.finditer(r"<sec\b[^>]*>\s*<title[^>]*>(.*?)</title>(.*?)</sec>",
                             proc_body, re.DOTALL):
        sec_title = strip_tags(secm.group(1))
        for num, text in parse_list_items(secm.group(2)):
            steps.append({"step_no": num, "text": text[:2000], "section": sec_title, "duration": ""})
    if not steps:
        for num, text in parse_list_items(proc_body):
            steps.append({"step_no": num, "text": text[:2000], "section": "", "duration": ""})

    materials_raw = (strip_tags(reagents_body) + "\n" +
                     strip_tags(equip_body) + "\n" +
                     strip_tags(reagent_setup) + "\n" +
                     strip_tags(equip_setup))[:8000]

    timing_sec = extract_sec(xml, r"Timing")
    timing = strip_tags(timing_sec)[:500]
    troubles = extract_troubleshooting(xml)
    if not troubles:
        tb = extract_sec(xml, r"Troubleshooting")
        if tb:
            for num, text in parse_list_items(tb):
                troubles.append({"problem": text[:500], "solution": ""})

    return {
        **meta,
        "source": "nprot",
        "reagents": reagents,
        "equipment": equipment,
        "materials_raw": materials_raw,
        "steps": steps,
        "troubleshooting": troubles,
        "timing": timing,
        "parser_version": VERSION,
    }
