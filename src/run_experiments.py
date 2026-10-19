import csv, json, logging, os, platform, shutil, statistics as st, sys, time, tracemalloc
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from alerts import write_alerts
from detectors import NonceOnly, ExactPair, NormPair, SqliteUnique, BloomPair, WindowPair
from generator import load_pairs, expand_pairs, group_split, make_log, save_log
from metrics import scores, ci_recall_precision
OUT = Path("results")

def predict(factory, events):
    det = factory()
    return [det.process(e["key_id"], e["nonce"]) for e in events]

def timed(factory, events, reps):
    best = []
    for _ in range(reps):
        t0 = time.perf_counter()
        predict(factory, events)
        best.append(time.perf_counter() - t0)
    return len(events) / st.median(best)

def peak_kib(factory, events):
    tracemalloc.start()
    predict(factory, events)
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    return peak / 1024

def main(cfg_path="configs/exp.json"):
    cfg = json.load(open(cfg_path))
    (OUT / "raw").mkdir(parents=True, exist_ok=True)
    (OUT / "logs").mkdir(exist_ok=True)
    logging.basicConfig(filename=OUT / "run.log", level=logging.INFO, format="%(asctime)s %(message)s")
    shutil.copy(cfg_path, OUT / "config_used.json")
    json.dump({"python": platform.python_version(), "platform": platform.platform(), "cpu_count": os.cpu_count()}, open(OUT / "env.json", "w"), indent=2)
    pairs = load_pairs()
    rows, errs = [], []
    for seed in cfg["seeds"]:
        pairs_s = expand_pairs(pairs, cfg.get("expand_per_key", 1), seed)
        train, test = group_split(pairs_s, seed, cfg["test_frac"])
        for rate in cfg["reuse_rates"]:
            log_tr = make_log(train, rate, seed)
            log_te = make_log(test, rate, seed + 1)
            save_log(log_te, OUT / "logs" / f"log_seed{seed}_rate{rate}.sqlite")
            y_te = [e["label"] for e in log_te]
            n_te = len(log_te)
            chosen_w = cfg["window_sizes"][-1]
            for w in cfg["window_sizes"]:
                if scores([e["label"] for e in log_tr], predict(lambda: WindowPair(w), log_tr))["recall"] >= cfg["target_recall_for_window"]:
                    chosen_w = w; break
            dets = [("", NonceOnly), ("", ExactPair), ("", NormPair), ("", SqliteUnique)]
            dets = [(n, f, 1) for n, f in dets]
            dets += [(f"bpi={b}", (lambda b=b: BloomPair(n_te, b)), 1) for b in cfg["bloom_bits_per_item"]]
            dets += [(f"W={w}", (lambda w=w: WindowPair(w)), int(w == chosen_w)) for w in cfg["window_sizes"]]
            for params, factory, selected in dets:
                preds = predict(factory, log_te)
                name = factory().name
                sc = scores(y_te, preds)
                (rl, rh), (pl, ph) = ci_recall_precision(y_te, preds, cfg["bootstrap_resamples"], seed)
                row = dict(seed=seed, reuse_rate=rate, detector=name, params=params, selected_on_train=selected, n_events=n_te, n_pos=sum(y_te), **sc,
                           recall_ci_lo=rl, recall_ci_hi=rh, precision_ci_lo=pl, precision_ci_hi=ph,
                           events_per_s=timed(factory, log_te, cfg["timing_reps"]), peak_mem_kib=peak_kib(factory, log_te))
                rows.append(row)
                for kind, cond in (("FN", lambda y, p: y and not p), ("FP", lambda y, p: p and not y)):
                    cnt = Counter(e["scenario"] for e, p in zip(log_te, preds) if cond(e["label"], p))
                    for scen, c in cnt.items():
                        errs.append(dict(seed=seed, reuse_rate=rate, detector=name, params=params, kind=kind, scenario=scen, count=c))
                if name == "V1_norm_pair" and seed == cfg["seeds"][0] and rate == cfg["reuse_rates"][-1]:
                    write_alerts(OUT / "alerts_sample.jsonl", log_te, preds, name)
    keys = list(rows[0].keys())
    with open(OUT / "raw" / "results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, keys); w.writeheader(); w.writerows(rows)
    with open(OUT / "raw" / "errors_by_scenario.csv", "w", newline="") as f:
        w = csv.DictWriter(f, ["seed", "reuse_rate", "detector", "params", "kind", "scenario", "count"]); w.writeheader(); w.writerows(errs)
    groups = {}
    for r in rows: groups.setdefault((r["reuse_rate"], r["detector"], r["params"]), []).append(r)
    cols = ["precision", "recall", "f1", "false_alarm", "events_per_s", "peak_mem_kib"]
    with open(OUT / "summary.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["reuse_rate", "detector", "params"] + [f"{c}_{s}" for c in cols for s in ("mean", "std")])
        for (rate, name, params), rs in sorted(groups.items()):
            line = [rate, name, params]
            for c in cols:
                vals = [r[c] for r in rs]
                line += [round(st.mean(vals), 5), round(st.pstdev(vals), 5)]
            w.writerow(line)
    print("Xong. Đã lưu kết quả tại thư mục results/summary.csv")

if __name__ == "__main__":
    main(*sys.argv[1:])