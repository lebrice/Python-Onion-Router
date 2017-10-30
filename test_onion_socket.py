#!/usr/bin/python3

import time
import unittest


from node import OnionNode, DirectoryNode
from onion_socket import OnionSocket
from errors import *
from workers import SocketReader
from network_creator import *


class OnionSocketTestCase(unittest.TestCase):
    def setUp(self):
        self.setup_network()
        self.start_all()

        self.website = SocketReader(12351)
        self.website.start()

    def tearDown(self):
        self.stop_all()
        self.website.stop()

    def setup_network(self):
        self.directory_node, self.onion_nodes = generate_nodes(
            onion_node_count=3,
            starting_port=12345
        )

    def start_all(self):
        self.directory_node.start()
        for node in self.onion_nodes:
            node.start()

    def stop_all(self):
        for node in self.onion_nodes:
            node.stop()
        self.directory_node.stop()

    @unittest.skip
    def test_socket_send_without_connect_raises_error(self):
        socket = OnionSocket.socket()
        with self.assertRaises(OnionSocketError):
            socket.send("something")

    def test_message_creation(self):
        socket = OnionSocket.socket()
        socket.connect(("127.0.0.1", 12351))

    def get_dummy_neighbours(self):
        neighbours = [
            ("mom", "127.0.0.1", "12345"),
            ("bob", "127.0.0.1", "12346"),
            ("alice", "127.0.0.1", "12347"),
            ("john", "127.0.0.1", "12348")
        ]
        return neighbours
