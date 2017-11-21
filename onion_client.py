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

socket.setdefaulttimeout(None)




class OnionClient(Thread):
    def __init__(self, ip, port, number_of_nodes):
        super().__init__()
        self.initialized = False
        self.ip = ip
        self.port = port
        self.number_of_nodes = number_of_nodes

        self.circuit_table = ct.circuit_table()
        self.sender_key_table = ct.sender_key_table()
        self.network_list = {}

    def connect(self, dir_ip, dir_port):
        """
            called from exterior to tell client to prepare for transmission
            - fetch network list
            - build circuit
        """
        self._contact_dir_node(dir_ip, dir_port)
        self._build_circuit()
        self.initialized = True
        self.running = False

    def run(self):
        self.running = True

        if self.initialized:
            with socket.socket() as receiving_socket:
                receiving_socket.settimeout(DEFAULT_TIMEOUT)
                receiving_socket.bind((self.ip, self.port))
                receiving_socket.listen()
                while self.running:
                    # Wait for the next message to arrive.
                    try:
                        client_socket, address = receiving_socket.accept()

                        # TODO check received packet and remove layers here
                        # client_thread = ns.NodeSwitchboard(client_socket, address,
                        #                                    self.circuit_table,
                        #                                    self.node_key_table,
                        #                                    self.node_relay_table,
                        #                                    self.rsa_keys)
                        # client_thread.start()
                    except socket.timeout:
                        continue
        else:
            print("ERROR    Client not initialized. Call .connect() first")

    def stop(self):
        self.running = False

    def send(self, url):
        """
            called from exterior to tell client to send message through the circuit
        """
        if not self.initialized:
            raise OnionRuntimeError("ERROR     Client not initialized. Call .connect() first.\n")

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
        if nodes == -1:
            return

        # will always send the packet through the first node to reach the others
        entry_node = nodes[0]

        self._create(entry_node['ip'], entry_node['port'])
        with socket.socket() as client_socket:
            client_socket.connect((entry_node['ip'], entry_node['port']))

            # first link is special: only one to get control "create" packet
            destID = self._generate_new_circID()
            self.entry_circID = destID
            self.circuit_table.add_circuit_entry(
                entry_node['ip'],
                entry_node['port'],
                destID)
            self.sender_key_table.add_key_entry(destID, i, k)
            payload = pm.new_payload(self.ip, self.port, ciphered_shared_key)

            # Create the custom control packet
            pkt = pm.new_control_packet(destID, "create", payload)

            # send first half of key exchange
            client_socket.sendall(pkt.encode())

            # Obtain a response packet
            rec_bytes = client_socket.recv(BUFFER_SIZE)
            message = json.loads(rec_bytes.decode())

            if message == -1 or message['command'] != 'created':
                raise OnionRuntimeError(
                    "ERROR    Did not receive expected confirmation packet\n"
                )
                print("         Circuit building exiting. . .")

            # received "created" packet successfully -- store info in tables
            # TODO check return value. right now created packets are filled with junk
            self.sender_key_table.add_key_entry(destID, 0, k)

            # store connection to first circID, the entry point to the circuit
            self.circuit_table.add_circuit_entry(
                nodes[0]['ip'],
                nodes[0]['port'],
                destID)

            # --- DONE WITH FIRST NODE

            # --- For all the other nodes:
            for i in range(1, len(nodes)):
                k = enc.generate_fernet_key()
                ciphered_shared_key = enc.encrypt_RSA(
                    k,
                    nodes[i]['public_exp'],
                    nodes[i]['modulus'])

                # data to be placed in "extend" packet payload. nodes will use circIDs to navigate,
                # until a node has decrypted the payload and finds the ip and port of the new node
                encrypted_data = pm.new_relay_payload(
                    nodes[i]['ip'],
                    nodes[i]['port'],
                    ciphered_shared_key)

                # apply layers of encryption on shared key + key exchange before sending it
                # e.g. for node 2, apply layer 1 then layer 0
                encryption_layer = i-1
                while(encryption_layer >= 0):
                    layer = self.sender_key_table.get_key(destID, encryption_layer)
                    encrypted_data = enc.encrypt_fernet(encrypted_data, layer)
                    encryption_layer -= 1

                pkt = pm.new_relay_packet(destID, "extend", encrypted_data)

                # send first half of key exchange
                client_socket.sendall(pkt.encode())

                rec_bytes = client_socket.recv(BUFFER_SIZE)
                message = json.loads(rec_bytes.decode())

                if message == -1 or (message['command'] != 'created' and message['command'] != 'extended'):
                    raise OnionRuntimeError(
                        "ERROR    Did not receive expected confirmation packet\n"
                    )
                    print("         Circuit building exiting. . .")

                # received "created" or "extended packet successfully -- store info in tables
                # TODO check return value. right now created packets are filled with junk
                self.sender_key_table.add_key_entry(destID, i, k)

                # store connection to first circID, the entry point to the circuit
                if (i == 0):
                    self.circuit_table.add_circuit_entry(nodes[0]['ip'], nodes[0]['port'], destID)

        # remove encryption layers (from node 0 to node 2)
        layer = self.sender_key_table.get_key(self.entry_circID, 0)
        payload = enc.decrypt_fernet(message['encrypted_data'], layer)
        for i in range(1, self.number_of_nodes):
            layer = self.sender_key_table.get_key(self.entry_circID, i)
            payload = enc.decrypt_fernet(payload, layer)
        self._close()

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
        self._create(ip, int(port))
        # apply three encryption layers to message
        # TODO put ip, port of website here if we don't want to do dns request on the exit node side
        encrypted_data = pm.new_payload(0, 0, message)

        for i in range(self.number_of_nodes - 1, -1, -1):
            layer = self.sender_key_table.get_key(self.entry_circID, i)
            encrypted_data = enc.encrypt_fernet(encrypted_data, layer)

        pkt = pm.new_relay_packet(self.entry_circID, "relay_data", encrypted_data)
        self._send(pkt)
        return self.receive_from_circuit(self.client_socket)

    def receive_from_circuit(self, client_socket):
        rec_bytes = client_socket.recv(BUFFER_SIZE)
        #message_str = rec_bytes.decode('utf-8')
        message = json.loads(rec_bytes.decode("UTF-8"))

        layer = self.sender_key_table.get_key(self.entry_circID, 0)
        payload = enc.decrypt_fernet(message['encrypted_data'], layer)
        for i in range(1, self.number_of_nodes):
            layer = self.sender_key_table.get_key(self.entry_circID, i)
            payload = enc.decrypt_fernet(payload, layer)
        payload = base64.urlsafe_b64decode(payload['data']).decode("UTF-8")
        return payload
