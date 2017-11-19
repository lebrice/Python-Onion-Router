#!/usr/bin/python3

import collections
import sys
import socket
import threading
import json
import time
import types

from socket import SocketType
from typing import List, Dict

from encryption import *
from messaging import IpInfo
import circuit_tables as ct
from relaying import IntermediateRelay
from workers import *
import RSA
import node_switchboard as ns
import packet_manager as pm

DIRECTORY_IP = "127.0.0.1"
DIRECTORY_PORT = "12345"

DEFAULT_TIMEOUT = 1  # timeout value for all blocking socket operations.


class OnionNode(threading.Thread):
    """A Node in the onion-routing network"""

    def __init__(self, name, receiving_port):
        super().__init__()
        self._name = name
        self.ip_address = socket.gethostname()
        self.receiving_port = receiving_port

        self.network_list = {}

        # Create a public key, private key and modulus for key exchange
        self.rsa_keys = RSA.get_private_key_rsa()

        self.circuit_table = ct.circuit_table()
        self.node_key_table = ct.node_key_table()
        self.node_relay_table = ct.node_relay_table()

        self._running_lock = Lock()
        self._running_flag = False
        self.initialized = False

    def run(self):
        """
        Starts the node, initializing all the required connections
        with the onion routing network
        """
        self.running = True
        self.contact_dir_node()
        self.initialized = True

        with socket.socket() as receiving_socket:
            receiving_socket.settimeout(DEFAULT_TIMEOUT)
            receiving_socket.bind((self.ip_address, self.receiving_port))
            receiving_socket.listen()
            while self.running:
                # Wait for the next message to arrive.
                try:
                    client_socket, address = receiving_socket.accept()
                    client_thread = ns.NodeSwitchboard(client_socket, address,
                                                       self.circuit_table,
                                                       self.node_key_table,
                                                       self.node_relay_table,
                                                       self.rsa_keys)
                    client_thread.start()
                except socket.timeout:
                    continue

    def contact_dir_node(self):
        """
            make the node known to the directory node
            contact directory node with a dir_query packet
            give info:
                ip, port (known through socket)
                public rsa keys of this node
            dir node answers with a list of all nodes in onion network

        """

        pkt = pm.new_dir_packet("dir_query", 0, self.rsa_keys)
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

    @property
    def running(self):
        """ returns if the node is currently running """
        with self._running_lock:
            return self._running_flag

    @running.setter
    def running(self, value):
        with self._running_lock:
            self._running_flag = value

    def stop(self):
        """ tells the node to shutdown. """
        self.running = False
        #self.join()

    # def relay_forward_in_chain(self):
    #     """returns a function that modifies messages before they are sent
    #     forward in the chain.
    #     """
    #     def handle(message):
    #         # TODO: this should be where we modify, encrypt, decrypt, etc.
    #         return message
    #     return handle
    #
    # def relay_backward_in_chain(self):
    #     """returns a function that modifies messages before they are sent
    #     backward in the chain.
    #     """
    #     def handle(message):
    #         # TODO: this should be where we modify, encrypt, decrypt, etc.
    #         return message
    #     return handle

    # def get_neighbouring_nodes_addresses(self) -> List[IpInfo]:
    #     with socket.socket() as _socket:
    #         _socket.settimeout(DEFAULT_TIMEOUT)
    #         _socket.connect((DIRECTORY_IP, DIRECTORY_PORT))
    #
    #         message = OnionMessage(
    #             header="GET_NEIGHBOURS",
    #             destination=DIRECTORY_IP
    #         )
    #
    #         # print("OnionNode is writing a message:", message)
    #         _socket.sendall(message.to_bytes())
    #         response_bytes = _socket.recv(1024)
    #
    #         response_str = str(response_bytes, encoding="utf-8")
    #         response = OnionMessage.from_json_string(response_str)
    #
    #         neighbours = convert_to_ip_info(response.data)
    #         # print(f"OnionNode received list of neighbours back: {neighbours}")
    #         return neighbours

    def _create(self, ip, port):
        self.client_socket = socket.socket(DEFAULT_TIMEOUT)
        self.client_socket.connect((ip, port))

    def _send(self, message_str):
        message_bytes = message_str.encode('utf-8')
        self.client_socket.sendall(message_bytes)

    def _close(self):
        self.client_socket.close()

