# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2019-2020 NITK Surathkal

"""Test APIs from routing sub-package"""
import unittest
from glob import glob
import time
import logging
from os.path import isfile
from nest import config
from nest.topology_map import TopologyMap
from nest.topology import Node, connect
from nest.routing.routing_helper import RoutingHelper
from nest.clean_up import delete_namespaces

import subprocess
from subprocess import Popen, PIPE

'''
    SubprocessManager: typically FRR daemaon management class handling output
    blocking scenarios (PIPE.stdout etc.)
'''
class SubprocessManager:
    def __init__(self, command):
        self.command = command
        self.process = None
        self.stdout = None
        self.stderr = None

    def __enter__(self):
        print("Start the subprocess when entering the context.")
        self.process = subprocess.Popen(
            self.command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure the process is terminated when exiting the context."""
        if self.process:
            self.process.terminate()
            self.process.wait()

    def communicate(self):
        """Communicate with the process to capture output."""
        if not self.process:
            raise RuntimeError("Process not started.")
        self.stdout, self.stderr = self.process.communicate()
        return self.stdout, self.stderr


'''
    NSRoutingDaemon:
     this is essentially a helper for shell utility, so that if we dont
     use nest.experiment or test. We can do the following independently
     - manage topology
     - manage FRR daemons (start/stop)
     - config FRRs etc.
'''
class NSRoutingDaemon:
    def __init__(self, namespace, test_name=""):
        self.ns_id = namespace

        self.basedir = os.path("/tmp/nest", test_name, namespace)
        os.makedirs(basedir, exist_ok=True)


        # default start zebra and setup integrated config
        self.conf_file = self._create_integrated_file()

    def _create_integrated_file(self):
        # create frr.conf
        pass


    def start(self, daemon):
        pid_file = os.path(self.basedir,
                           self.ns_id + "_" + daemon + ".pid")
        ns_id = self.ns_id
        cmd = f"ip netns exec {ns_id}" +
              f" {FRR_DAEMONPATH}daemon -F " +
              f" traditional -s -n -N {ns_id}"

        command = self.cmd.split()
        with SubprocessManager(command) as manager:
            print("Command:",  subprocess.list2cmdline(command))
            stdout, stderr = manager.communicate()
            print("Standard Output:", stdout)
            print("Standard Error:", stderr)

    def stop(self):
        # tbd

