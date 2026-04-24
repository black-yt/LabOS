"""Print corpus summary across sources."""
import json, os, sys
from collections import Counter


def load(path):
    if not os.path.exists(path): return []
    return [json.loads(l) for l in open(path)]


def report(data_dir: str):
    parsed_dir = os.path.join(data_dir, "parsed")
    rej_dir = os.path.join(data_dir, "rejected")
    sources = {f.replace(".jsonl","") for f in os.listdir(parsed_dir)} if os.path.exists(parsed_dir) else set()
    print(f"{'source':<10}{'pass':>6}{'fail':>6}  {'med_reag':>9}{'med_eq':>8}{'med_step':>10}{'avg_score':>11}  flags (top3)")
    print("-"*90)
    for s in sorted(sources):
        recs = load(os.path.join(parsed_dir, f"{s}.jsonl"))
        rej = load(os.path.join(rej_dir, f"{s}.jsonl"))
        if not recs and not rej: continue
        med = lambda xs: sorted(xs)[len(xs)//2] if xs else 0
        reag = [len(r["reagents"]) for r in recs]
        eq = [len(r["equipment"]) for r in recs]
        steps = [len(r["steps"]) for r in recs]
        avg_score = sum(r["qc_score"] for r in recs)/len(recs) if recs else 0
        c = Counter()
        for r in rej:
            for f in r["qc_flags"]: c[f]+=1
        topflags = ", ".join(f"{k}={v}" for k,v in c.most_common(3))
        print(f"{s:<10}{len(recs):>6}{len(rej):>6}  {med(reag):>9}{med(eq):>8}{med(steps):>10}{avg_score:>11.2f}  {topflags}")


if __name__ == "__main__":
    report(sys.argv[1] if len(sys.argv)>1 else os.path.join(os.path.dirname(__file__), "..", "data"))
