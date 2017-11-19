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
from relaying import IntermediateRelay
from workers import *
import encryption as enc
import node_switchboard as ns
import packet_manager as pm

DEFAULT_TIMEOUT = 1  # timeout value for all blocking socket operations.


class OnionNode(threading.Thread):
    """A Node in the onion-routing network"""

    def __init__(self, ip, port):
        super().__init__()
        self.ip = ip
        self.port = port

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

        if self.initialized:
            with socket.socket() as receiving_socket:
                receiving_socket.settimeout(DEFAULT_TIMEOUT)
                receiving_socket.bind((self.ip, self.port))
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
        else:
            print("ERROR    Node not initialized. Call node.connect() first")

    def connect(self, dir_ip, dir_port):
        self._contact_dir_node(dir_ip, dir_port)
        self.initialized = True

    def _contact_dir_node(self, dir_ip, dir_port):
        """
            make the node known to the directory node
            contact directory node with a dir_update packet
            give info:
                ip, port (known through socket)
                public rsa keys of this node
            dir node answers with a list of all nodes in onion network

        """

        pkt = pm.new_dir_packet("dir_update", (self.ip, self.port), self.rsa_keys)
        self._create(dir_ip, dir_port)
        self._send(pkt)

        # wait for a response packet; 3 tries
        tries = 3
        rec_bytes = 0
        while tries != 0:
            try:
                rec_bytes = self.client_socket.recv(BUFFER_SIZE)
                break
            except socket.timeout:
                tries -= 1
                if tries == 0:
                    print("ERROR    Timeout while waiting for confirmation packet [3 tries]\n")
                    print("         Directory connection exiting. . .")
                    self._close()
                    return
                continue

        message = json.loads(rec_bytes.decode())

        if message['type'] != "dir":
            print("ERROR    Unexpected answer from directory")
            self._close()
            return

        self.network_list = message['table']
        self._close()

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


    def _create(self, ip, port):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
            - update:  updates the client's information
    """

    def __init__(self, ip, port):
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