# def convert_to_ip_info(list_of_lists):
#     """ Helper method that converts a list of lists into a list of tuples. """
#     tuples = []
#     for ip, port in list_of_lists:
#         tuples.append(IpInfo(ip, port))
#     return tuples


class DirectoryNode(Thread):
    """
        Contains information on all nodes
        each node has the following information:
            - ip address : receiving port
            - public rsa key pair (e, n) = (public exp, modulus) to be used for key exchange

        the directory node can do the following:
            - answer:  sends the network_info.json file to client
            - update:   updates the client's information
    """

    def __init__(self, receiving_port=12345):
        super().__init__()
        self._host = socket.gethostname()
        self._receiving_port = receiving_port
        self.ip_info = IpInfo(self._host, self._receiving_port)
        self._running_flag = False
        self._running_lock = Lock()

    def create_json(self):
        # create the network file, add directory node's info to it
        f = open('network_list.json', 'x')
        new = {'nodes in network': [{
            'ip': DIRECTORY_IP,
            'port': DIRECTORY_PORT,
            'public_exp': 0,
            'modulus': 0
        }]}
        json.dump(new, f)
        f.close()

    def write_to_json(self, ip, port, public_exp, modulus):
        # add new node
        try:
            f = open('network_list.json', 'r')
            data = json.load(f)

            # if a node is already in the list, then it is trying to update its RSA info
            updated = 0
            for n in data['nodes in network']:
                if n['ip'] == ip and n['port'] == port:
                    n['public_exp'] = public_exp
                    n['modulus'] = modulus
                    updated = 1

            # node is new: add it to network file
            if updated == 0:
                new_entry = {
                    'ip': ip,
                    'port': port,
                    'public_exp': public_exp,
                    'modulus': modulus
                }
                data['nodes in network'].append(new_entry)

            with open('test.json', 'w') as f:
                json.dump(data, f)
                f.close()

            return updated
        except FileNotFoundError:
            print("ERROR    network_list.json does not exist. Use create_json to create it\n")
            return

    def return_json(self):
        try:
            f = open('network_list.json', 'r')
            data = json.load(f)
            f.close()
            return data
        except FileNotFoundError:
            print("ERROR    network_list.json does not exist. Use create_json to create it\n")
            return

    def run(self):
        self.running = True
        self.create_json()

        with socket.socket() as recv_socket:
            recv_socket.settimeout(DEFAULT_TIMEOUT)
            recv_socket.bind((self._host, self._receiving_port))
            recv_socket.listen()
            while self.running:
                try:
                    client_socket, client_address = recv_socket.accept()
                    with client_socket:  # Closes it automatically.
                        client_socket.settimeout(DEFAULT_TIMEOUT)
                        rec_bytes = client_socket.recv(1024)
                        message = json.load(rec_bytes.decode())

                        if message['type'] != "dir":
                            # invalid message, ignore
                            client_socket.close()
                            continue

                        ip, port = client_address.split(':')
                        updated = self.write_to_json(ip, port, message['public_exp'], message['modulus'])

                        pkt = pm.new_dir_packet("dir_answer", updated, self.return_json)
                        message_bytes = pkt.encode('utf-8')
                        client_socket.connect((ip, port))
                        client_socket.sendall(message_bytes)
                        client_socket.close()

                except socket.timeout:
                    continue  # Try again.

    @property
    def running(self):
        """ returns if the node is currently running """
        with self._running_lock:
            return self._running_flag

    @running.setter
    def running(self, value):
        with self._running_lock:
            self._running_flag = value

    def stop(self):
        """ tells the node to shutdown. """
        self.running = False
        #self.join()
