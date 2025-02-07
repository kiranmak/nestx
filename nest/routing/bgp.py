# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2019-2020 NITK Surathkal

"""Class to handles OSPF related functionalities"""

import random
from functools import partial
from nest.engine.dynamic_routing import run_bgpd
from nest.routing.route_daemons import RoutingDaemonBase
from nest import config

# pylint: disable=line-too-long


class Bgp(RoutingDaemonBase):
    """
    Handles OSPF related functionalities.
    """
    def __init__(self, router_ns_id, ipv6_routing, interfaces, conf_dir, **kwargs):
        super().__init__(
                router_ns_id, ipv6_routing, interfaces, "bgpd", conf_dir, **kwargs
            )
    # pylint: disable=too-many-branches
    def create_basic_config(self):
        """
        Creates a file with basic configuration for BGP.
        Use base `add_to_config` directly for more complex configurations
        """
        if self.log_file is not None:
            self.add_to_config(f"log file {self.log_file}")

        self.create_config()

    def run(self):
        pass
        """
        Runs the bgpd command
        super().run(
            engine_func=partial(
                run_bgpd,
                self.router_ns_id,
                self.conf_file,
                self.pid_file,
                self.ipv6_routing,
                log_file=self.log_file,
                socket_file=self.socket_file,
            )
        )
        """ 
