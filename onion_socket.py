#!/usr/bin/python3
""" Module that defines the OnionSocket, used by the user to communicate using
the onion routing network """
import random
import time

from node import OnionNode
from errors import OnionSocketError, OnionNetworkError


class OnionSocket():
    def __init__(self, onion_node=None):
        """ TODO: Create the OnionSocket."""
        self.my_private_key = 455
        if onion_node is None:
            self.node = OnionNode("my_node", 12350, self.my_private_key)
        else:
            self.node = onion_node

    @staticmethod
    def socket():
        """ Creates a new OnionSocket.

        (Made to imitate *socket.socket()* method.)
        """
        return OnionSocket()

    def connect(self, target_ip_info):
        """ Connects to the given remote host, through the onion network.
        """
        # NOTE: This might be a good place to build/initialize the circuit?
        self.target_ip, self.target_port = target_ip_info

        # TODO: Need to initialize the node properly.
        self.node.start()
        while(self.node.initialized is not True):
            time.sleep(0.1)  # Thread.yield() equivalent, kindof.
        print("All is good.")

    def send(self, data: bytes):
        """ Sends the given data to the remote host through the OnionSocket.
        """
        message = self._create_message(data)
        print(message)
        raise NotImplementedError()

    def recv(self, buffer_size):
        """ Receives the given number of bytes from the Onion socket.
        """
        raise NotImplementedError()

    def _select_random_neighbours(self):
        if not self.node.running:
            raise OnionSocketError("Onion network has not been initialized.")
        if len(self.node.neighbours) < 3:
            message = f"There are currently not enough nodes for an onion" + \
                f"network to exist. (current: {len(self.node.neighbours)}<3)"
            raise OnionNetworkError(message)
        return random.sample(self.node.neighbours, 3)

    def _create_message(self, data):
        A, B, C = self._select_random_neighbours()
        # TODO: Implement the create_message mechanic
        print(A, B, C)
        return "BOB"
