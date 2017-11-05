#!/usr/bin/python3

import collections
import sys
import socket
import threading
import time
import types

from socket import SocketType
from typing import List, Dict

from encryption import *
from messaging import IpInfo
from relaying import IntermediateRelay
from workers import *

MOM_IP = socket.gethostname()
MOM_RECEIVING_PORT = 12345

DEFAULT_TIMEOUT = 1  # timeout value for all blocking socket operations.


class OnionNode(threading.Thread, SimpleAdditionEncriptor):
    """A Node in the onion-routing network"""

    def __init__(self, name, receiving_port, private_key):
        super().__init__()
        self._name = name
        self._ip_address = socket.gethostname()
        self._receiving_port = receiving_port
        self._private_key = private_key

        self.neighbours: List[IpInfo] = []
        self.public_keys = {}
        self.shared_secrets = {}

        self._running_lock = Lock()
        self._running_flag = False
        self.initialized = False

    def run(self):
        """
        Starts the node, initializing all the required connections
        with the onion routing network
        """
        self.running = True
        with socket.socket() as receiving_socket:
            receiving_socket.settimeout(DEFAULT_TIMEOUT)
            receiving_socket.bind((self._ip_address, self._receiving_port))
            receiving_socket.listen()
            while self.running:
                # Wait for the next message to arrive.
                try:
                    client_socket, address = receiving_socket.accept()
                    self.process_message(client_socket, message)
                    client_socket.close()
                except socket.timeout:
                    continue

    def _initialize(self):
        """Initializes the node.

        Calls the directory node and performs key exchanges
        TODO: Implement this for real. This is just pseudocode
        """
        self.contact_directory_node()
        self.neighbours = self.get_neighbouring_nodes_addresses()

        for neighbour in self.neighbours:
            public_key, shared_key = self.perform_key_exchange_with(neighbour)
            self.public_keys[neighbour] = public_key
            self.shared_secrets[neighbour] = shared_key

        self.initialized = True

    @property
    def running(self):
        """ returns if the node is currently running """
        with self._running_lock:
            return self._running_flag

    @running.setter
    def running(self, value):
        with self._running_lock:
            self._running_flag = value

    def start(self):
        self._initialize()
        super().start()

    def stop(self):
        """ tells the node to shutdown. """
        self.running = False
        self.join()

    def process_message(self, _socket: SocketType, message: OnionMessage):
        """
        TODO: main application logic.
        - Figure out what to do with a message: is it supposed to be forwarded
        to another node ?
        """
        if message.header == "RELAY":
            # NOTE: This might not be exactly how we get the destination.
            # Nevertheless, this serves as an example of what we can do with
            # the IntermediateRelay class from relaying.py.
            new_socket = socket.create_connection(message.destination)
            relay = IntermediateRelay(
                _socket,
                new_socket,
                self.relay_forward_in_chain(),
                self.relay_backward_in_chain()
            )
            relay.start()
        # TODO: fill in the other cases.

    def relay_forward_in_chain(self):
        """returns a function that modifies messages before they are sent
        forward in the chain.
        """
        def handle(message):
            # TODO: this should be where we modify, encrypt, decrypt, etc.
            return message
        return handle

    def relay_backward_in_chain(self):
        """returns a function that modifies messages before they are sent
        backward in the chain.
        """
        def handle(message):
            # TODO: this should be where we modify, encrypt, decrypt, etc.
            return message
        return handle

    def perform_key_exchange_with(self, neighbour: IpInfo):
        """Perform a DH key-exchange with the given neighbour and return the shared key
        TODO: Implement this.
        """
        return (31, 123)  # Some random values, for the moment.
        pass

    def contact_directory_node(self):
        """TODO: Tell the directory node that we exist, exchange keys with it,
        then get some information from it.
        """

    def get_neighbouring_nodes_addresses(self) -> List[IpInfo]:
        # TODO: Get a list of all neighbouring nodes.
        with socket.socket() as _socket:
            _socket.settimeout(DEFAULT_TIMEOUT)
            _socket.connect((MOM_IP, MOM_RECEIVING_PORT))

            message = OnionMessage(
                header="GET_NEIGHBOURS",
                destination=MOM_IP
            )

            # print("OnionNode is writing a message:", message)
            _socket.sendall(message.to_bytes())
            response_bytes = _socket.recv(1024)

            response_str = str(response_bytes, encoding="utf-8")
            response = OnionMessage.from_json_string(response_str)

            neighbours = convert_to_tuples(response.data)
            # print(f"OnionNode received list of neighbours back: {neighbours}")
            return neighbours

    def send_message(self, message: OnionMessage):
        target_ip, target_port = message.destination
        with socket.socket() as _socket:
            _socket.connect((target_ip, target_port))
            _socket.sendall(message.to_bytes())


def convert_to_tuples(list_of_lists):
    """ Helper method that converts a list of lists into a list of tuples. """
    tuples = []
    for l in list_of_lists:
        tuples.append(tuple(l))
    return tuples


class DirectoryNode(Thread, SimpleAdditionEncriptor):
    """ Central node, coordinates the onion network.
    TODO: implement this.
    """

    def __init__(self, receiving_port=12345):
        super().__init__()
        self._host = socket.gethostname()
        self._receiving_port = receiving_port
        self.ip_info = IpInfo(self._host, self._receiving_port)
        self._running_flag = False
        self._running_lock = Lock()

        self.network_onion_nodes = []

    def run(self):
        self.running = True
        with socket.socket() as recv_socket:
            recv_socket.settimeout(DEFAULT_TIMEOUT)
            recv_socket.bind((self._host, self._receiving_port))
            recv_socket.listen()
            while self.running:
                # TODO: Implement this for real.
                # print("Directory Node is running.")
                try:
                    client_socket, client_address = recv_socket.accept()
                    with client_socket:  # Closes it automatically.
                        client_socket.settimeout(DEFAULT_TIMEOUT)
                        message_bytes = client_socket.recv(1024)
                        message_str = str(message_bytes, encoding='utf-8')
                        # print("Directory node received message:", message_str)

                        if not OnionMessage.is_valid_string(message_str):
                            # TODO: Figure out what to do in such a case.
                            client_socket.sendall("INVALID_STR".encode())
                            client_socket.close()
                            continue

                        message = OnionMessage.from_json_string(message_str)

                        if self.network_onion_nodes.count(client_address) == 0:
                            self.network_onion_nodes.append(client_address)

                        if(message.header == "GET_NEIGHBOURS"):
                            neighbours = self.network_onion_nodes.copy()
                            neighbours.remove(client_address)

                            response_message = OnionMessage(
                                source=(self._host, self._receiving_port),
                                header="WELCOME_TO_NETWORK",
                                destination=client_address,
                                data=neighbours
                            )
                            client_socket.sendall(response_message.to_bytes())
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
        self.join()
