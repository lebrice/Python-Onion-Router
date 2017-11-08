#!/usr/bin/python3

import unittest
from threading import Thread
import socket
import sys
import time
import json

from relaying import IntermediateRelay, SocketReader

HOST = socket.gethostname()
PORT = 12350


class IntermediateRelayTestCase(unittest.TestCase):
    """
           <RELAY>
    A --> (B  -  C) --> D
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

    def test_sent_from_a_goes_to_d(self):
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

    def test_sent_from_d_goes_to_a(self):
        test_message = """{"value": 10}"""
        sent_obj = json.loads(test_message)

        relay = IntermediateRelay(
            self.socket_b,
            self.socket_c
        )
        relay.start()

        self.socket_d.sendall(test_message.encode())

        received_bytes = self.socket_a.recv(1024)
        received_string = str(received_bytes, encoding="UTF-8")
        received_obj = json.loads(received_bytes)
        self.assertEqual(sent_obj, received_obj)

    def test_left_to_right_function_is_applied(self):
        test_message = """{"value": 10}"""
        sent_obj = json.loads(test_message)

        relay = IntermediateRelay(
            self.socket_b,
            self.socket_c,
            left_to_right=double_value
        )
        relay.start()

        self.socket_a.sendall(test_message.encode())

        received_bytes = self.socket_d.recv(1024)
        received_string = str(received_bytes, encoding="UTF-8")
        received_obj = json.loads(received_bytes)
        expected = sent_obj['value'] * 2
        actual = received_obj['value']
        self.assertEqual(expected, actual)

    def test_right_to_left_function_is_applied(self):
        test_message = """{"value": 10}"""
        sent_obj = json.loads(test_message)

        relay = IntermediateRelay(
            self.socket_b,
            self.socket_c,
            left_to_right=double_value,
            right_to_left=square_value
        )
        relay.start()

        self.socket_d.sendall(test_message.encode())

        received_bytes = self.socket_a.recv(1024)
        received_string = str(received_bytes, encoding="UTF-8")
        received_obj = json.loads(received_bytes)
        expected = sent_obj['value'] ** 2
        actual = received_obj['value']
        self.assertEqual(expected, actual)

    def test_closing_a_eventually_closes_d(self):
        test_message = """{"value": 10}"""

        relay = IntermediateRelay(
            self.socket_b,
            self.socket_c
        )
        relay.start()

        self.socket_a.close()
        time.sleep(0.2)
        self.assert_is_closed(self.socket_d)

    def test_closing_d_eventually_closes_a(self):
        test_message = """{"value": 10}"""

        relay = IntermediateRelay(
            self.socket_b,
            self.socket_c
        )
        relay.start()

        self.socket_d.close()
        time.sleep(0.2)
        self.assert_is_closed(self.socket_a)

    def assert_is_closed(self, _socket):
        import sys
        if sys.platform == "linux":
            # On Linux, if we receive the empty string, the socket is "closed."
            received = _socket.recv(1024)
            self.assertEqual(received, b'')

        elif sys.platform == "win32":
            # On Windows, we get a ConnectionResetError.
            with self.assertRaises(ConnectionResetError):
                received = _socket.recv(1024)

        else:
            print("""WARNING, please add how the socket is supposed to be
            detected to be closed for your platform here.""")


def double_value(message):
    message['value'] *= 2
    return message


def square_value(message):
    message['value'] *= message['value']
    return message