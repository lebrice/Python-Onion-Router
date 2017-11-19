#!/usr/bin/python3
"""
    Module that defines the Onion Client, used by the user to communicate
    through the onion routing network
"""
from contextlib import contextmanager
import random
import socket
import json
import time
import packet_manager as pm
from errors import OnionSocketError, OnionNetworkError

import sender_circuit_builder as scb
import circuit_tables as ct
import RSA

BUFFER_SIZE = 1024 # Constant for now
DEFAULT_TIMEOUT = 1
NUMBER_OF_NODES = 3
DIRECTORY_IP = "127.0.0.1"
DIRECTORY_PORT = "12345"

class OnionClient():
    def __init__(self, onion_node=None):
        self.initialized = False

        self.circuit_table = ct.circuit_table()
        self.sender_key_table = ct.sender_key_table()
        self.network_list = {}

    def connect(self):
        """
            called from exterior to tell client to prepare for transmission
            - fetch network list
            - build circuit
        """
        self._contact_dir_node()
        self._build_circuit()
        self.initialized = True

    def send(self, data):
        """
            called from exterior to tell client to send message through the circuit
        """
        if not self.initialized:
            print("ERROR     Client not initialized. Call OnionClient.connect() first.\n")
            return


    def recv(self, buffer_size):
        """ Receives the given number of bytes from the Onion socket.
        """
        raise NotImplementedError()

    def _contact_dir_node(self):
        """
            query dir node for network list, without including the client in the list of nodes
            this avoids the problem of the client using itself as a node later on

        """

        pkt = pm.new_dir_packet("dir_query", 0, 0)
        self._create(DIRECTORY_IP, DIRECTORY_PORT)
        self._send(pkt)

        # wait for a response packet; 3 tries
        tries = 3
        rec_bytes = 0
        while tries != 0:
            try:
                rec_bytes = self.client_socket.recv(BUFFER_SIZE)
            except socket.timeout:
                tries -= 1
                if tries == 0:
                    print("ERROR    Timeout while waiting for confirmation packet [3 tries]\n")
                    print("         Directory connection exiting. . .")
                    self._close()
                    return
                continue

        message = json.load(rec_bytes.decode())

        if message['type'] != "dir":
            print("ERROR    Unexpected answer from directory")
            self._close()

        self.network_list = message['table']


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



