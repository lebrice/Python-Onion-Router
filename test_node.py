#!/usr/bin/python3
import unittest
import time
from node import *


class NodeTestCase(unittest.TestCase):
    def setUp(self):
        self.dir_node = DirectoryNode()
        self.dir_node.start()

    def tearDown(self):
        self.dir_node.stop()
        time.sleep(0.5)

    def test_node_connects_to_dir_node_on_startup(self):
        new_node = OnionNode(port=12346)
        new_node.start()
        time.sleep(0.2)
        nodes_in_network = self.dir_node.network_info.nodes_in_network
        new_node.stop()

        self.assertEqual(len(nodes_in_network), 1)
        self.assertEqual(nodes_in_network[0].ip, new_node.ip)
        self.assertEqual(nodes_in_network[0].port, new_node.port)
