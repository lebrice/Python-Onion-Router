#!/usr/bin/python3

import socket
import time
import unittest

from threading import Thread

from node import OnionNode, DirectoryNode
import onion_socket
from onion_socket import OnionSocket
from errors import *
from network_creator import *

HOST = socket.gethostname()
PRIVATE_KEY = 1443


class OnionSocketTestCase(unittest.TestCase):

    def setUp(self):
        """ Runs before every test """
        self.directory_node = DirectoryNode()
        # TODO: actually create a set of onion nodes.
        self.directory_node.network_onion_nodes = [
            ("127.0.0.1", 12347),
            ("127.0.0.1", 12348),
            ("127.0.0.1", 12349)
        ]
        self.directory_node.start()

    def tearDown(self):
        """ Runs after every test """
        self.directory_node.stop()

    @unittest.skip
    def test_socket_send_without_connect_raises_error(self):
        """ Test that using socket.send() before calling socket.connect()
        raises an error."""
        with self.assertRaises(OnionSocketError):
            with onion_socket.socket() as _socket:
                _socket.send("something without having called socket.connect()")

    @unittest.skip
    def test_connect_works(self):
        """ TODO: fix this test. It currently doesnt work. """
        def fun():
            some_socket = socket.socket()
            some_socket.bind((HOST, 12370))
            some_socket.listen()
            dummy_listener, _ = some_socket.accept()
            some_socket.close()
            time.sleep(0.2)
            dummy_listener.close()

        dummy_thread = Thread(target=fun)
        test_socket = OnionSocket.socket()

        dummy_thread.start()
        try:
            test_socket.connect(("127.0.0.1", 12370))
        except OnionError as e:
            self.fail(f"There was an error: {e}")
        finally:
            test_socket.close()

    def get_dummy_onion_node(self):
        """ Returns a dummy OnionNode for testing purposes. """
        return OnionNode("my_node", 12346, PRIVATE_KEY)
