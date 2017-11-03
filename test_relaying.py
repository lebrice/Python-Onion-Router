#!/usr/bin/python3

import unittest
import threading
import time

from relaying import *


class SplitIntoObjectsTestCase(unittest.TestCase):
    def test_split_into_objects_works(self):
        strings = [
            """{"name": "bob", "age": 21}""",
            """
            {
                "name": "clarice",
                "age": 14
            }"""
        ]
        string = ''.join(strings)

        for original_str, result in zip(strings, split_into_objects(string)):
            result_object, length_used = result
            self.assertEqual(json.loads(original_str), result_object)
            self.assertEqual(len(original_str), length_used)

    def test_split_into_objects_sows_correct_used_length(self):
        useful_chars = "{'name': 'bob', 'age': 21}"
        unused_chars = "123456789"
        string = useful_chars + unused_chars

        for result in split_into_objects(string):
            obj, length = result
            self.assertEqual(length, len(useful_chars))
            self.assertEqual(obj, json.loads(useful_chars))


HOST = socket.gethostname()


class SocketReaderTestCase(unittest.TestCase):
    def test_socket_reader_receives_message(self):
        test_message = """
        {
            "value": 10
        }
        """
        sent_obj = json.loads(test_message)
        received_objects = []

        sender = TestMessageSender(12345, test_message)

        recv_socket = socket.socket()
        recv_socket.bind((HOST, 12345))

        recv_socket.listen()

        sender.start()
        client_socket, address = recv_socket.accept()

        reader = SocketReader(client_socket, received_objects)
        reader.start()

        # give time for the reader to receive the message.
        time.sleep(0.2)
        sender.close()
        # Give time for the reader to notice the socket closing.
        time.sleep(0.1)
        self.assertTrue(reader.closed)
        self.assertIn(sent_obj, received_objects)


class TestMessageSender(threading.Thread):
    def __init__(self, target_port, message_to_send):
        super().__init__()
        self.target_port = target_port
        self.message_to_send = message_to_send
        self._socket = socket.socket()

    def start(self):
        time.sleep(0.1)  # give some time for the receiver to be set up.
        super().start()

    def run(self):
        self._socket.connect((socket.gethostname(), self.target_port))
        self._socket.sendall(self.message_to_send.encode())

    def close(self):
        self._socket.close()


