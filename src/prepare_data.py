import csv, hashlib, json, sys
from collections import Counter
from pathlib import Path

RAW = Path("data/raw/ACVP-Server/gen-val/json-files")
OUT = Path("data/processed")
WANTED = ("prompt.json", "expectedResults.json", "internalProjection.json")
ALGO_DIRS = ["ACVP-AES-GCM-1.0", "ACVP-AES-GMAC-1.0", "ACVP-AES-XPN-1.0", "ACVP-AES-CCM-1.0", "ACVP-AES-CCM-ECMA-1.0"]

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def collect(node, found):
    if isinstance(node, dict):
        k, v = node.get("key"), node.get("iv")
        if isinstance(k, str) and isinstance(v, str) and k and v:
            found.append((k.lower(), v.lower()))
        for child in node.values():
            collect(child, found)
    elif isinstance(node, list):
        for child in node:
            collect(child, found)

def main(raw=RAW, out=OUT):
    raw = Path(raw)
    # ĐÃ SỬA: manifest giờ là một danh sách [] thay vì {}
    found_all, per_algo, manifest, owner = [], {}, [], {}
    
    for algo in ALGO_DIRS:
        folder = raw / algo
        if not folder.is_dir():
            continue
        rows = []
        for name in WANTED:
            p = folder / name
            if p.exists():
                collect(json.loads(p.read_text(encoding="utf-8")), rows)
                manifest.append({"file": str(p), "sha256": sha256_file(p), "bytes": p.stat().st_size})
        uniq = set(rows)
        per_algo[algo] = {"rows_read": len(rows), "unique_pairs": len(uniq)}
        for pair in uniq:
            owner.setdefault(pair, algo)
        found_all += rows

    unique = sorted(owner)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    
    with open(out / "acvp_pairs.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["key_hex", "iv_hex", "algo"])
        w.writerows((k, v, owner[(k, v)]) for k, v in unique)
    
    stats = {
        "files_read": len(manifest),
        "rows_read": len(found_all),
        "unique_pairs": len(unique),
        "duplicates_removed": len(found_all) - len(unique),
        "distinct_keys": len({k for k, _ in unique}),
        "per_algorithm": per_algo,
        "nonce_hex_length_distribution": dict(Counter(len(v) for _, v in unique)),
        "key_hex_length_distribution": dict(Counter(len(k) for k, _ in unique)),
    }
    
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    (out / "data_stats.json").write_text(json.dumps(stats, indent=2))
    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    main()