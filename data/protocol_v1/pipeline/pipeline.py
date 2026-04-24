"""Orchestrator: search → fetch → parse → validate → store."""
import time, datetime, logging
from .europepmc import EuropePMC
from .parsers import REGISTRY
from .schema import Protocol, validate
from .storage import Storage

log = logging.getLogger(__name__)


SOURCE_QUERIES = {
    "star":    'JOURNAL:"STAR protocols" OPEN_ACCESS:Y',
    "bioprot": 'JOURNAL:"Bio-protocol" OPEN_ACCESS:Y',
    "nprot":   'JOURNAL:"Nat Protoc" OPEN_ACCESS:Y',
    # Current Protocols: structure close to Nat Protoc → reuse nprot parser
    "curprot": '(JOURNAL:"Curr Protoc" OR JOURNAL:"Current Protocols") OPEN_ACCESS:Y',
    # Methods in Molecular Biology: prose-based, tune bioprot parser
    "mimb":    'JOURNAL:"Methods Mol Biol" OPEN_ACCESS:Y',
    # Nature Methods: mixed journal — gate + parser filter non-protocols
    # JoVE: Protocol section + Table of Materials (only ~40% have the materials
    # table preserved in the PMC XML; the rest are filtered by the gate).
    "jove":    'JOURNAL:"J Vis Exp" OPEN_ACCESS:Y',
    # Nature Methods uses the standard research-article layout (Main/Results/Methods),
    # not a protocol layout. Pilot yield was near-zero without prose-level NLP.
    # Left wired so a future LLM-extraction pass can re-enable it.
    # "nmeth":   'JOURNAL:"Nat Methods" OPEN_ACCESS:Y',
}


def dict_to_protocol(d: dict) -> Protocol:
    pid = f"{d['source']}:{d.get('pmcid') or d.get('doi')}"
    return Protocol(
        id=pid,
        source=d["source"],
        title=d.get("title", ""),
        doi=d.get("doi", ""),
        pmcid=d.get("pmcid", ""),
        pmid=d.get("pmid", ""),
        license=d.get("license", ""),
        journal=d.get("journal", ""),
        pub_year=d.get("pub_year", ""),
        authors=d.get("authors", []),
        abstract=d.get("abstract", ""),
        reagents=d.get("reagents", []),
        equipment=d.get("equipment", []),
        materials_raw=d.get("materials_raw", ""),
        steps=d.get("steps", []),
        troubleshooting=d.get("troubleshooting", []),
        timing=d.get("timing", ""),
        fetched_at=datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        parser_version=d.get("parser_version", ""),
    )


def run_source(source_key: str, storage: Storage, max_results: int,
                cache_dir: str, rate: float = 4.0):
    assert source_key in REGISTRY, source_key
    client = EuropePMC(rate_per_sec=rate, cache_dir=cache_dir)
    parser = REGISTRY[source_key]
    query = SOURCE_QUERIES[source_key]
    log.info("source=%s query=%s limit=%d", source_key, query, max_results)

    stats = {"fetched": 0, "parsed": 0, "pass": 0, "fail": 0, "skipped": 0, "errors": 0}
    for hit in client.search(query, page_size=100, max_results=max_results):
        pmcid = hit.get("pmcid")
        if not pmcid:
            stats["skipped"] += 1; continue
        pid = f"{source_key}:{pmcid}"
        if storage.seen(pid):
            stats["skipped"] += 1; continue
        try:
            xml = client.fulltext_xml(pmcid)
            stats["fetched"] += 1
            parsed = parser(xml)
            parsed["source"] = source_key
            proto = dict_to_protocol(parsed)
            validate(proto)
            storage.save(proto.to_dict())
            stats["parsed"] += 1
            stats["pass" if proto.qc_pass else "fail"] += 1
            if stats["parsed"] % 25 == 0:
                log.info("  progress: %s", stats)
        except Exception as e:
            stats["errors"] += 1
            log.warning("  err pmcid=%s: %s", pmcid, str(e)[:120])
    return stats
