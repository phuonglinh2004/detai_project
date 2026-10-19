import random

def confusion(y, p):
    tp = sum(1 for a, b in zip(y, p) if a and b)
    fp = sum(1 for a, b in zip(y, p) if not a and b)
    fn = sum(1 for a, b in zip(y, p) if a and not b)
    tn = len(y) - tp - fp - fn
    return tp, fp, fn, tn

def scores(y, p):
    tp, fp, fn, tn = confusion(y, p)
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    far = fp / (fp + tn) if fp + tn else 0.0
    return dict(tp=tp, fp=fp, fn=fn, tn=tn, precision=prec, recall=rec, f1=f1, false_alarm=far)

def boot_mean_ci(values, n_boot=300, seed=0):
    if not values: return (0.0, 0.0)
    rng = random.Random(seed)
    m = len(values)
    means = sorted(sum(rng.choices(values, k=m)) / m for _ in range(n_boot))
    return (means[int(0.025 * n_boot)], means[int(0.975 * n_boot) - 1])

def ci_recall_precision(y, p, n_boot=300, seed=0):
    rec_vals = [int(b) for a, b in zip(y, p) if a]
    prec_vals = [int(a) for a, b in zip(y, p) if b]
    return boot_mean_ci(rec_vals, n_boot, seed), boot_mean_ci(prec_vals, n_boot, seed)