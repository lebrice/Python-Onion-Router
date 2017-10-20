#!/usr/bin/python3
"""
Defines the different tasks that will be executed by nodes.
"""

import socket
import sys
from threading import Thread, Lock

PUBLIC_MODULUS = 23
PUBLIC_BASE = 5



class DiffieHellmanReceiverTask():
    """
    Defines a task responsible for answering to key-exchange requests
    """

    def __init__(self, receiving_port, private_key):
        # TODO: Figure out a way of piping up the resulting shared secrets to another parent class (eventually Node)

        self._private_key = private_key

        self._host = socket.gethostname()
        self._port = receiving_port

        # Create a new socket for receiving connections.
        self._receiving_socket = socket.socket()
        self._receiving_socket.bind((self._host, self._port))

        self.shared_secrets = {}
        # We use a lock to prevent concurrent modification of the shared_secrets dictionary
        self.lock = Lock()

        self.running = False

    def __call__(self):
        self.running = True
        self._receiving_socket.listen()  # Listen, with up to 5 queued up connections
        try:
            while self.running:
                client_socket, address = self._receiving_socket.accept()
                task = KeyExchangeTask(self, client_socket, address, private_key)
                client_specific_thread = Thread(None, task)
                client_specific_thread.start()
        finally:
            self._receiving_socket.close()

    def add_shared_secret(self, address, new_shared_secret):
        with self.lock:
            self.shared_secrets[address] = new_shared_secret


class KeyExchangeTask(object):
    def __init__(self, parent_task, exchange_socket, address, private_key):
        # The parent task which we will give the key to.
        self.parent_task = parent_task

        self._exchange_socket = exchange_socket
        self._address = address
        self._private_key = private_key

        self._my_number = PUBLIC_BASE ** self._private_key % PUBLIC_MODULUS

    def __call__(self):
        self._exchange_socket.send(bytes(self._my_number))
        client_public_number_bytes = self._exchange_socket.recv(1024)
        client_public_number = int.from_bytes(client_public_number_bytes, sys.byteorder)

        our_shared_secret = (client_public_number ** self._private_key) % PUBLIC_MODULUS

        with self.parent_task.lock:
            parent_thread.shared_secrets[self._address] = our_shared_secret

        self._exchange_socket.close()


class DiffieHellmanSender(object):
    def __init__(self, private_key):
        self._private_key = private_key

        self.shared_secrets = {}
        self._lock = Lock
    
    def exchange_keys(self, server_ip, server_receiving_port):
        their_public_key, our_shared_secret = initiate_key_exchange(
            self._server_ip,
            self._server_receiving_port,
            self._private_key
        )

    # def get_shared_secret(self, server_ip, server_receiving_port):
    #     exchangeThread = Thread(None, target=initiate_key_exchange(
    #         self.add_shared_secret,
    #         server_ip,
    #         server_receiving_port,
    #         self._private_key
    #     ))
    #     exchangeThread.join()

    def initiate_key_exchange(server_ip, server_receiving_port, private_key):
        socket = socket.socket()
        socket.connect((server_ip, server_receiving_port))

        my_number = PUBLIC_BASE ** self._private_key % PUBLIC_MODULUS

        socket.send(bytes(my_number))

        their_number_in_bytes = socket.recv(1024)
        their_number = int.from_bytes(their_number_in_bytes, sys.byteorder)
        print("Their number is ", their_number)

        our_shared_secret = (their_number ** private_key) % PUBLIC_MODULUS
        print("Our shared secret is", our_shared_secret)
        return their_number, our_shared_secret








