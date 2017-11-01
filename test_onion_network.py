#!/usr/bin/python3
""" Integration testing """
import unittest


class IntegrationTestCase(unittest.TestCase):
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
