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

import circuit_tables as ct
import encryption as enc

BUFFER_SIZE = 1024 # Constant for now
DEFAULT_TIMEOUT = 1

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

    def send(self, data):
        """
            called from exterior to tell client to send message through the circuit
        """
        if not self.initialized:
            print("ERROR     Client not initialized. Call .connect() first.\n")
            return

        print("You tried to send a message\n")


    def recv(self, buffer_size):
        """ Receives the given number of bytes from the Onion socket.
        """
        raise NotImplementedError()

    def _contact_dir_node(self, dir_ip, dir_port):
        """
            query dir node for network list, without including the client in the list of nodes
            this avoids the problem of the client using itself as a node later on

        """

        pkt = pm.new_dir_packet("dir_query", 0, 0)
        self._create(dir_ip, dir_port)
        self._send(pkt)
        #message = self._receive()

        # wait for a response packet; 3 tries
        tries = 3
        message = -1
        while tries != 0:
            try:
                rec_bytes = self.client_socket.recv(BUFFER_SIZE)
                message = json.loads(rec_bytes.decode())
                break
            except socket.timeout:
                tries -= 1
                if tries == 0:
                    print("ERROR    Timeout while waiting for confirmation packet [3 tries]\n")
                    print("         Directory connection exiting. . .")
                    self._close()
                    return
                continue

        if message == -1 or message['type'] != "dir":
            print("ERROR    Unexpected answer from directory\n")
            # invalid message, ignore
            self._close()
            return

        self.network_list = message['table']
        print("contacting dir")
        self._close()


    def _select_random_nodes(self):
        if len(self.network_list['nodes in network']) < self.number_of_nodes:
            print("ERROR    There are not enough nodes to build the circuit. Current: ",
                  len(self.network_list), "requested", self.number_of_nodes)
            return -1

        return random.sample(self.network_list['nodes in network'], self.number_of_nodes)


    def _generate_new_circID(self):
        # define a limit to how many circuits the node can be part of
        max_circuit_no = 100

        if self.circuit_table.get_length() == max_circuit_no:
            print("ERROR    Too many active circuits; could not create circuit. Current max is ", max_circuit_no)
            print("         Try deleting a circuit before creating a new one")
            return

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
        self._create(nodes[0]['ip'], nodes[0]['port'])

        for i in range(0, len(nodes)):
            k = enc.generate_fernet_key()
            ciphered_shared_key = enc.encrypt_RSA(k, nodes[i]['public_exp'], nodes[i]['modulus'])

            if i == 0:
                # first link is special: only one to get control "create" packet
                destID = self._generate_new_circID()
                self.circuit_table.add_circuit_entry(nodes[0]['ip'], nodes[0]['port'], destID)
                self.sender_key_table.add_key_entry(destID, i, k)
                pkt = pm.new_control_packet(destID, "create", ciphered_shared_key)
            else:
                self._create(nodes[0]['ip'], nodes[0]['port'])
                # data to be placed in "extend" packet payload. nodes will use circIDs to navigate,
                # until a node has decrypted the payload and finds the ip and port of the new node
                encrypted_data = pm.new_relay_payload(nodes[i]['ip'], nodes[i]['port'], ciphered_shared_key)

                # apply layers of encryption on shared key + key exchange before sending it
                # e.g. for node 2, apply layer 1 then layer 0
                for j in range(i - 1, -1, -1):
                    layer = self.sender_key_table.get_key(destID, j)
                    encrypted_data = enc.encrypt_fernet(encrypted_data, layer)

                pkt = pm.new_relay_packet(destID, "extend", encrypted_data)

            # send first half of key exchange
            print("sending packet {}".format(i))
            self._send(pkt)

            # wait for a response packet; 30 tries
            tries = 30
            message = -1
            while tries != 0:
                try:
                    rec_bytes = self.client_socket.recv(BUFFER_SIZE)
                    print(rec_bytes)
                    message = json.loads(rec_bytes.decode())
                    break
                except socket.timeout:
                    tries -= 1
                    print(tries)
                    if tries == 0:
                        print("ERROR    Timeout while waiting for confirmation packet [30 tries]\n")
                        print("         Directory connection exiting. . .")
                        self._close()
                        return
                    continue

            if message == -1 or (message['command'] != 'created' and message['command'] != 'extended'):
                print("ERROR    Did not receive expected confirmation packet\n")
                print("         Circuit building exiting. . .")
                # invalid message, ignore
                self._close()
                return

            # received "created" or "extended packet successfully -- store info in tables
            # TODO check return value. right now created packets are filled with junk
            self.sender_key_table.add_key_entry(destID, i, k)

            # store connection to first circID, the entry point to the circuit
            if (i == 0):
                self.circuit_table.add_circuit_entry(nodes[0]['ip'], nodes[0]['port'], destID)

        print("Built circuit successfully")
        self._close()


    def _create(self, ip, port):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((ip, port))

    def _send(self, message_str):
        message_bytes = message_str.encode('utf-8')
        print("client {}".format(message_bytes))
        self.client_socket.sendall(message_bytes)
        print("sent")

    def _close(self):
        print("closing socket")
        self.client_socket.close()