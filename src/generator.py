import csv, hashlib, random, sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    event_id INTEGER PRIMARY KEY, ts REAL, key_id TEXT, nonce TEXT, alg TEXT, op TEXT, session_id INTEGER, scenario TEXT, label INTEGER
);
"""

def key_id(key_hex): return hashlib.sha256(key_hex.encode()).hexdigest()[:12]
def norm(nonce): return nonce.strip().lower()

def load_pairs(path="data/processed/acvp_pairs.csv"):
    with open(path, newline="") as f:
        return [(r["key_hex"], r["iv_hex"]) for r in csv.DictReader(f)]

def expand_pairs(pairs, per_key, seed):
    rng = random.Random(seed)
    out, seen = list(pairs), set(pairs)
    for k, v in pairs:
        for _ in range(per_key - 1):
            nv = f"{rng.getrandbits(len(v) * 4):0{len(v)}x}"
            if (k, nv) not in seen:
                seen.add((k, nv))
                out.append((k, nv))
    return out

def group_split(pairs, seed, test_frac=0.5):
    kids = sorted({key_id(k) for k, _ in pairs})
    random.Random(seed).shuffle(kids)
    cut = int(len(kids) * (1 - test_frac))
    train_keys = set(kids[:cut])
    train = [p for p in pairs if key_id(p[0]) in train_keys]
    test = [p for p in pairs if key_id(p[0]) not in train_keys]
    return train, test

def make_log(pairs, reuse_rate, seed):
    rng = random.Random(seed)
    base = list(pairs); rng.shuffle(base)
    n = len(base)
    events = [dict(ts=float(i), key=k, nonce=v, scenario="clean") for i, (k, v) in enumerate(base)]
    SCENARIOS = ["reuse_near", "reuse_far", "case_variant", "cross_key"]
    for _ in range(int(n * reuse_rate)):
        scen = rng.choice(SCENARIOS)
        i = rng.randrange(n)
        k, v = base[i]
        ts = i + rng.uniform(1, 20)
        if scen == "reuse_far": ts = i + n / 2 + rng.uniform(0, n / 4)
        elif scen == "case_variant": v = v.upper()
        elif scen == "cross_key":
            for _ in range(20):
                k2 = base[rng.randrange(n)][0]
                if key_id(k2) != key_id(k):
                    k = k2; break
        events.append(dict(ts=ts, key=k, nonce=v, scenario=scen))
    events.sort(key=lambda e: e["ts"])
    seen, out = set(), []
    for eid, e in enumerate(events):
        kid = key_id(e["key"])
        sig = (kid, norm(e["nonce"]))
        out.append(dict(event_id=eid, ts=round(e["ts"], 3), key_id=kid, nonce=e["nonce"],
                        alg=f"AES-{len(e['key']) * 4}-AEAD", op="encrypt", session_id=eid // 100,
                        scenario=e["scenario"], label=int(sig in seen)))
        seen.add(sig)
    return out

def save_log(events, path):
    db = sqlite3.connect(path)
    db.executescript(SCHEMA)
    db.executemany("INSERT OR REPLACE INTO events VALUES (:event_id,:ts,:key_id,:nonce,:alg,:op,:session_id,:scenario,:label)", events)
    db.commit(); db.close()