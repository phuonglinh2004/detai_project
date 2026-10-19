import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from detectors import NonceOnly, ExactPair, NormPair, SqliteUnique, BloomPair, WindowPair
from generator import group_split, make_log, key_id, expand_pairs

N = "aabbccddeeff00112233aabb"

def test_same_key_same_nonce_detected():
    for det in (NonceOnly(), ExactPair(), NormPair(), SqliteUnique(), BloomPair(100), WindowPair(10)):
        assert det.process("k1", N) is False
        assert det.process("k1", N) is True, det.name

def test_no_reuse_no_alert():
    det = ExactPair()
    assert not any(det.process("k1", f"{i:024x}") for i in range(500))

def test_same_nonce_different_key_is_legit():
    d = ExactPair(); d.process("k1", N)
    assert d.process("k2", N) is False
    b0 = NonceOnly(); b0.process("k1", N)
    assert b0.process("k2", N) is True

def test_case_variant_needs_normalization():
    d1, d2 = ExactPair(), NormPair()
    d1.process("k1", N); d2.process("k1", N)
    assert d1.process("k1", N.upper()) is False
    assert d2.process("k1", N.upper()) is True

def test_window_forgets_old_events():
    w = WindowPair(3)
    w.process("k1", N)
    for i in range(10): w.process("k1", f"{i:024x}")
    assert w.process("k1", N) is False

def test_bloom_never_misses_duplicates():
    b = BloomPair(1000, bits_per_item=4)
    items = [f"{i:024x}" for i in range(1000)]
    for x in items: b.process("k", x)
    assert all(b.process("k", x) for x in items)

def test_group_split_no_key_leak():
    pairs = [(f"{i % 20:064x}", f"{i:024x}") for i in range(400)]
    tr, te = group_split(pairs, seed=1)
    assert {key_id(k) for k, _ in tr}.isdisjoint({key_id(k) for k, _ in te})

def test_generator_deterministic():
    pairs = [(f"{i % 20:064x}", f"{i:024x}") for i in range(400)]
    assert make_log(pairs, 0.05, 7) == make_log(pairs, 0.05, 7)

def test_expand_pairs_deterministic_and_unique():
    pairs = [(f"{i:032x}", f"{i:024x}") for i in range(50)]
    a, b = expand_pairs(pairs, 4, seed=3), expand_pairs(pairs, 4, seed=3)
    assert a == b and len(a) == 200 and len(set(a)) == 200