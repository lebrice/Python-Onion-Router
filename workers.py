#!/usr/bin/python3
"""
Defines Workers that will be used to carry out various tasks.
"""
from threading import Thread
from queue import Queue
import socket

from messaging import OnionMessage


class ClosableQueue(Queue):
    """
    Queue subclass that can be closed. By closing the Queue,
    the threads that are consuming its output are stopped.
    """
    SENTINEL = object()

    def close(self):
        self.put(self.SENTINEL)

    def __iter__(self):
        while True:
            item = self.get()
            try:
                if item is self.SENTINEL:
                    return  # Cause the thread to exit.
                yield item
            finally:
                self.task_done()


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


class SocketReader(Thread):
    """
    Takes the data from a Socket, and tries to parse it into sequences of
    messages.

    Parses each message into :out_queue:
    """

    def __init__(self, receiving_port, out_queue):
        super().__init__()
        self.receiving_port = receiving_port
        self.out_queue = out_queue
        self.running = False

    def run(self):
        self.running = True
        # Create the receiving socket
        with socket.socket() as recv_socket:
            host = socket.gethostname()
            recv_socket.bind((host, self.receiving_port))
            recv_socket.listen(5)

            while self.running:
                client_socket, address = recv_socket.accept()
                received_string = ""
                empty = False
                while not empty:
                    buffer = client_socket.recv(1024)
                    empty = buffer == b''
                    print("received: ", buffer, "\nEmpty:", empty)
                    string = str(buffer, encoding='UTF-8')
                    received_string += string
                
                # print("Received string:", received_string)
                objects = split_into_objects(received_string)
                for obj in split_into_objects(received_string):
                    self.out_queue.put(obj)
                    self.out_queue.task_done()
                    # print("received_object: ", obj)

                client_socket.close()

    def stop(self):
        self.running = False


def split_into_objects(string):
    """
    attempts to split the given string into a series of JSON objects.
    """
    import json
    string_so_far = ""
    open_bracket_count = 0
    closed_bracket_count = 0
    for index, char in enumerate(string):
        string_so_far += char
        if char == '{':
            open_bracket_count += 1
        elif char == '}':
            closed_bracket_count += 1
        if open_bracket_count == closed_bracket_count:
            try:
                obj = json.loads(string_so_far)
                string_so_far = ""
                open_bracket_count = 0
                closed_bracket_count = 0
                yield obj
            except json.JSONDecodeError:
                pass  # OK. that wasn't a valid json.


class SocketWriter(Thread):
    """
    Worker that takes messages from :in_queue: (which should be a
    ClosableQueue) and writes each of them into a socket connected to the
    given :ip_address: and :port:

    Whenever the :in_queue:.close() function is called, the SocketWriter will
    eventually stop.
    """

    def __init__(self, in_queue: ClosableQueue, ip_address, port):
        super().__init__()
        self.in_queue = in_queue
        self.ip_address = ip_address
        self.port = port
        self.out_socket = socket.socket()

        self.sent_count = 0

    def run(self):
        self.out_socket.connect((self.ip_address, self.port))
        for message in self.in_queue:
            string_version = str(message)
            bytes_to_send = string_version.encode()
            total_length = len(bytes_to_send)
            sent_so_far = 0
            # print("sending:", string_version)
            while sent_so_far < total_length:
                bytes_sent = self.out_socket.send(bytes_to_send[sent_so_far:])
                sent_so_far += bytes_sent
                print("sent_so_far:", sent_so_far)
            self.sent_count += 1
            print(f"successfully sent message #{self.sent_count}")
        print(f"done sending all {self.sent_count} messages.")


def main():

    messages_to_send = ClosableQueue()
    for i in range(3):
        messages_to_send.put(random_test_message(size=i*5))
    writer = SocketWriter(messages_to_send, socket.gethostname(), 12345)

    received_messages = Queue()
    reader = SocketReader(12345, received_messages)
    reader.start()
    writer.start()
    messages_to_send.close()
    messages_to_send.join()

    received_messages.join()
    reader.stop()

    while not received_messages.empty():
        print("successfully received:", received_messages.get())

    print("done.")


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

if __name__ == '__main__':
    main()
