#!/usr/bin/python3
""" Module that defines the OnionSocket, used by the user to communicate using
the onion routing network """
import random
import socket
import time

from node import OnionNode
from errors import OnionSocketError, OnionNetworkError

from encryption import *
from messaging import *


class OnionSocket():
    def __init__(self, onion_node=None):
        # TODO: change this private key for each node.
        self.my_private_key = 164  # Some random value
        self.target_ip = None
        self.target_port = None
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
        if not self.node.running:
            raise OnionSocketError("Onion network has not been initialized.")
        message = self._create_message(data)
        raise NotImplementedError()

    def recv(self, buffer_size):
        """ Receives the given number of bytes from the Onion socket.
        """
        raise NotImplementedError()

    def _select_three_random_neighbours(self):
        if len(self.node.neighbours) < 3:
            message = f"There are currently not enough nodes for an onion" + \
                f"network to exist. (current: {len(self.node.neighbours)}<3)"
            raise OnionNetworkError(message)
        return random.sample(self.node.neighbours, 3)

    def _create_message(self, data):
        """ Creates a message, to be send accross the OnionNetwork.

        NOTE: At the moment, it does

            ME ---> A ---> B ---> C ---> EXIT
        
        """
        ME = (socket.gethostname(), self.node._receiving_port)
        A, B, C = self._select_three_random_neighbours()
        EXIT = (self.target_ip, self.target_port)

        keys = [self.node.shared_secrets.get(n) for n in [A, B, C]]
        # key_a = self.node.shared_secrets.get(A)
        # key_a = self.node.shared_secrets.get(A)
        # key_a = self.node.shared_secrets.get(A)
        key_a, key_b, key_c = keys

        # TODO: Replace with whichever encryptor makes the most sense.
        encryptor = DoNothingEncryptor

        # NOTE: This is just pseudocode. We might use a very different approach
        exit_message = OnionMessage(
            header="EXIT",
            source=C,
            destination=EXIT,
            # TODO: the data between C and the Website needs to be encrypted!
            data=data
        )
        message3 = OnionMessage(
            header="RELAY",
            source=B,
            destination=C,
            data=encryptor.encrypt(exit_message.to_json_string(), key_c)
        )
        message2 = OnionMessage(
            header="RELAY",
            source=A,
            destination=B,
            data=encryptor.encrypt(message3.to_json_string(), key_b)
        )
        message1 = OnionMessage(
            header="RELAY",
            source=ME,
            destination=A,
            data=encryptor.encrypt(message2.to_json_string(), key_a)
        )
        print("exit_message:", exit_message)
        print("message3", message3)
        print("message2", message2)
        print("message1", message1)
        self.node.send_message(message1)
