#!/usr/bin/env python3
import sys, time, threading
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel

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

    if 'auto' in sys.argv:
        h2.cmd('python3 server.py &')
        def fail():
            time.sleep(5);  print('*** FAILING s1-s2');  net.configLinkStatus('s1', 's2', 'down')
            time.sleep(8);  print('*** RESTORING s1-s2'); net.configLinkStatus('s1', 's2', 'up')
        threading.Thread(target=fail, daemon=True).start()
        print(h1.cmd('python3 client.py 10.0.0.2 1000'))
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()
