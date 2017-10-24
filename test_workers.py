#!/usr/bin/python3

import unittest
from workers import *


class ReaderWriterTestCase(unittest.TestCase):
    def test_read_equals_sent(self):
        """
        Test that the messages read by the SocketReader
        correspond to those that were written by the SocketWriter.
        """
        message_count = 5


        original_messages = random_test_messages(message_count)
        messages_to_send = ClosableQueue()
        for m in original_messages:
            messages_to_send.put(m)

        writer = SocketWriter(messages_to_send, socket.gethostname(), 12345)

        received_objects = Queue()
        reader = SocketReader(12345, received_objects)

        reader.start()
        writer.start()

        # close the writing queue, which will eventually stop the writer thread
        messages_to_send.close()
        # wait until all messages have been sent.
        messages_to_send.join()

        reader.stop()  # Stop the SocketReader

        messages = []
        for i in range(message_count):
            json_object = received_objects.get()
            message = OnionMessage.from_json(json_object)
            print("successfully received:", message)
            messages.append(message)
            received_objects.task_done()

        received_objects.join()  # wait for all objects to have been received.

        self.assertListEqual(messages, original_messages)


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


def random_string(length=1):
    import random
    import string
    letters = [random.choice(string.ascii_letters) for i in range(length)]
    return ''.join(letters)
