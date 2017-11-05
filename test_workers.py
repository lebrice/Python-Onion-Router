#!/usr/bin/python3

import json
import unittest
import threading
import time
from workers import *


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
        results = split_into_objects_and_lengths(string)
        for original_str in strings:
            result = results.__next__()
            result_object, length_used = result
            self.assertEqual(json.loads(original_str), result_object)
            self.assertEqual(len(original_str), length_used)

    def test_split_into_objects_shows_correct_used_length(self):
        useful_chars = "{'name': 'bob', 'age': 21}"
        unused_chars = "123456789"
        string = useful_chars + unused_chars

        for result in split_into_objects(string):
            obj, length = result
            self.assertEqual(length, len(useful_chars))
            self.assertEqual(obj, json.loads(useful_chars))

HOST = socket.gethostname()
PORT = 12345


class SocketReaderTestCase(unittest.TestCase):

    def setUp(self):
        # Change ports each time, such that the tests dont conflict with one
        # another.
        global PORT
        PORT += 1
        self.port = PORT

    def test_socket_reader_receives_message(self):
        test_message = """
        {
            "value": 10
        }
        """
        self.assert_well_received(test_message)

    def test_works_with_fraction_of_buffer_size(self):
        string = random_string(int(BUFFER_SIZE * 1.5))
        test_message = f"""
        {{
            "value": "{string}"
        }}
        """
        self.assert_well_received(test_message)

    def test_works_with_long_messages(self):
        string = random_string(BUFFER_SIZE * 5)
        test_message = f"""
        {{
            "value": "{string}"
        }}
        """
        self.assert_well_received(test_message)

    def assert_well_received(self, test_message):
        sent_obj = json.loads(test_message)
        received_objects = []

        sender = TestMessageSender(self.port, test_message)

        recv_socket = socket.socket()
        recv_socket.bind((HOST, self.port))

        recv_socket.listen()

        sender.start()
        client_socket, address = recv_socket.accept()
        reader = SocketReader(client_socket, received_objects)
        reader.start()

        recv_socket.close()

        # give time for the reader to receive the message.
        time.sleep(0.2)
        sender.close()
        # Give time for the reader to notice the socket closing.
        time.sleep(0.1)
        self.assertTrue(reader.closed)
        self.assertIn(sent_obj, received_objects)

    def test_closes_properly(self):
        test_message = """

        {
            "value": 123
        }
        """
        sent_obj = json.loads(test_message)
        received_objects = []

        sender = TestMessageSender(self.port, test_message)

        recv_socket = socket.socket()
        recv_socket.bind((HOST, self.port))

        recv_socket.listen()

        sender.start()
        client_socket, address = recv_socket.accept()
        reader = SocketReader(client_socket, received_objects)
        reader.start()

        recv_socket.close()

        # give time for the reader to receive the message.
        time.sleep(0.2)
        # The reader should still have its socket open, even if the entire
        # message was sent.
        self.assertFalse(reader.closed)
        # Close the sender
        sender.close()
        time.sleep(0.1)
        # The reader should have closed its end by now.
        self.assertTrue(reader.closed)


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


def random_string(length=1):
    import random
    import string
    letters = [random.choice(string.ascii_letters) for i in range(length)]
    return ''.join(letters)
