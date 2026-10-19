import hashlib, sqlite3
from collections import OrderedDict

def norm(nonce): return nonce.strip().lower()

class NonceOnly:
    def __init__(self): self.name, self.seen = "B0_nonce_only", set()
    def process(self, key_id, nonce):
        hit = nonce in self.seen
        self.seen.add(nonce)
        return hit

class ExactPair:
    def __init__(self): self.name, self.seen = "B1_exact_pair", set()
    def process(self, key_id, nonce):
        sig = (key_id, nonce)
        hit = sig in self.seen
        self.seen.add(sig)
        return hit

class NormPair(ExactPair):
    def __init__(self):
        super().__init__()
        self.name = "V1_norm_pair"
    def process(self, key_id, nonce):
        return super().process(key_id, norm(nonce))

class SqliteUnique:
    def __init__(self, path=":memory:"):
        self.name = "V2_sqlite_unique"
        self.db = sqlite3.connect(path)
        self.db.execute("CREATE TABLE IF NOT EXISTS seen(key_id TEXT, nonce TEXT, PRIMARY KEY(key_id, nonce)) WITHOUT ROWID")
    def process(self, key_id, nonce):
        try:
            self.db.execute("INSERT INTO seen VALUES (?,?)", (key_id, norm(nonce)))
            return False
        except sqlite3.IntegrityError:
            return True

class BloomPair:
    def __init__(self, capacity, bits_per_item=8, k=3):
        self.name = f"V3_bloom_{bits_per_item}bpi"
        self.m, self.k = max(64, capacity * bits_per_item), k
        self.bits = bytearray((self.m + 7) // 8)
    def _idx(self, s):
        d = hashlib.blake2b(s.encode(), digest_size=16).digest()
        h1, h2 = int.from_bytes(d[:8], "big"), int.from_bytes(d[8:], "big") | 1
        return [(h1 + i * h2) % self.m for i in range(self.k)]
    def process(self, key_id, nonce):
        idx = self._idx(key_id + ":" + norm(nonce))
        hit = all((self.bits[i >> 3] >> (i & 7)) & 1 for i in idx)
        for i in idx: self.bits[i >> 3] |= 1 << (i & 7)
        return hit

class WindowPair:
    def __init__(self, window):
        self.name, self.w, self.n = f"V4_window_{window}", window, 0
        self.od = OrderedDict()
    def process(self, key_id, nonce):
        self.n += 1
        while self.od and next(iter(self.od.values())) <= self.n - self.w:
            self.od.popitem(last=False)
        sig = (key_id, norm(nonce))
        hit = sig in self.od
        self.od[sig] = self.n
        self.od.move_to_end(sig)
        return hit