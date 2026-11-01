import time
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib import hub

# {dpid: {in_port: out_port}}  matches topo.py port numbers
PATHS = {
    'primary': {1: {1: 2, 2: 1}, 2: {1: 2, 2: 1}, 4: {1: 3, 3: 1}},
    'backup':  {1: {1: 3, 3: 1}, 3: {1: 2, 2: 1}, 4: {2: 3, 3: 2}},
}


class AdaptiveRecovery(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dps = {}
        self.down = set()
        self.active = 'primary'
        hub.spawn(self.stats_loop)

    def path_ok(self, name):
        for dpid, m in PATHS[name].items():
            for in_p, out_p in m.items():
                if (dpid, in_p) in self.down or (dpid, out_p) in self.down:
                    return False
        return True

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def on_features(self, ev):
        dp = ev.msg.datapath
        self.dps[dp.id] = dp
        self.logger.info("SWITCH CONNECTED: s%s (active path: %s)", dp.id, self.active)
        self.install(dp, self.active)

    @set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
    def on_port_status(self, ev):
        t0 = time.time()
        msg = ev.msg
        dp = msg.datapath
        port = msg.desc.port_no
        if port >= 0xffffff00:
            return
        ofp = dp.ofproto
        is_down = bool(msg.desc.state & ofp.OFPPS_LINK_DOWN) or \
                  bool(msg.desc.config & ofp.OFPPC_PORT_DOWN)
        if is_down:
            self.down.add((dp.id, port))
            self.logger.info("LINK DOWN: s%s port %s", dp.id, port)
        else:
            self.down.discard((dp.id, port))
            self.logger.info("LINK UP: s%s port %s", dp.id, port)
        new = next((n for n in ('primary', 'backup') if self.path_ok(n)), None)
        if new != self.active:
            old, self.active = self.active, new
            for d in self.dps.values():
                self.install(d, new)
            self.logger.info("REROUTE %s -> %s (controller reaction %.2f ms)",
                             old, new, (time.time() - t0) * 1000)

    def install(self, dp, name):
        ofp, p = dp.ofproto, dp.ofproto_parser
        dp.send_msg(p.OFPFlowMod(datapath=dp, command=ofp.OFPFC_DELETE,
                                 out_port=ofp.OFPP_ANY, out_group=ofp.OFPG_ANY,
                                 match=p.OFPMatch()))
        if name is None:
            return
        for in_p, out_p in PATHS[name].get(dp.id, {}).items():
            inst = [p.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS,
                                            [p.OFPActionOutput(out_p)])]
            dp.send_msg(p.OFPFlowMod(datapath=dp, priority=10,
                                     match=p.OFPMatch(in_port=in_p),
                                     instructions=inst))

    def stats_loop(self):
        while True:
            hub.sleep(2)
            for dp in list(self.dps.values()):
                dp.send_msg(dp.ofproto_parser.OFPFlowStatsRequest(dp))

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def on_stats(self, ev):
        for s in ev.msg.body:
            self.logger.info("STATS s%s in_port=%s pkts=%d bytes=%d",
                             ev.msg.datapath.id, s.match['in_port'],
                             s.packet_count, s.byte_count)
