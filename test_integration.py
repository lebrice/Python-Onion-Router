#!/usr/bin/python3
""" Integration testing """
import unittest

import node

from node import DirectoryNode, OnionNode


class IntegrationTestCase(unittest.TestCase):
    """
    Integration Tests for the Onion Network.
    """
    def setUp(self):
        self._setup_network()
        self._start_all()

        self.website = SocketReader(12351)
        self.website.start()

    def _setup_network(self):
        self.directory_node, self.onion_nodes = generate_nodes(
            onion_node_count=3,
            starting_port=12345
        )

    def _start_all(self):
        self.directory_node.start()
        for node in self.onion_nodes:
            node.start()

    def tearDown(self):
        self._stop_all()
        self.website.stop()

    def _stop_all(self):
        for node in self.onion_nodes:
            node.stop()
        self.directory_node.stop()


def generate_nodes(onion_node_count=10, starting_port=12345):
    """Generates a directory node and some onion nodes.

    Returns: (DirectoryNode, List[OnionNode])
    """
    directory_node = DirectoryNode(receiving_port=starting_port)
    onion_nodes = []
    for i in range(onion_node_count):
        node_name = "ONION_NODE_{}".format(i)
        node_receiving_port = starting_port + i
        node_private_key = 127 + i  # Some lousy private key.
        node = OnionNode(node_name, node_receiving_port, node_private_key)
        onion_nodes.append(node)

    return directory_node, onion_nodes