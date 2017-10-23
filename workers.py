#!/usr/bin/python3
"""
Defines Workers that will be used to carry out various tasks.
"""
from threading import Thread
from queue import Queue


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

import socket
from messaging import OnionMessage

class SocketReader(Thread):
    """
    Takes the data from a Socket, and tries to parse it into sequences of messages.
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
            recv_socket.listen()

            bytes_received = 0

            while self.running:
                client_socket, address = recv_socket.accept()

                buffer = client_socket.recv(1024)
                print("Received:", buffer)

                is_valid = False
                try:
                    string = str(buffer, encoding='UTF-8')
                    is_valid = OnionMessage.is_valid_string(string)
                    print("is_valid:", is_valid)
                    

                except UnicodeDecodeError as err:
                    print("invalid")
                else:
                    message = OnionMessage.from_json_string(string)
                    self.out_queue.put(message)

    def stop(self):
        self.running = False
        self.join()

def main():
    received_messages = ClosableQueue(10)
    reader = SocketReader(12345, received_messages)
    reader.start()

    sender = Thread(target=send)
    sender.start()
    sender.join()
    reader.stop()
    reader.join()

    message = received_messages.get()
    print("successfully received:", message)

def send():
    sock = socket.socket()
    remote_host = socket.gethostname()
    remote_host_port = 12345
    sock.connect((remote_host, remote_host_port))

    bob = """
        {
            "header": "ONION ROUTING G12",
            "source": "127.0.0.1",
            "destination": "",
            "data": null
        }
    """
    message = OnionMessage.from_json_string(bob)
    sock.send(message.to_bytes())
    return


if __name__ == '__main__':
    main()