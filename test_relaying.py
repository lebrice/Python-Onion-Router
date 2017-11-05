#!/usr/bin/python3

import unittest
import threading
import socket
import time

from relaying import *


class IntermediateRelayTestCase(unittest.TestCase):

    def setUp(self):
        pass


    def test_read_from_left_goes_to_right(self):
        test_message = """{
            "value": 10
        }"""
        sent_obj = json.loads(test_message)

       

def random_string(length):
    import random
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
