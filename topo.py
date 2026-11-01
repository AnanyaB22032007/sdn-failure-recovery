#!/usr/bin/env python3
import sys, time, threading
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel

SCENS = ('baseline', 'static', 'single', 'flap', 'double', 'loss')
SCEN = next((a for a in sys.argv[1:] if a in SCENS), 'single')
AUTO = 'auto' in sys.argv or any(a in SCENS for a in sys.argv[1:])

# (seconds after start, action, switchA, switchB)
EVENTS = {
    'baseline': [],
    'static':   [(5, 'down', 's1', 's2'), (13, 'up', 's1', 's2')],
    'single':   [(5, 'down', 's1', 's2'), (13, 'up', 's1', 's2')],
    'flap':     [(4, 'down', 's1', 's2'), (6, 'up', 's1', 's2'),
                 (8, 'down', 's1', 's2'), (10, 'up', 's1', 's2'),
                 (12, 'down', 's1', 's2'), (14, 'up', 's1', 's2')],
    'double':   [(4, 'down', 's1', 's2'), (7, 'down', 's1', 's3'),
                 (9, 'up', 's1', 's3'), (12, 'up', 's1', 's2')],
    'loss':     [(5, 'down', 's1', 's2'), (13, 'up', 's1', 's2')],
}

def run():
    net = Mininet(controller=None, link=TCLink,
                  switch=lambda n, **kw: OVSSwitch(n, protocols='OpenFlow13', **kw))
    net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)
    h1 = net.addHost('h1', ip='10.0.0.1/24', mac='00:00:00:00:00:01')
    h2 = net.addHost('h2', ip='10.0.0.2/24', mac='00:00:00:00:00:02')
    s1, s2, s3, s4 = [net.addSwitch(f's{i}') for i in range(1, 5)]
    opt = dict(delay='5ms')
    net.addLink(h1, s1, port2=1, **opt)
    net.addLink(s1, s2, port1=2, port2=1, **opt)
    net.addLink(s1, s3, port1=3, port2=1, **opt)
    net.addLink(s2, s4, port1=2, port2=1, **opt)
    net.addLink(s3, s4, port1=2, port2=2, **opt)
    net.addLink(h2, s4, port2=3, **opt)
    net.start()
    time.sleep(3)
    print(net.pingAll())

    if SCEN == 'loss':
        for l in net.links:
            l.intf1.config(delay='5ms', loss=3)
            l.intf2.config(delay='5ms', loss=3)
        print('*** 3% packet loss added on all links')

    if AUTO:
        print('*** SCENARIO:', SCEN)
        h2.cmd('python3 server.py &')
        def events():
            t0 = time.time()
            for t, act, a, b in EVENTS[SCEN]:
                time.sleep(max(0, t0 + t - time.time()))
                print(f'*** t={t}s  {a}-{b} {act.upper()}')
                net.configLinkStatus(a, b, act)
        threading.Thread(target=events, daemon=True).start()
        print(h1.cmd(f'python3 client.py 10.0.0.2 1000 {SCEN}'))
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()
