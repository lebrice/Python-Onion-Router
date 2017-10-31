#!/usr/bin/python3
"""
Defines the different tasks that will be executed by nodes.
"""

import socket
import sys
from threading import Thread, Lock
from queues import ClosableQueue

PUBLIC_ROOT = 23
PUBLIC_BASE = 5

MAX_PUBLIC_KEY_LENGTH_BYTES = 1024


class DiffieHellmanReceiver(Thread):
    """ Defines a worker responsible for answering key-exchange requests.

    Whenever a request is received at the :receiving_port:, the key exchange
    takes place, and the resulting shared_key and public_key are put until the
    :shared_secrets: dict.
    """

    def __init__(self, receiving_port, private_key, shared_secrets):
        """ Creates a new Receiver Thread that responds to key exchange requests.

        Arguments:
            - receiving_port: The port on which to listen for requests.
            - private_key: The private key to use while creating keys.
            - shared_secrets: : the dictionary of shared_secrets.
        """
        super().__init__()
        self._private_key = private_key

        self._host = socket.gethostname()
        self._port = receiving_port
        self.shared_secrets = shared_secrets

        self._running_flag = False
        self._running_lock = Lock()

    def run(self):
        self.running = True
        with socket.socket() as receiving_socket:
            receiving_socket.bind((self._host, self._port))
            receiving_socket.listen()  # Listen

            while self.running:
                client_socket, address = receiving_socket.accept()
                print(f"got a connection from {address}")
                client_specific_thread = Thread(
                    target=get_and_store_keys(
                        client_socket,
                        address,
                        self._private_key,
                        self.shared_secrets
                    )
                )
                client_specific_thread.start()

    @property
    def running(self) -> bool:
        with self._running_lock:
            return self._running_flag

    @running.setter
    def running(self, value: bool):
        with self._running_lock:
            self._running_flag = value

    def stop(self):
        self.running = False


def get_and_store_keys(client_socket, address, private_key, shared_secrets):
    """ Retrieves the shared secret using *exchange_keys()* and stores it in the
    given dict as a tuple (public_key, shared_secret).
    """
    public_key, secret = exchange_keys(client_socket, private_key)
    print(f"public key: {public_key}, secret: {secret}")
    shared_secrets[address] = (public_key, secret)
    client_socket.close()


def get_shared_secret(server_ip, server_receiving_port, private_key):
    """Perform a key exchange with the specified remote host.
    Returns:
        a tuple containing (the other host's public key, our shared secret)
    """
    with socket.socket() as my_socket:
        my_socket.connect((server_ip, server_receiving_port))
        return exchange_keys(my_socket, private_key)


def exchange_keys(exchange_socket, private_key):
    """ exchange public keys over the given socket. """
    my_number = compute_public_key(private_key)
    print
    exchange_socket.send(key_to_bytes(my_number))
    server_key_in_bytes = exchange_socket.recv(MAX_PUBLIC_KEY_LENGTH_BYTES)
    server_public_key = key_from_bytes(server_key_in_bytes)
    print(f"sent {my_number}, received {server_public_key}")
    our_shared_secret = compute_shared_secret(private_key, server_public_key)
    return server_public_key, our_shared_secret


def compute_public_key(private_key):
    """ Computes the public key associated with the given private key. 

    Uses the publicly available PUBLIC_BASE and PUBLIC_MODULUS variables.
    """
    return PUBLIC_BASE ** private_key % PUBLIC_ROOT


def compute_shared_secret(private_key, other_public_key):
    """ Computes the shared secret given the private key and the peer's
    public key. """
    return (other_public_key ** private_key) % PUBLIC_ROOT




def key_from_bytes(some_bytes: bytes) -> int:
    return int.from_bytes(some_bytes, sys.byteorder)


def key_to_bytes(key: int) -> bytes:
    return key.to_bytes(MAX_PUBLIC_KEY_LENGTH_BYTES, sys.byteorder)
