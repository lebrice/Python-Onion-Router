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


class ReaderWriterTestCase(unittest.TestCase):
    """ 
    TODO: update this test, it is currently disabled because the classes
    changed. 
    """
    @unittest.skip
    def test_read_equals_sent(self):
        """
        Test that the messages read by the SocketReader correspond to those
        originally written by the SocketWriter.
        """
        message_count = 10

        # Start a reader, and let him wait for a connection.
        # Where the Reader puts incoming objects
        received_objects = ClosableQueue()
        reader = TestSocketReader(12345, received_objects)
        reader.start()  # Start the reader. It will wait for messages.

        # Create random messages to write to a socket
        original_messages = random_test_messages(message_count)
        # The messages to be written are held in a ClosableQueue
        messages_to_send = ClosableQueue()
        for m in original_messages:
            messages_to_send.put(m)  # Add each message to the queue.

        # Create a SocketWriter, and give him the queue of messages to send.
        writer = TestSocketWriter(messages_to_send, socket.gethostname(), 12345)
        writer.start()  # Start the writer

        # close the writing queue, which eventually stops the writer thread
        messages_to_send.close()
        # wait until all messages have been processed by the SocketWriter.
        writer.join()

        # If a message is done being sent by the socketWriter, than it is
        # also done being received by the socketReader, since we use TCP.

        # wait for the reader to have finished reading all messages.
        reader.join()

        messages = []
        for json_object in received_objects:
            # convert the received json to an OnionMessage instance
            message = OnionMessage.from_json(json_object)
            # print("successfully received:", message)
            messages.append(message)

        # Assert that both lists should match perfectly.
        self.assertCountEqual(messages, original_messages)


def random_test_messages(count):
    return [random_test_message(i*5) for i in range(count)]


def random_test_message(size):
    data = random_string(size)
    bob = f"""
        {{
            "header": "ONION ROUTING G12",
            "source": "127.0.0.1",
            "destination": "",
            "data": "{data}"
        }}
    """
    return OnionMessage.from_json_string(bob)




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
