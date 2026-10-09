import socket, time, sys, csv

server = sys.argv[1]
N = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
PORT, INTERVAL, RTO, MAX_RETRY = 5005, 0.02, 0.1, 3

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(0.005)
pending, rtt, recv_t, retries, lost = {}, {}, [], {}, set()
start, nxt = time.time(), 0

while nxt < N or pending:
    now = time.time()
    if nxt < N and now >= start + nxt * INTERVAL:
        sock.sendto(f"{nxt},{now}".encode(), (server, PORT))
        pending[nxt] = {'first': now, 'last': now, 'n': 0}
        nxt += 1
    try:
        data, _ = sock.recvfrom(1024)
        seq = int(data.split(b',')[0])
        if seq in pending:
            t = time.time()
            rtt[seq] = (t - pending[seq]['first']) * 1000
            retries[seq] = pending[seq]['n']
            recv_t.append(t)
            del pending[seq]
    except socket.timeout:
        pass
    for seq, p in list(pending.items()):
        if now - p['last'] > RTO:
            if p['n'] >= MAX_RETRY:
                lost.add(seq); del pending[seq]
            else:
                sock.sendto(f"{seq},{now}".encode(), (server, PORT))
                p['n'] += 1; p['last'] = now

gaps = [b - a for a, b in zip(recv_t, recv_t[1:])]
vals = list(rtt.values())
print(f"Sent={N} Delivered={len(rtt)} Lost={len(lost)} ({100*len(lost)/N:.1f}% loss)")
print(f"Packets needing retransmit={sum(1 for r in retries.values() if r>0)}")
print(f"Latency avg={sum(vals)/len(vals):.1f} ms  max={max(vals):.1f} ms")
print(f"Longest outage (recovery time) = {max(gaps)*1000:.0f} ms")
with open('results.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['seq', 'rtt_ms', 'retries'])
    for s in sorted(rtt): w.writerow([s, round(rtt[s], 2), retries[s]])
