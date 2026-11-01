import csv
from collections import defaultdict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ORDER = ['baseline', 'static', 'single', 'flap', 'double', 'loss']
rows = defaultdict(list)
for r in csv.DictReader(open('summary.csv')):
    rows[r['scenario']].append(r)

def stat(tag, col):
    v = [float(r[col]) for r in rows[tag]]
    return sum(v) / len(v), min(v), max(v)

lines = ['| Scenario | Runs | Loss % | Retransmitted (avg) | Avg latency ms | Max latency ms | Outage ms (avg, min-max) |',
         '|---|---|---|---|---|---|---|']
for t in ORDER:
    if t not in rows:
        continue
    l, rt, a, mx, o = (stat(t, c) for c in ['loss_pct', 'retransmitted', 'avg_ms', 'max_ms', 'outage_ms'])
    lines.append(f'| {t} | {len(rows[t])} | {l[0]:.1f} | {rt[0]:.0f} | {a[0]:.1f} | {mx[0]:.0f} | {o[0]:.0f} ({o[1]:.0f}-{o[2]:.0f}) |')
open('comparison.md', 'w').write('\n'.join(lines) + '\n')
print('\n'.join(lines))

fig, ax = plt.subplots(1, 2, figsize=(14, 5))
for t in ORDER:
    try:
        rr = list(csv.DictReader(open(f'results_{t}.csv')))
    except FileNotFoundError:
        continue
    ax[0].plot([int(r['seq']) for r in rr], [float(r['rtt_ms']) for r in rr], label=t, linewidth=0.9)
ax[0].set_xlabel('Packet sequence number'); ax[0].set_ylabel('RTT (ms)')
ax[0].set_title('Per-packet latency by scenario'); ax[0].legend(); ax[0].grid(alpha=0.3)
tags = [t for t in ORDER if t in rows]
ax[1].bar(tags, [stat(t, 'outage_ms')[0] for t in tags], color=['#2F6BFF', '#00897B', '#6C3FE0', '#E8505B', '#FFB400'][:len(tags)])
ax[1].set_ylabel('Longest outage (ms)'); ax[1].set_title('Recovery time by scenario (average)'); ax[1].grid(axis='y', alpha=0.3)
plt.tight_layout(); plt.savefig('latency_comparison.png', dpi=150)
print('saved latency_comparison.png and comparison.md')
