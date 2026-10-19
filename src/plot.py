import sys, csv, statistics as st
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rows = list(csv.DictReader(open("results/raw/results.csv")))
rate = sys.argv[1] if len(sys.argv) > 1 else max([r["reuse_rate"] for r in rows], key=float)
agg = defaultdict(lambda: defaultdict(list))

for r in rows:
    if r["reuse_rate"] == rate:
        label = r["detector"].split("_", 1)[0] + (" " + r["params"] if r["params"] else "")
        for m in ("precision", "recall", "false_alarm", "events_per_s"):
            agg[label][m].append(float(r[m]))
labels = list(agg)

fig, ax = plt.subplots(figsize=(10, 4))
w = 0.27
for i, m in enumerate(("precision", "recall", "false_alarm")):
    ax.bar([x + (i - 1) * w for x in range(len(labels))], [st.mean(agg[l][m]) for l in labels], w, yerr=[st.pstdev(agg[l][m]) for l in labels], label=m, capsize=2)
ax.set_xticks(range(len(labels))); ax.set_xticklabels(labels, rotation=35, ha="right")
ax.set_title(f"Precision / Recall / False alarm (reuse_rate={rate})")
ax.legend(); fig.tight_layout(); fig.savefig("results/fig_quality.png", dpi=150)

fig, ax = plt.subplots(figsize=(10, 4))
ax.bar(labels, [st.mean(agg[l]["events_per_s"]) for l in labels])
ax.set_yscale("log"); ax.set_ylabel("events/s (log)")
ax.set_xticks(range(len(labels))); ax.set_xticklabels(labels, rotation=35, ha="right")
ax.set_title("Tốc độ xử lý (processing rate)")
fig.tight_layout(); fig.savefig("results/fig_speed.png", dpi=150)

print("Đã vẽ xong! Vui lòng xem ảnh results/fig_quality.png và results/fig_speed.png")