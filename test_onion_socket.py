#!/usr/bin/python3

import time
import unittest


from node import OnionNode, DirectoryNode
from onion_socket import OnionSocket
from errors import *
from workers import SocketReader


class OnionSocketTestCase(unittest.TestCase):
    def setUp(self):
        self.directory_node = DirectoryNode()
        self.directory_node.start()

        self.dummy_reader = SocketReader(12351)
        self.dummy_reader.start()

    def tearDown(self):
        self.directory_node.stop()
        self.dummy_reader.stop()

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
