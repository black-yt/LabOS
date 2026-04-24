"""Current Protocols parser.

Structure in PMC fulltext XML:
  - Multiple sibling <sec><title>Materials</title>...</sec> blocks (one per
    sub-protocol). Items inside are <list-item>/<p> entries, same as Bio-protocol.
  - Step-containing sections are rendered as a title-only <sec> followed by a
    sibling <sec> containing <list list-type="simple" specific-use="protocol-steps">.
    Easiest capture: collect every <list> whose `specific-use` attribute is
    "protocol-steps".
  - "REAGENTS AND SOLUTIONS" recipe block lives in its own section; fold into
    materials_raw for completeness.
"""
import re
from .base import extract_sec, extract_meta, strip_tags, extract_troubleshooting
from .bioprot import parse_entity_list, _mine_inline

VERSION = "curprot-0.2"


def _iter_sections_by_title(xml: str, title_pattern: str):
    """Yield the body of every <sec> whose <title> matches (not just the first)."""
    for m in re.finditer(
        rf"<sec\b[^>]*>\s*(?:<label[^>]*>[^<]*</label>\s*)?<title[^>]*>\s*{title_pattern}\s*</title>",
        xml, re.IGNORECASE | re.DOTALL,
    ):
        start = m.start()
        depth = 0
        for tag in re.finditer(r"</?sec\b[^>]*>", xml[start:]):
            if tag.group().startswith("</"):
                depth -= 1
                if depth == 0:
                    yield xml[start + m.end() - m.start(): start + tag.start()]
                    break
            else:
                depth += 1


_NUM_LABEL = re.compile(r"^\s*\d+[a-z]?\.?\s*$")


def _parse_protocol_step_lists(xml: str) -> list[dict]:
    """Extract steps.

    Strategy: walk the document and track the most recent <title>. Emit a step
    for every <list-item> that carries a numeric <label> (e.g. "1", "2a") — this
    naturally skips Materials entries (unnumbered) while capturing procedure
    lists regardless of whether they use `specific-use="protocol-steps"`.
    """
    steps = []
    current_section = ""
    for m in re.finditer(
        r"<title[^>]*>(.*?)</title>|<list-item\b[^>]*>(.*?)</list-item>",
        xml, re.DOTALL,
    ):
        if m.group(1) is not None:
            title = strip_tags(m.group(1))
            if title and len(title) < 200:
                current_section = title
            continue
        it = m.group(2)
        lab = re.search(r"<label[^>]*>([^<]+)</label>", it)
        if not lab or not _NUM_LABEL.match(lab.group(1)):
            continue
        text = strip_tags(re.sub(r"<label[^>]*>[^<]*</label>", "", it))
        if len(text) < 10:
            continue
        steps.append({
            "step_no": lab.group(1).strip().rstrip("."),
            "text": text[:2000],
            "section": current_section,
            "duration": "",
        })
    return steps


def parse(xml: str) -> dict:
    meta = extract_meta(xml)

    reagents, equipment = [], []
    materials_raw_parts = []
    for mats_body in _iter_sections_by_title(xml, r"Materials"):
        entries = parse_entity_list(mats_body)
        for e in entries:
            raw_low = e["raw"].lower()
            if any(w in raw_low for w in ("centrifuge", "microscope", "incubator",
                                          "thermocycler", "cytometer", "spectrophotometer",
                                          "pipettor", "software", "heat block",
                                          "shaker", "sonicator", "scanner")):
                equipment.append({"name": e["name"], "vendor": e["vendor"], "model": e["catalog_id"]})
            else:
                reagents.append({"name": e["name"], "vendor": e["vendor"],
                                 "catalog_id": e["catalog_id"], "rrid": "", "category": ""})
        materials_raw_parts.append(strip_tags(mats_body))

    # Include the shared "REAGENTS AND SOLUTIONS" block (recipes) in materials_raw.
    recipes = extract_sec(xml, r"REAGENTS AND SOLUTIONS")
    if recipes:
        materials_raw_parts.append(strip_tags(recipes))

    steps = _parse_protocol_step_lists(xml)

    if len(reagents) < 3:
        have = {r["name"].lower() for r in reagents}
        for r in _mine_inline(strip_tags(xml)):
            if r["name"].lower() not in have:
                reagents.append(r); have.add(r["name"].lower())

    materials_raw = "\n".join(materials_raw_parts)[:8000]
    if len(materials_raw) < 150 and reagents:
        materials_raw = "\n".join(
            f"{r['name']} ({r.get('vendor','')}, {r.get('catalog_id','')})"
            for r in reagents
        )[:8000]
    troubles = extract_troubleshooting(xml)
    return {
        **meta,
        "source": "curprot",
        "reagents": reagents,
        "equipment": equipment,
        "materials_raw": materials_raw,
        "steps": steps,
        "troubleshooting": troubles,
        "timing": "",
        "parser_version": VERSION,
    }
