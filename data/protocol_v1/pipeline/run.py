"""CLI entry: python -m crawler.run --source star --limit 200"""
import argparse, logging, os, sys, json
from .pipeline import run_source, SOURCE_QUERIES
from .storage import Storage


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=list(SOURCE_QUERIES.keys()) + ["all"], default="all")
    ap.add_argument("--limit", type=int, default=100, help="per-source max results")
    ap.add_argument("--data-dir", default=os.path.join(os.path.dirname(__file__), "..", "data"))
    ap.add_argument("--cache-dir", default=os.path.join(os.path.dirname(__file__), "..", "data", "raw"))
    ap.add_argument("--rate", type=float, default=4.0, help="requests/sec to EuroPMC")
    ap.add_argument("--stats", action="store_true", help="print manifest stats and exit")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    data_dir = os.path.abspath(args.data_dir)
    cache_dir = os.path.abspath(args.cache_dir)
    os.makedirs(data_dir, exist_ok=True)
    storage = Storage(data_dir)

    if args.stats:
        print(json.dumps(storage.stats(), indent=2, default=str))
        return

    sources = list(SOURCE_QUERIES.keys()) if args.source == "all" else [args.source]
    all_stats = {}
    for s in sources:
        all_stats[s] = run_source(s, storage, args.limit, cache_dir=cache_dir, rate=args.rate)

    print("\n=== RUN SUMMARY ===")
    print(json.dumps(all_stats, indent=2))
    print("\n=== CUMULATIVE ===")
    print(json.dumps(storage.stats(), indent=2, default=str))


if __name__ == "__main__":
    main()
