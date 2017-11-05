#!/usr/bin/python3

import unittest
import threading
import socket
import time
import json

from relaying import *

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
        port += 2
        self.socket_a.close()
        self.socket_b.close()
        self.socket_c.close()
        self.socket_d.close()



    def test_read_from_left_goes_to_right(self):
        test_message = """{
            "value": 10
        }"""
        sent_obj = json.loads(test_message)

       

def random_string(length):
    import random
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
