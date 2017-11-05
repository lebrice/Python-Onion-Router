#!/usr/bin/python3

import unittest
from threading import Thread
import socket
import time
import json

from relaying import IntermediateRelay, SocketReader

HOST = socket.gethostname()
PORT = 12350


class IntermediateRelayTestCase(unittest.TestCase):
    """
    A --> (B  RELAY  C) --> D
    """
    def setUp(self):
        """ Set up the sockets as illustrated above. """
        self.socket_a = socket.socket()

        some_socket = socket.socket()
        some_socket.bind((HOST, PORT))
        some_socket.listen()

        def fun_1():
            time.sleep(0.2)
            self.socket_a.connect((HOST, PORT))

        some_thread = Thread(target=fun_1)
        some_thread.start()

        self.socket_b, _ = some_socket.accept()
        some_thread.join()
        some_socket.close()

        self.socket_c = socket.socket()

        some_socket = socket.socket()
        some_socket.bind((HOST, PORT+1))
        some_socket.listen()

        def fun_2():
            time.sleep(0.2)
            self.socket_c.connect((HOST, PORT+1))

        some_thread = Thread(target=fun_2)
        some_thread.start()
        self.socket_d, _ = some_socket.accept()
        some_thread.join()
        some_socket.close()

    def tearDown(self):
        global PORT
        PORT += 2
        self.socket_a.close()
        self.socket_b.close()
        self.socket_c.close()
        self.socket_d.close()

    def test_read_from_left_goes_to_right(self):
        test_message = """{"value": 10}"""
        sent_obj = json.loads(test_message)

        relay = IntermediateRelay(
            self.socket_b,
            self.socket_c
        )
        relay.start()

        self.socket_a.sendall(test_message.encode())

        received_bytes = self.socket_d.recv(1024)
        received_string = str(received_bytes, encoding="UTF-8")
        received_obj = json.loads(received_bytes)
        self.assertEqual(sent_obj, received_obj)
