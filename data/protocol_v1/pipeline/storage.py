"""Append-only JSONL sharded by source + manifest of seen IDs (resume support)."""
import json, os, hashlib, time
from threading import Lock


class Storage:
    def __init__(self, root: str):
        self.root = root
        self.parsed_dir = os.path.join(root, "parsed")
        self.rejected_dir = os.path.join(root, "rejected")
        os.makedirs(self.parsed_dir, exist_ok=True)
        os.makedirs(self.rejected_dir, exist_ok=True)
        self.manifest_path = os.path.join(root, "manifest.jsonl")
        self._lock = Lock()
        self._seen = self._load_manifest()

    def _load_manifest(self) -> set[str]:
        seen = set()
        if os.path.exists(self.manifest_path):
            with open(self.manifest_path) as f:
                for line in f:
                    try:
                        seen.add(json.loads(line)["id"])
                    except Exception:
                        pass
        return seen

    def seen(self, proto_id: str) -> bool:
        return proto_id in self._seen

    def save(self, proto_dict: dict) -> str:
        source = proto_dict.get("source", "unknown")
        pid = proto_dict["id"]
        ok = proto_dict.get("qc_pass")
        target_dir = self.parsed_dir if ok else self.rejected_dir
        shard_path = os.path.join(target_dir, f"{source}.jsonl")
        line = json.dumps(proto_dict, ensure_ascii=False)
        with self._lock:
            with open(shard_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
            with open(self.manifest_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "id": pid, "source": source, "qc_pass": ok,
                    "qc_score": proto_dict.get("qc_score"),
                    "qc_flags": proto_dict.get("qc_flags"),
                    "doi": proto_dict.get("doi"),
                    "pmcid": proto_dict.get("pmcid"),
                    "ts": int(time.time()),
                }) + "\n")
            self._seen.add(pid)
        return shard_path

    def stats(self) -> dict:
        n_pass = n_fail = 0
        by_source: dict[str, dict] = {}
        if not os.path.exists(self.manifest_path):
            return {"total": 0}
        with open(self.manifest_path) as f:
            for line in f:
                try:
                    m = json.loads(line)
                except Exception:
                    continue
                s = m.get("source", "?")
                d = by_source.setdefault(s, {"pass": 0, "fail": 0})
                if m.get("qc_pass"):
                    d["pass"] += 1; n_pass += 1
                else:
                    d["fail"] += 1; n_fail += 1
        return {"pass": n_pass, "fail": n_fail, "total": n_pass + n_fail, "by_source": by_source}
