"""Re-parse cached XMLs for records that previously failed the gate.

Iterates every line in data/rejected/<source>.jsonl, loads the cached XML/HTML
from disk, re-runs the current parser, and (a) promotes passing records to
data/parsed/<source>.jsonl, (b) rewrites data/rejected/<source>.jsonl with only
the still-failing records, (c) rewrites the manifest entry.

Usage:
    python3 -m crawler.reparse --source jove
    python3 -m crawler.reparse --source oww
"""
from __future__ import annotations
import argparse, json, os, logging, datetime
from .parsers import REGISTRY
from .schema import validate
from .pipeline import dict_to_protocol
from .storage import Storage

log = logging.getLogger(__name__)


def _load_oww_html(pageid: str, cache_dir: str) -> tuple[str, dict]:
    path = os.path.join(cache_dir, f"{pageid}.html")
    with open(path, encoding="utf-8") as f:
        return f.read()


def reparse_source(source: str, data_dir: str) -> dict:
    parsed_path = os.path.join(data_dir, "parsed", f"{source}.jsonl")
    rejected_path = os.path.join(data_dir, "rejected", f"{source}.jsonl")
    manifest_path = os.path.join(data_dir, "manifest.jsonl")
    if not os.path.exists(rejected_path):
        return {"error": f"no rejected file: {rejected_path}"}

    # load previously-rejected records
    old_fail = [json.loads(l) for l in open(rejected_path, encoding="utf-8")]
    log.info("source=%s rejected_in=%d", source, len(old_fail))

    # current state on disk
    still_fail: list[dict] = []
    promoted: list[dict] = []
    errors = 0

    if source == "oww":
        from . import openwetware as oww
        cache = os.path.join(data_dir, "raw_oww")
        for old in old_fail:
            pageid = old["id"].split(":", 1)[1]
            path = os.path.join(cache, f"{pageid}.html")
            if not os.path.exists(path):
                still_fail.append(old); continue
            try:
                html = open(path, encoding="utf-8").read()
                d = oww.parse(html, old["title"], "")
                d["id"] = old["id"]
                proto = dict_to_protocol(d)
                proto.id = old["id"]
                validate(proto)
                rec = proto.to_dict()
                (promoted if proto.qc_pass else still_fail).append(rec)
            except Exception as e:
                errors += 1
                still_fail.append(old)
                log.warning("err %s: %s", old.get("id"), str(e)[:120])
    else:
        parser = REGISTRY[source]
        cache = os.path.join(data_dir, "raw")
        for old in old_fail:
            pmcid = old.get("pmcid")
            if not pmcid:
                still_fail.append(old); continue
            path = os.path.join(cache, f"{pmcid}.xml")
            if not os.path.exists(path):
                still_fail.append(old); continue
            try:
                xml = open(path, encoding="utf-8", errors="replace").read()
                d = parser(xml)
                d["source"] = source
                proto = dict_to_protocol(d)
                validate(proto)
                rec = proto.to_dict()
                (promoted if proto.qc_pass else still_fail).append(rec)
            except Exception as e:
                errors += 1
                still_fail.append(old)
                log.warning("err %s: %s", pmcid, str(e)[:120])

    # Rewrite files atomically via .tmp
    def _rewrite(path: str, records: list[dict]):
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        os.replace(tmp, path)

    # append promoted to parsed file
    with open(parsed_path, "a", encoding="utf-8") as f:
        for r in promoted:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    _rewrite(rejected_path, still_fail)

    # rewrite manifest: flip qc_pass on promoted IDs
    promoted_ids = {r["id"] for r in promoted}
    still_ids = {r["id"] for r in still_fail}
    if promoted_ids:
        out = []
        with open(manifest_path, encoding="utf-8") as f:
            for line in f:
                try:
                    m = json.loads(line)
                except Exception:
                    out.append(line); continue
                if m.get("id") in promoted_ids:
                    # find matching promoted rec for updated score
                    rec = next((p for p in promoted if p["id"] == m["id"]), None)
                    if rec:
                        m["qc_pass"] = True
                        m["qc_score"] = rec.get("qc_score")
                        m["qc_flags"] = rec.get("qc_flags")
                out.append(json.dumps(m) + "\n")
        with open(manifest_path + ".tmp", "w", encoding="utf-8") as f:
            f.writelines(out)
        os.replace(manifest_path + ".tmp", manifest_path)

    return {
        "source": source,
        "previously_failed": len(old_fail),
        "now_passing": len(promoted),
        "still_failing": len(still_fail),
        "errors": errors,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True,
                    help="source key (e.g. jove, oww, curprot, mimb)")
    ap.add_argument("--data-dir",
                    default=os.path.join(os.path.dirname(__file__), "..", "data"))
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    r = reparse_source(args.source, os.path.abspath(args.data_dir))
    print(json.dumps(r, indent=2))


if __name__ == "__main__":
    main()
