#!/usr/bin/python3
"""
Defines Workers that will be used to carry out various tasks.
"""
from contextlib import contextmanager
from threading import Thread, Lock
from typing import List
import socket
from socket import SocketType

from messaging import OnionMessage
from queues import ClosableQueue

BUFFER_SIZE = 4096


class SocketReader(Thread):
    """
    Reads from a given socket, and whenever it receives a message, adds it
    in the given received_messages list.
    """
    def __init__(self, _socket: SocketType, received_messages: List):
        super().__init__()
        self.recv_socket = _socket
        self.received_messages = received_messages
        self.closed = False

    def run(self):
        received_so_far = ""

        empty = False

        while not empty:
            received_bytes = self.recv_socket.recv(BUFFER_SIZE)

            empty = (received_bytes == b'')
            if empty:
                break
            received_string = str(received_bytes, encoding="UTF-8")
            received_so_far += received_string

            received_objects = split_into_objects_and_lengths(received_so_far)

            for obj, length in received_objects:
                self.received_messages.append(obj)
                # Remove the bytes we used.
                received_so_far = received_so_far[length:]

        self.recv_socket.close()
        self.closed = True


def split_into_objects_and_lengths(string):
    """
    splits the given string into a series of tuples:
    (JSON object, length of string used to create that object).
    """
    import json
    string_so_far = ""
    open_bracket_count = 0
    closed_bracket_count = 0
    for char in string:
        string_so_far += char
        if char == '{':
            open_bracket_count += 1
        elif char == '}':
            closed_bracket_count += 1
        if open_bracket_count == closed_bracket_count:
            try:
                obj = json.loads(string_so_far)
                # Return the object, since the parsing worked.
                yield (obj, len(string_so_far))

            except json.JSONDecodeError:
                pass  # OK. that wasn't a valid json. Keep trying.

            else:
                # No exceptions ocurred. We reset the counter variables.
                string_so_far = ""
                open_bracket_count = 0
                closed_bracket_count = 0


def split_into_objects(string):
    """
    splits the given string into a series of JSON objects.
    """
    import json
    string_so_far = ""
    open_bracket_count = 0
    closed_bracket_count = 0
    for char in string:
        string_so_far += char
        if char == '{':
            open_bracket_count += 1
        elif char == '}':
            closed_bracket_count += 1
        if open_bracket_count == closed_bracket_count:
            try:
                obj = json.loads(string_so_far)
                yield obj  # Return the object, since the parsing worked.

            except json.JSONDecodeError:
                pass  # OK. that wasn't a valid json. Keep trying.

            else:
                # No exceptions ocurred. We reset the counter variables.
                string_so_far = ""
                open_bracket_count = 0
                closed_bracket_count = 0
