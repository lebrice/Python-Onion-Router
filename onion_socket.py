#!/usr/bin/python3
""" Module that defines the OnionSocket, used by the user to communicate using
the onion routing network """
import random

from node import OnionNode
from errors import OnionSocketError


class OnionSocket():
    def __init__(self):
        """ TODO: Create the OnionSocket."""
        self.my_private_key = 455
        self.node = OnionNode("my_node", 12350, self.my_private_key)

    @staticmethod
    def socket() -> OnionSocket:
        """ Creates a new OnionSocket.

        (Made to imitate *socket.socket()* method.)
        """
        # TODO: Implement this correctly.
        return OnionSocket()

    def connect(self, target_ip_info):
        """ Connects to the given remote host, through the onion network.
        """
        # NOTE: This might be a good place to build/initialize the circuit?
        self.target_ip, self.target_port = target_ip_info
        raise NotImplementedError()

    def send(data: bytes):
        """ Sends the given data to the remote host through the OnionSocket.
        """
        raise NotImplementedError()

    def recv(self, buffer_size):
        """ Receives the given number of bytes from the Onion socket. """
        raise NotImplementedError()

    def create_message(data):
        A, B, C = _select_random_neighbours()

    def _select_random_neighbours(self):
        if not self.node.is_running:
            raise OnionSocketError("Onion network has not been initialized.")
        if len(self.node.neighbours) < 3:
            raise OnionSocketError("""There are currently not enough nodes for
            an onion network to exist.""")
        return *random.sample(self.node.neighbours, 3)