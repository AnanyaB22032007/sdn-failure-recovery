# Adaptive Communication Network with Failure Recovery

SDN + UDP socket programming mini project (Project 30), built with Mininet, Open vSwitch and the os-ken controller (the maintained fork of Ryu).

## 1. Problem statement

A resilient UDP communication framework in which the SDN controller detects link failures and reroutes application traffic through an alternate path, while the UDP application recovers lost packets with retransmissions.

## 2. Architecture

Diamond topology, OpenFlow 1.3, controller on port 6653:

    h1 - s1 ---- s2 (primary path) ---- s4 - h2
           \                           /
            ---- s3 (backup path) -----

Files: server.py (UDP echo server), client.py (UDP client with sequence numbers, 100 ms retransmit timeout, max 3 retries), topo.py (Mininet topology and automatic failure test), controller.py (os-ken SDN controller).

## 3. How it works

1. The controller installs flow rules for the primary path (s1, s2, s4).
2. h1 sends numbered UDP packets to the h2 server, which echoes them back.
3. A link on the primary path goes down, and the switch sends an OpenFlow Port Status message to the controller.
4. The controller installs rules for the backup path (via s3).
5. Packets lost during the switch are retransmitted by the client.
6. When the link returns, the controller switches back to the primary path.
7. The client reports loss, latency and the longest outage (recovery time).

## 4. Setup (Ubuntu)

    sudo apt install -y mininet openvswitch-switch python3-pip python3-venv git
    sudo systemctl enable --now openvswitch-switch
    python3 -m venv ~/oskenenv
    source ~/oskenenv/bin/activate
    pip install os-ken

## 5. How to run

Terminal 1 (controller, keep it running):

    cd ~/sdn_project
    source ~/oskenenv/bin/activate
    osken-manager --ofp-tcp-listen-port 6653 controller.py

Terminal 2 (network and failure test, no venv):

    cd ~/sdn_project
    sudo mn -c
    sudo python3 topo.py auto

Expected: 0% dropped, then FAILING s1-s2, RESTORING s1-s2 and a client summary. The controller logs LINK DOWN, REROUTE primary -> backup, LINK UP and REROUTE backup -> primary.

## 6. Test cases

| # | Test | Expected result |
|---|---|---|
| T1 | No failure | 0% loss, primary path |
| T2 | Fail s1-s2 during traffic | Reroute to backup, short outage |
| T3 | Restore s1-s2 | Switch back to primary |
| T4 | Fail both paths | No path, loss, recovery when a link returns |
| T5 | Link flapping | Controller stays stable |
| T6 | MAX_RETRY 0 vs 3 | Retries reduce loss |
| T7 | Packet interval 10/20/50 ms | Recovery time vs rate |

## 7. Results (D1 initial test, T2)

| Metric | Value |
|---|---|
| Packets sent / delivered | 1000 / 1000 |
| Packet loss | 0.0% |
| Packets needing retransmission | 7 |
| Average latency | 53.7 ms |
| Maximum latency | 166.2 ms |
| Longest outage (recovery time) | 120 ms |
| Controller reaction time | about 1 ms |

D2 results (T1 to T7, 5 runs each, graphs): to be added.

## 8. Team

| Member | Responsibility |
|---|---|
| Member 1 | UDP application, app-level recovery, T6 |
| Member 2 | Mininet topology and SDN controller, T4 and T5 |
| Member 3 | Integration, testing, evaluation, documentation, demo |

## 9. Notes

os-ken is used instead of Ryu because Ryu does not install on the newer Python version on the test machine. os-ken is the maintained fork with the same API.
