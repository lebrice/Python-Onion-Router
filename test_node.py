#!/usr/bin/python3
import unittest
import time
from node import *


class NodeTestCase(unittest.TestCase):
    def test_node_connects_to_dir_node_on_startup(self):
        dir_node = DirectoryNode()
        dir_node.start()

        new_node = OnionNode(port=12345)
        new_node.start()

        time.sleep(0.2)
        nodes_in_network = dir_node.network_info.nodes_in_network
        self.assertEquals(len(nodes_in_network), 1)
        self.assertEquals(nodes_in_network[0].ip, new_node.ip)
        self.assertEquals(nodes_in_network[0].port, new_node.port)
        self.assertEquals(nodes_in_network[0].public_exp, new_node.public_exp)
        self.assertEquals(nodes_in_network[0].modulus, new_node.modulus)
