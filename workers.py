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


class Worker(Thread):
    """
    Takes items from the :in_queue:, executes :func: on them,
    then places the results on its :out_queue:.
    Automatically stops whenever the :in_queue.close(): method is called.

    *(see ClosableQueue)*
    """

    def __init__(self, func, in_queue, out_queue):
        super().__init__()
        self.func = func
        self.in_queue = in_queue
        self.out_queue = out_queue

    def run(self):
        for item in self.in_queue:
            result = self.func(item)
            self.out_queue.put(result)


class SplitterWorker(Thread):
    """
    Worker that takes an item from its :in_queue:, and then runs :func: on it.

    *func(item) -> bool*

    If :func(item): returns :True:, the item is placed on :out_queue_a:
    If :func(item): returns :False:, the item is placed on :out_queue_b:
    """

    def __init__(self, func, in_queue, out_queue_a, out_queue_b):
        super().__init__()
        self.func = func
        self.in_queue = in_queue
        self.out_queue_a = out_queue_a
        self.out_queue_b = out_queue_b

    def run(self):
        for item in self.in_queue:
            condition = self.func(item)
            if condition:
                self.out_queue_a.put(item)
            else:
                self.out_queue_b.put(item)
        self.out_queue_a.close()
        self.out_queue_b.close()


class TestSocketReader(Thread):
    """
    Takes the data from a Socket, and tries to parse it into sequences of
    messages.

    Parses each message into a JSON, then passes it to :out_queue:
    """

    def __init__(self, receiving_port):
        super().__init__()
        self.receiving_port = receiving_port
        self._out_queue = ClosableQueue()
        self._running_flag = False
        self._running_lock = Lock()

    def run(self):
        self._running_flag = True
        # Create the receiving socket
        with socket.socket() as recv_socket:
            host = socket.gethostname()
            recv_socket.settimeout(2)
            recv_socket.bind((host, self.receiving_port))
            recv_socket.listen(5)

            while self.running:
                # Safely check if we should stop running.
                try:
                    client_socket, address = recv_socket.accept()
                    received_string = ""
                    empty = False

                    while not empty:
                        buffer = client_socket.recv(1024)
                        empty = (buffer == b'')
                        string = str(buffer, encoding='UTF-8')
                        received_string += string

                    # print("Received string:", received_string)

                    # TODO: Might want to take this out, and simply return the
                    # bytes that we receive, one at a time, since not everyone
                    # might want to use this "split into objects" functionality.
                    objects = split_into_objects(received_string)
                    count = 0

                    with self._out_queue:
                        for obj in objects:
                            self._out_queue.put(obj)
                            count += 1
                            # print("received_object: ", obj)

                    # print(f"done receiving {count} objects for this connection.")
                    client_socket.close()
                except socket.timeout:
                    continue

    @property
    def running(self):
        """ returns if the node is currently running """
        with self._running_lock:
            return self._running_flag

    @running.setter
    def running(self, value):
        with self._running_lock:
            self._running_flag = value

    def stop(self):
        """ tells the node to shutdown. """
        self._out_queue.close()
        self.running = False
        self.join()

    def next(self, block=True, timeout=None):
        """
        Waits for the next item and return it. (This is a blocking call)
        """
        return self._out_queue.get(block, timeout)


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


class TestSocketWriter(Thread):
    """
    Worker that takes messages and writes each of them into a socket connected
    to the given :ip_address: and :port:

    Whenever the :in_queue:.close() function is called, the SocketWriter will
    eventually stop.
    """

    def __init__(self, target_ip, target_port):
        super().__init__()
        self._in_queue = ClosableQueue()
        self._target_ip = target_ip
        self._target_port = target_port

    def run(self):
        with socket.socket() as out_socket:
            out_socket.connect((self._target_ip, self._target_port))

            for message in self._in_queue:
                string_version = str(message)
                bytes_to_send = string_version.encode()
                total_length = len(bytes_to_send)
                sent_so_far = 0

                while sent_so_far < total_length:
                    bytes_sent = out_socket.send(bytes_to_send[sent_so_far:])
                    sent_so_far += bytes_sent

    def write(self, message):
        """ Puts the given message on the outgoing queue to be sent. """
        self._in_queue.put(message)

    def close(self):
        self._in_queue.close()

    @property
    def input(self):
        return self._in_queue


@contextmanager
def test_read_socket(receiving_port) -> TestSocketReader:
    reader = TestSocketReader(receiving_port)
    try:
        reader.start()
        yield reader
    finally:
        reader.stop()


@contextmanager
def test_write_to_socket(target_ip, target_port) -> TestSocketWriter:
    writer = TestSocketWriter(target_ip, target_port)
    try:
        writer.start()
        yield writer
    finally:
        writer.close()


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

            received_objects = split_into_objects(received_so_far)

            for obj, length in received_objects:
                self.received_messages.append(obj)
                # Remove the bytes we used.
                received_so_far = received_so_far[length:]

        self.recv_socket.close()
        self.closed = True


def split_into_objects(string):
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
