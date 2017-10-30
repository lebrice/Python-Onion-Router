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
        self.private_key = 1443
        self.directory_node = DirectoryNode()
        self.directory_node.network_onion_nodes = [
            ("127.0.0.1", 12347),
            ("127.0.0.1", 12348),
            ("127.0.0.1", 12349)
        ]
        self.directory_node.start()

    def tearDown(self):
        self.directory_node.stop()

    @unittest.skip
    def test_socket_send_without_connect_raises_error(self):
        socket = OnionSocket.socket()
        with self.assertRaises(OnionSocketError):
            socket.send("something")

    def test_message_creation(self):
        node = self.get_dummy_onion_node()
        socket = OnionSocket(onion_node=node)
        socket.connect(("127.0.0.1", 12350))

        ready_for_sending = socket._create_message("HTTP GET: www.youtube.com")
        print(ready_for_sending)

    def get_dummy_onion_node(self):
        """ Returns a dummy OnionNode for testing purposes. """
        node = OnionNode("my_node", 12346, self.private_key)
        return node
