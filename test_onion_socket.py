#!/usr/bin/python3

import unittest

from node import OnionNode
from onion_socket import OnionSocket
from errors import OnionSocketError


class OnionSocketTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def test_socket_send_without_connect_raises_error(self):
        socket = OnionSocket.socket()
        with self.assertRaises(OnionSocketError):
            socket.send("something")
