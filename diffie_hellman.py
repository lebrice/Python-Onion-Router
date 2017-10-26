#!/usr/bin/python3
"""
Defines the different tasks that will be executed by nodes.
"""

import socket
import sys
from threading import Thread, Lock
from queues import ClosableQueue

PUBLIC_MODULUS = 23
PUBLIC_BASE = 5


class DiffieHellmanReceiver(threading.Thread):
    """
    Defines a worker responsible for answering key-exchange requests
    """

    def __init__(self, receiving_port, private_key, shared_secrets):
        """
        Creates a new Receiver.

        :shared_secrets: : the dictionary of shared_secrets. The receiver will add secret keys to it.
        """
        self._private_key = private_key

        self._host = socket.gethostname()
        self._port = receiving_port
        self.shared_secrets = shared_secrets

        self._running_flag = False
        self._running_lock = Lock()

    def run(self):
        self.running = True
        with socket.socket() as receiving_socket:
            receiving_socket.listen()  # Listen

            while self.running:
                client_socket, address = receiving_socket.accept()
                task = KeyExchangeTask(
                    client_socket,
                    address,
                    self.private_key,
                    self.shared_secrets
                )
                client_specific_thread = Thread(target=task)
                client_specific_thread.start()

    @property
    def running(self) -> bool:
        with self._running_lock:
            return self._running_flag

    @running.setter
    def running(self, value: bool):
        with self._running_lock:
            self._running_flag = value


class KeyExchangeTask(object):
    def __init__(self, exchange_socket, address, private_key, shared_secrets):

        self._exchange_socket = exchange_socket
        self._address = address
        self._private_key = private_key

        self.shared_secrets

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
