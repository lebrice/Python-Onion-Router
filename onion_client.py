#!/usr/bin/python3
"""
    Module that defines the Onion Client, used by the user to communicate
    through the onion routing network
"""
from contextlib import contextmanager
from threading import Thread
import random
from random import randint
import socket
import json
import time
import packet_manager as pm
import base64

import circuit_tables as ct
import encryption as enc
from errors import OnionError, OnionRuntimeError

BUFFER_SIZE = 4096  # Constant for now
DEFAULT_TIMEOUT = 1

# socket.setdefaulttimeout(DEFAULT_TIMEOUT)


class OnionClient():
    def __init__(self, ip, port, number_of_nodes):
        self.initialized = False
        self.ip = ip
        self.port = port
        self.number_of_nodes = number_of_nodes

        self.circuit_table = ct.circuit_table()
        self.sender_key_table = ct.sender_key_table()
        self.network_list = {}

        self.client_socket = None
        self._entry_node = None

    def connect(self, dir_ip, dir_port):
        """
            called from exterior to tell client to prepare for transmission
            - fetch network list
            - build circuit
        """
        self._contact_dir_node(dir_ip, dir_port)
        self._build_circuit()
        self.initialized = True

    def send(self, url):
        """
            called from exterior to tell client to send message through the circuit
        """
        self.send_through_circuit(url)

    def recv(self, buffer_size):
        """ Receives the given number of bytes from the Onion socket.
        """
        return self.receive_from_circuit(buffer_size)

    def _contact_dir_node(self, dir_ip, dir_port):
        """
            query dir node for network list, without including the client in the list of nodes
            this avoids the problem of the client using itself as a node later on

        """
        pkt = pm.new_dir_packet("dir_query", 0, 0)
        message = None

        with socket.socket() as client_socket:
            client_socket.connect((dir_ip, dir_port))
            client_socket.sendall(pkt.encode())

            rec_bytes = client_socket.recv(BUFFER_SIZE)
            message = json.loads(rec_bytes.decode())

        if message == -1 or message['type'] != "dir":
            raise OnionRuntimeError("ERROR    Unexpected answer from directory\n")

        self.network_list = message['table']

    def _select_random_nodes(self):
        if len(self.network_list['nodes in network']) < self.number_of_nodes:
            raise OnionRuntimeError(
                "ERROR    There are not enough nodes to build the circuit",
                "Current: ",
                len(self.network_list),
                "requested",
                self.number_of_nodes)

        result = random.sample(
            self.network_list['nodes in network'],
            self.number_of_nodes)
        return result

    def _generate_new_circID(self):
        # define a limit to how many circuits the node can be part of
        max_circuit_no = 100

        if self.circuit_table.get_length() == max_circuit_no:
            raise OnionRuntimeError(
                "ERROR    Too many active circuits; could not create circuit.",
                "Current max is ", max_circuit_no,
                "\nTry deleting a circuit before creating a new one"
            )

        # generate a circID that is not in use in the circuit_table
        while True:
            circID = randint(0, 10000)
            if self.circuit_table.get_address(circID) == -1:
                break

        return circID

    def _build_circuit(self):
        nodes = self._select_random_nodes()
        for index, node in enumerate(nodes):
            if index == 0:
                self._connect_with_entry_node(node)
                self._send_create_packet(node)
            else:
                self._send_extend_packet(node, index)

    def _save_entry_node(self, entry_node):
        self.entry_circID = self._generate_new_circID()
        self.circuit_table.add_circuit_entry(
            entry_node['ip'],
            entry_node['port'],
            self.entry_circID)
        self._entry_node = entry_node

    def _send_create_packet(self, entry_node):
        assert self.client_socket is None
        # first link is special: only one to get control "create" packet

        # NOTE: validate how we create and/or reuse sockets.
        self.client_socket = socket.socket()
        self.client_socket.connect((self.entry_node['ip'],
                                    self.entry_node['port']))

        key = enc.generate_fernet_key()
        self.sender_key_table.add_key_entry(self.entry_circID, 0, key)
        ciphered_shared_key = enc.encrypt_RSA(
            key,
            entry_node['public_exp'],
            entry_node['modulus'])
        payload = pm.new_payload(self.ip, self.port, ciphered_shared_key)

        # Create the custom control packet
        pkt = pm.new_control_packet(self.entry_circID, "create", payload)

        # send first half of key exchange
        self.client_socket.sendall(pkt.encode())

        # Obtain a response packet
        rec_bytes = self.client_socket.recv(BUFFER_SIZE)
        message = json.loads(rec_bytes.decode())

        if message == -1 or message['command'] != 'created':
            raise OnionRuntimeError(
                "ERROR    Did not receive expected confirmation packet\n"
            )
            print("         Circuit building exiting. . .")

        # received "created" packet successfully -- store info in tables
        # store connection to first circID, the entry point to the circuit
        self.circuit_table.add_circuit_entry(
            entry_node['ip'],
            entry_node['port'],
            self.entry_circID)
        print("Successfully sent the first 'create' packet")

        # TODO: Make sure that we should really reuse the same socket.
        self.client_socket.close()
        del self.client_socket

    def _send_extend_packet(self, node, layer):
        """
        Send an 'extend' to the rest of the nodes in the circuit that we are
        building.
        """
        assert self.client_socket is None
        
        # NOTE: validate how we create and/or reuse sockets.
        self.client_socket = socket.socket()
        self.client_socket.connect((self.entry_node['ip'],
                                    self.entry_node['port']))

        key = enc.generate_fernet_key()
        ciphered_shared_key = enc.encrypt_RSA(
            key,
            node['public_exp'],
            node['modulus'])

        # data to be placed in "extend" packet payload. nodes will use circIDs to navigate,
        # until a node has decrypted the payload and finds the ip and port of the new node
        encrypted_data = pm.new_relay_payload(
            node['ip'],
            node['port'],
            ciphered_shared_key)

        # apply layers of encryption on shared key + key exchange before sending it
        encrypted_data = self.successive_encrypt(encrypted_data, layer)

        pkt = pm.new_relay_packet(self.entry_circID, "extend", encrypted_data)

        # send first half of key exchange
        self.client_socket.sendall(pkt.encode())

        tries = 0
        rec_bytes = None
        while(tries < 30):
            print("Waiting for a response:")
            try:
                rec_bytes = self.client_socket.recv(BUFFER_SIZE)
            except socket.error as e:
                print("Socket error:", e)
            tries += 1

        message = json.loads(rec_bytes.decode())

        if message == -1 or (message['command'] != 'created' and message['command'] != 'extended'):
            raise OnionRuntimeError(
                "ERROR    Did not receive expected confirmation packet\n"
            )
            print("         Circuit building exiting. . .")

        self.sender_key_table.add_key_entry(self.entry_circID, layer, key)

        self.client_socket.close()
        del self.client_socket

    def send_through_circuit(self, message):
        """
        called from exterior to tell client to send message through the circuit
        """
        if not self.initialized:
            raise OnionRuntimeError(
                "ERROR     Client not initialized. Call .connect() first.\n"
            )

        # get entry point (currently fixed to only one)
        # TODO build more circuits, select a random one in the table
        ip, port = self.circuit_table.get_address(self.entry_circID).split(":")

        # TODO: this is already done, we already know the first node, since we
        # used it in the circuit building portion.
        # self._create(ip, int(port))

        message = pm.new_payload(0, 0, message)
        # apply three encryption layers to message
        encrypted_data = self.successive_encrypt(message, self.number_of_nodes)
        pkt = pm.new_relay_packet(
            self.entry_circID,
            "relay_data",
            encrypted_data)
        self._send(pkt)

    def receive_from_circuit(self):
        rec_bytes = self.client_socket.recv(BUFFER_SIZE)
        message_str = rec_bytes.decode('utf-8')
        message = json.loads(message_str)
        decrypted = self.successive_decrypt(message['encrypted_data'])
        payload = base64.urlsafe_b64decode(decrypted['data']).decode("UTF-8")
        return payload

    def successive_encrypt(self, message, layer_count):
        """
        apply three encryption layers to message
        """
        # apply layers of encryption on shared key + key exchange before sending it
        # e.g. for node 2, apply layer 1 then layer 0
        encrypted_data = message
        for j in range(layer_count - 1, -1, -1):
            key = self.sender_key_table.get_key(self.entry_circID, j)
            encrypted_data = enc.encrypt_fernet(encrypted_data, key)
        return encrypted_data

    def successive_decrypt(self, data):
        """
        remove encryption layers (from node 0 to node 2)
        """
        layer = self.sender_key_table.get_key(self.entry_circID, 0)
        payload = enc.decrypt_fernet(data, layer)
        for i in range(1, self.number_of_nodes):
            layer = self.sender_key_table.get_key(self.entry_circID, i)
            payload = enc.decrypt_fernet(payload, layer)
        return payload
