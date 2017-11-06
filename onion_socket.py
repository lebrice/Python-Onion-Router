#!/usr/bin/python3
""" Module that defines the OnionSocket, used by the user to communicate using
the onion routing network """
from contextlib import contextmanager
import random
import socket
import time

from node import OnionNode
from errors import OnionSocketError, OnionNetworkError

from encryption import *
from messaging import *
import packet_manager as pm
import circuit_tables as ct
import circuit_builder as cb
import relaying
import RSA

# TODO: create a new private key for each OnionSocket
DEFAULT_PRIVATE_KEY = 164


@contextmanager
def socket(onion_node=None):
    if onion_node is None:
        onion_node = OnionNode("my_node", 12350)
    onion_socket = OnionSocket(onion_node)
    try:
        yield onion_socket
    finally:
        onion_socket.close()


class OnionSocket():
    def __init__(self, onion_node=None):
        # TODO: change this private key for each node.
        self.target_ip = None
        self.target_port = None
        if onion_node is None:
            self.node = OnionNode("my_node", 12350)
        else:
            self.node = onion_node

        self.circuit_table = ct.circuit_table()
        self.sender_key_table = ct.sender_key_table()

        # TODO: Need to initialize the node properly.
        self.node.start()
        while(self.node.initialized is not True):
            time.sleep(0.1)  # Thread.yield() equivalent, kindof

    @staticmethod
    def socket(onion_node=None):
        if onion_node is None:
            onion_node = OnionNode("my_node", 12350)
        return OnionSocket(onion_node)

    @property
    def connected(self):
        return (self.target_ip is not None) and (self.target_port is not None)

    def connect(self, target_ip_info):
        """ Connects to the given remote host, through the onion network.
        """
        # NOTE: This might be a good place to build/initialize the circuit?
        self.target_ip, self.target_port = target_ip_info
        # TODO: Might create circuit now ?

    def send(self, data: bytes):
        """ Sends the given data to the remote host through the OnionSocket.
        """
        if not self.connected:
            raise OnionSocketError("Onion network has not been initialized.")
        message = self._create_message(data)
        self.node.send_message(message)

    def recv(self, buffer_size):
        """ Receives the given number of bytes from the Onion socket.
        """
        raise NotImplementedError()

    def close(self):
        """ closes the onionSocket. """
        # TODO
        self.node.stop()

    def _select_three_random_neighbours(self):
        if len(self.node.neighbours) < 3:
            message = f"There are currently not enough nodes for an onion" + \
                f"network to exist. (current: {len(self.node.neighbours)}<3)"
            raise OnionNetworkError(message)
        return random.sample(self.node.neighbours, 3)


    ###
    ###    BEGIN CIRCUIT BUILDING
    ###

    def create_connection(self, node, rsa_keys):
        circID, msg = pm.new_control_packet(0, "create", rsa_keys)
        self.circuit_table.add_circuit_entry(node.ip, node.port, circID)


    # TODO: how do you get ip/port info from an object returned by select three random neighbor
    def build_circuit(self):
        node1, node2, node3 = self._select_three_random_neighbours()
        rsa_keys = RSA.get_private_key_rsa()



    # def _create_message(self, data):
    #     """ Creates a message, to be send accross the OnionNetwork.
    #
    #     NOTE: At the moment, it does
    #
    #         ME ---> A ---> B ---> C ---> EXIT
    #
    #     """
    #     ME = (socket.gethostname(), self.node._receiving_port)
    #     A, B, C = self._select_three_random_neighbours()
    #     EXIT = (self.target_ip, self.target_port)
    #
    #     keys = [self.node.shared_secrets.get(n) for n in [A, B, C]]
    #     # key_a = self.node.shared_secrets.get(A)
    #     # key_a = self.node.shared_secrets.get(A)
    #     # key_a = self.node.shared_secrets.get(A)
    #     key_a, key_b, key_c = keys
    #
    #     # TODO: Replace with whichever encryptor makes the most sense.
    #     encryptor = DoNothingEncryptor
    #
    #     # NOTE: This is just pseudocode. We might use a very different approach
    #     exit_message = OnionMessage(
    #         header="EXIT",
    #         source=C,
    #         destination=EXIT,
    #         # TODO: the data between C and the Website needs to be encrypted!
    #         data=data
    #     )
    #     message3 = OnionMessage(
    #         header="RELAY",
    #         source=B,
    #         destination=C,
    #         data=encryptor.encrypt(exit_message.to_json_string(), key_c)
    #     )
    #     message2 = OnionMessage(
    #         header="RELAY",
    #         source=A,
    #         destination=B,
    #         data=encryptor.encrypt(message3.to_json_string(), key_b)
    #     )
    #     message1 = OnionMessage(
    #         header="RELAY",
    #         source=ME,
    #         destination=A,
    #         data=encryptor.encrypt(message2.to_json_string(), key_a)
    #     )
    #     print("\nexit_message:", exit_message)
    #     print("\nmessage3", message3)
    #     print("\nmessage2", message2)
    #     print("\nmessage1", message1)
    #     return message1


