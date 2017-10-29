#!/usr/bin/python3
"""
Defines Workers that will be used to carry out various tasks.
"""
from contextlib import contextmanager
from threading import Thread, Lock
import socket

from messaging import OnionMessage
from queues import ClosableQueue


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


class SocketReader(Thread):
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
            recv_socket.bind((host, self.receiving_port))
            recv_socket.listen(5)

            while True:
                # Safely check if we should stop running.
                with self._running_lock:
                    if not self._running_flag:
                        break

                # print("starting")
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

                print(f"done receiving {count} objects for this connection.")
                client_socket.close()

    def is_running(self):
        with self._running_lock:
            return self._running_flag

    @property
    def out(self):
        return self._out_queue

    def stop(self, timeout=None):
        self._out_queue.close()
        with self._running_lock:
            self._running_flag = False
        self.join()

    def next(self):
        """
        Waits for the next item and return it. (This is a blocking call)
        """
        return self._out_queue.get()


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


class SocketWriter(Thread):
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
                # print("sending:", string_version)

                while sent_so_far < total_length:
                    bytes_sent = out_socket.send(bytes_to_send[sent_so_far:])
                    sent_so_far += bytes_sent
                    # print("sent_so_far:", sent_so_far)
                self.sent_count += 1
                # print(f"successfully sent message #{self.sent_count}")
            print(f"done sending all {self.sent_count} messages.")

    def write(self, message):
        """ Puts the given message on the outgoing queue to be sent. """
        self._in_queue.put(message)

    def close(self):
        self._in_queue.close()

    @property
    def input(self):
        return self._in_queue


@contextmanager
def read_socket(receiving_port) -> SocketReader:
    reader = SocketReader(receiving_port)
    try:
        reader.start()
        yield reader
    finally:
        reader.stop()


@contextmanager
def write_to_socket(target_ip, target_port) -> SocketWriter:
    writer = SocketWriter(target_ip, target_port)
    try:
        writer.start()
        yield writer
    finally:
        writer.close()
