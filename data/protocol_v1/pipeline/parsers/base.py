"""Common XML helpers."""
import re
import html


def strip_tags(s: str) -> str:
    t = re.sub(r"<[^>]+>", " ", s or "")
    t = html.unescape(t)
    return re.sub(r"\s+", " ", t).strip()


def extract_sec(xml: str, title_pattern: str) -> str:
    """Extract body of a <sec> whose <title> matches. Handles nesting."""
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
                    return xml[start + m.end() - m.start(): start + tag.start()]
            else:
                depth += 1
    return ""


def extract_meta(xml: str) -> dict:
    def find(pat, default=""):
        m = re.search(pat, xml, re.DOTALL)
        return strip_tags(m.group(1)) if m else default
    doi = find(r'<article-id pub-id-type="doi">([^<]+)</article-id>')
    pmcid = find(r'<article-id pub-id-type="pmc(?:id)?">([^<]+)</article-id>')
    pmid = find(r'<article-id pub-id-type="pmid">([^<]+)</article-id>')
    title = find(r"<article-title[^>]*>(.*?)</article-title>")
    journal = find(r"<journal-title[^>]*>(.*?)</journal-title>")
    year = find(r'<pub-date[^>]*>.*?<year>(\d{4})</year>')
    lic = find(r'<license[^>]*xlink:href="([^"]+)"') or find(r"<license[^>]*>(.*?)</license>")
    abstract_sec = re.search(r"<abstract[^>]*>(.*?)</abstract>", xml, re.DOTALL)
    abstract = strip_tags(abstract_sec.group(1)) if abstract_sec else ""
    authors = re.findall(r"<surname>([^<]+)</surname>", xml)[:20]
    return {
        "doi": doi, "pmcid": pmcid, "pmid": pmid, "title": title,
        "journal": journal, "pub_year": year, "license": lic,
        "abstract": abstract, "authors": authors,
    }


def parse_list_items(xml: str, min_len: int = 15) -> list[tuple[str, str]]:
    """Return list of (step_no_hint, text). Step no derived from label tag or leading number."""
    items = re.findall(r"<list-item[^>]*>(.*?)</list-item>", xml, re.DOTALL)
    out = []
    for it in items:
        lab = re.search(r"<label[^>]*>([^<]+)</label>", it)
        text = strip_tags(re.sub(r"<label[^>]*>[^<]*</label>", "", it))
        if len(text) < min_len:
            continue
        num = (lab.group(1).strip() if lab else "")
        if not num:
            m = re.match(r"^\s*(\d+\.?\d*[a-z]?)\s*[.\)]\s*(.+)", text)
            if m:
                num, text = m.group(1), m.group(2)
        out.append((num, text))
    return out


def parse_table(xml_fragment: str) -> list[list[str]]:
    """Parse the first <table-wrap> or <table>; return row-major cells (text)."""
    rows_xml = re.findall(r"<tr[^>]*>(.*?)</tr>", xml_fragment, re.DOTALL)
    rows = []
    for r in rows_xml:
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.DOTALL)
        rows.append([strip_tags(c) for c in cells])
    return rows


def extract_troubleshooting(xml: str) -> list[dict]:
    """Find Problem/Solution pairs under Troubleshooting."""
    body = extract_sec(xml, r"Troubleshooting")
    if not body:
        return []
    out = []
    # pattern: <sec><title>Problem N</title>...</sec><sec><title>Potential solution</title>...</sec>
    probs = re.findall(
        r"<title[^>]*>\s*Problem[^<]*</title>(.*?)(?=<title[^>]*>\s*(?:Problem|Potential solution|$))",
        body, re.DOTALL | re.IGNORECASE,
    )
    sols = re.findall(
        r"<title[^>]*>\s*Potential solution[^<]*</title>(.*?)(?=<title[^>]*>\s*(?:Problem|$))",
        body, re.DOTALL | re.IGNORECASE,
    )
    for p, s in zip(probs, sols):
        out.append({"problem": strip_tags(p)[:500], "solution": strip_tags(s)[:1000]})
    return out
