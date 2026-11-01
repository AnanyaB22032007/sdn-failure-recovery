import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.figure(figsize=(10, 5))
for t, c in [('baseline', '#2F6BFF'), ('static', '#E8505B'), ('single', '#00897B'), ('flap', '#6C3FE0')]:
    rr = list(csv.DictReader(open(f'results_{t}.csv')))
    plt.plot([int(r['seq']) for r in rr], [float(r['rtt_ms']) for r in rr], label=t, color=c, linewidth=1)
plt.xlabel('Packet sequence number'); plt.ylabel('RTT (ms)')
plt.title('Latency per packet: static vs SDN reroute'); plt.legend(); plt.grid(alpha=0.3)
plt.savefig('latency_static_vs_sdn.png', dpi=150)
print('saved latency_static_vs_sdn.png')
