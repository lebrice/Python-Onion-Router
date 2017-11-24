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

from messaging import IpInfo
import circuit_tables as ct
import errors
from relaying import IntermediateRelay
from workers import *
import encryption as enc
import node_switchboard as ns
import packet_manager as pm

DEFAULT_TIMEOUT = 1  # timeout value for all blocking socket operations.

DIRECTORY_NODE_IP = socket.gethostname()
DIRECTORY_NODE_PORT = 12345

DEFAULT_NODE_IP = socket.gethostname()
DEFAULT_NODE_PORT = 12345

class OnionNode(threading.Thread):
    """A Node in the onion-routing network"""

    def __init__(
        self,
        ip=DEFAULT_NODE_IP,
        port=DEFAULT_NODE_PORT,
        directory_node_ip=DIRECTORY_NODE_IP,
        directory_node_port=DIRECTORY_NODE_PORT
    ):
        super().__init__()
        self.ip = ip
        self.port = port
        self.directory_node_ip = directory_node_ip
        self.directory_node_port = directory_node_port

        self.network_list = {}

        # Create a public key, private key and modulus for key exchange
        self.rsa_keys = enc.get_private_key_rsa()

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

        if not self.initialized:
            raise errors.OnionRuntimeError(
                "ERROR    Node not initialized. Call node.connect() first"
            )

        with socket.socket() as receiving_socket:
            receiving_socket.settimeout(DEFAULT_TIMEOUT)
            receiving_socket.bind((self.ip, self.port))
            receiving_socket.listen()
            while self.running:
                # Wait for the next message to arrive.
                try:
                    client_socket, address = receiving_socket.accept()
                    client_thread = ns.NodeSwitchboard(
                        client_socket,
                        address,
                        self.circuit_table,
                        self.node_key_table,
                        self.node_relay_table,
                        self.rsa_keys,
                        self.ip,
                        self.port
                    )
                    client_thread.start()
                except socket.timeout:
                    continue

        self.shutdown()

    def start(self):
        """
        Start the OnionNode

        NOTE: from threading.Thread
        """
        self._get_nodes_in_network()
        super().start()
        self.initialized = True

    def stop(self):
        """
        tells the node to shut itself down.
        TODO: contact directory node to let it know we're shutting down.
        """
        self.running = False
        #self.join()

    def connect(self, dir_ip, dir_port):
        """
        NOTE: Deprecated. Already taken care of in the 'start()' method.
        """
        print("WARNING: the 'connect' method is deprecated.")

    @contextmanager
    def _connect_to_directory_node(self):
        """
        attempts to connect to the directory node, and returns the resulting
        socket.
        NOTE: to be used in a statement like:
        "with _connect_to_directory_node() as X:"
        """
        _socket = socket.socket()
        try:
            _socket.connect(
                (self.directory_node_ip, self.directory_node_port)
            )
        except ConnectionRefusedError as e:
            raise errors.OnionNetworkError(
                "Unable to connect with Directory Node at Address:",
                (self.directory_node_ip, self.directory_node_port)
            )
        else:
            yield _socket
        finally:
            _socket.close()

    def _get_nodes_in_network(self):
        """
            make the node known to the directory node
            contact directory node with a dir_update packet
            give info:
                ip, port (known through socket)
                public rsa keys of this node
            dir node answers with a list of all nodes in onion network
        """
        pkt = pm.new_dir_packet(
            "dir_update",
            (self.ip, self.port),
            self.rsa_keys
        )

        with self._connect_to_directory_node() as client_socket:
            client_socket.sendall(pkt.encode())
            received_bytes = client_socket.recv(BUFFER_SIZE)
            message = json.loads(rec_bytes.decode())

            if message['type'] != "dir":
                raise errors.OnionRuntimeError(
                    "ERROR: Unexpected answer from directory"
                )
            self.network_list = message['table']


class DirectoryNode(Thread):
    """
        Contains information on all nodes
        each node has the following information:
            - ip address : receiving port
            - public rsa key pair (e, n) = (public exp, modulus) to be used
            for key exchange

        the directory node can do the following:
            - answer:  sends the network_info.json file to client
            - update:  updates the client's information
    """

    def __init__(self, ip=DIRECTORY_NODE_IP, port=DIRECTORY_NODE_PORT):
        super().__init__()
        self.ip = ip
        self.port = port
        self._running_flag = False
        self._running_lock = Lock()

        self.create_json()

    def create_json(self):
        # create the network file if it doesn't exist,
        try:
            f = open('network_list.json', 'x')
        except FileExistsError:
            f = open('network_list.json', 'w')
            f.seek(0)

        new = {'nodes in network': []}
        json.dump(new, f)
        f.close()

    def write_to_json(self, ip, port, public_exp, modulus):
        try:
            with open('network_list.json', 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            print("ERROR    network_list.json does not exist. Use create_json to create it\n")
            return

        # if a node is already in the list, then it is trying to update its RSA info
        updated = 0
        test = len(data['nodes in network'])

        if len(data['nodes in network']) > 0:
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
            updated = 1

        with open('network_list.json', 'w') as f:
            f.seek(0)
            json.dump(data, f, indent=4)

        return updated

    def return_json(self):
        try:
            with open('network_list.json', 'r') as f:
                data = json.load(f)
            return data
        except FileNotFoundError:
            print("ERROR    network_list.json does not exist. Use create_json to create it\n")
            return

    def run(self):
        self.running = True

        with socket.socket() as recv_socket:
            recv_socket.settimeout(DEFAULT_TIMEOUT)
            recv_socket.bind((self.ip, self.port))
            recv_socket.listen()
            while self.running:
                try:
                    client_socket, client_address = recv_socket.accept()
                    with client_socket:  # Closes it automatically.
                        client_socket.settimeout(DEFAULT_TIMEOUT)
                        rec_bytes = client_socket.recv(1024)
                        message = json.loads(rec_bytes.decode())

                        if message['type'] != "dir":
                            # invalid message, ignore
                            client_socket.close()
                            continue

                        updated = 0
                        if message['command'] == "dir_update":
                            updated = self.write_to_json(message['ip'], message['port'], message['public_exp'], message['modulus'])

                        pkt = pm.new_dir_packet("dir_answer", updated, self.return_json())
                        message_bytes = pkt.encode('utf-8')
                        #client_socket.connect((ip, port))
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
