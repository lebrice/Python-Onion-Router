#!/usr/bin/python3
"""
    Module that defines the Onion Client, used by the user to communicate using
    the onion routing network
"""
from contextlib import contextmanager
import random
import socket
import time

from node import OnionNode
from errors import OnionSocketError, OnionNetworkError

import sender_circuit_builder as scb
import circuit_tables as ct
import RSA

BUFFER_SIZE = 1024 # Constant for now
DEFAULT_TIMEOUT = 1
NUMBER_OF_NODES = 3

class OnionClient():
    def __init__(self, onion_node=None):
        self.target_ip = None
        self.target_port = None

        self.circuit_table = ct.circuit_table()
        self.sender_key_table = ct.sender_key_table()
        self.network_list = {}

        self._build_circuit()

        # # TODO: Need to initialize the node properly.
        # self.node.start()
        # while(self.node.initialized is not True):
        #     time.sleep(0.1)  # Thread.yield() equivalent, kindof

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
        # if not self.connected:
        #     raise OnionSocketError("Onion network has not been initialized.")
        # #message = self._create_message(data)
        # self.node.send_message(message)

    def recv(self, buffer_size):
        """ Receives the given number of bytes from the Onion socket.
        """
        raise NotImplementedError()

    def _select_three_random_neighbours(self):
        if len(self.network_list) < 3:
            message = "There are currently not enough nodes for an onion" + \
                "network to exist. (current: {len(self.node.neighbours)}<3)"
            raise OnionNetworkError(message)
        return random.sample(self.network_list['nodes in network'], 3)

    def _build_circuit(self):
        node1, node2, node3 = self._select_three_random_neighbours()
        nodes = [node1, node2, node3]
        builder = scb.SenderCircuitBuilder(nodes, self.circuit_table, self.sender_key_table)
        builder.start()
        builder.join()

    def _create(self, ip, port):
        self.client_socket = socket.socket(DEFAULT_TIMEOUT)
        self.client_socket.connect((ip, port))

    def _send(self, message_str):
        message_bytes = message_str.encode('utf-8')
        self.client_socket.sendall(message_bytes)

    def _close(self):
        self.client_socket.close()



