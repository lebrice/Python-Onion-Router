#!/usr/bin/python3

import sys
import socket
import threading
import time

from queue import Empty
from encryption import *
from workers import *
from queues import *

MOM_IP = socket.gethostname()
MOM_RECEIVING_PORT = 12345


class OnionNode(threading.Thread, SimpleAdditionEncriptor):
    """A Node in the onion-routing network"""

    def __init__(self, name, receiving_port, private_key):
        super().__init__()
        self._name = name
        self._ip_address = socket.gethostname()
        self._receiving_port = receiving_port
        self._private_key = private_key

        self.neighbours = []
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
        with read_socket(self._receiving_port) as socket_reader:
            while self.running:
                # Wait for the next message to arrive.
                message = socket_reader.next()
                self.process_message(message)

    def _initialize(self):
        """Initializes the node.

        Calls the directory node and performs key exchanges
        TODO: Implement this for real. This is just pseudocode
        """
        self.contact_directory_node()
        self.neighbours = self.get_neighbouring_nodes_addresses()

        for neighbour in self.neighbours:
            neighbour_ip, neighbour_port = neighbour
            public_key, shared_key = self.perform_key_exchange_with(neighbour)
            self.public_keys[(neighbour_ip, neighbour_port)] = public_key
            self.shared_secrets[(neighbour_ip, neighbour_port)] = shared_key

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
        # self.join()

    def process_message(self, message):
        """
        TODO: main application logic.
        - Figure out what to do with a message: is it supposed to be forwarded
        to another node ?
        """
        # if OnionMessage.is_meant_for_me(self, message):
        #     # Do something
        # else:
        #     # Forward the message along.
        pass

    def perform_key_exchange_with(self, neighbour):
        """Perform a DH key-exchange with the given neighbour and return the shared key
        TODO: Implement this.
        """
        return (31, 123) # Some random values, for the moment.
        pass

    def contact_directory_node(self):
        """TODO: Tell the directory node that we exist, exchange keys with it,
        then get some information from it.
        """

    def get_neighbouring_nodes_addresses(self):
        # TODO: Get a list of all neighbouring nodes.
        with socket.socket() as _socket:
            _socket.connect((MOM_IP, MOM_RECEIVING_PORT))

            message = OnionMessage(
                header="GET_NEIGHBOURS",
                destination=MOM_IP
            )

            print("OnionNode is writing a message:", message)
            _socket.sendall(message.to_bytes())
            response_bytes = _socket.recv(1024)

            response_str = str(response_bytes, encoding="utf-8")
            response = OnionMessage.from_json_string(response_str)

            neighbours = response.data
            print(f"OnionNode received list of neighbours back: {neighbours}")
            return neighbours


class DirectoryNode(Thread, SimpleAdditionEncriptor):
    """ Central node, coordinates the onion network.
    TODO: implement this.
    """

    def __init__(self, receiving_port=12345):
        super().__init__()
        self._host = socket.gethostname()
        self._receiving_port = receiving_port
        self._running_flag = False
        self._running_lock = Lock()

        self.network_onion_nodes = []

    def run(self):
        self.running = True
        with socket.socket() as recv_socket:
            recv_socket.bind((self._host, self._receiving_port))
            recv_socket.listen(5)
            while self.running:
                # TODO: Implement this for real.
                print("Directory Node is running.")
                client_socket, client_address = recv_socket.accept()
                message_bytes = client_socket.recv(1024)
                message_str = str(message_bytes, encoding='utf-8')
                print("Directory node received message:", message_str)

                if not OnionMessage.is_valid_string(message_str):
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

                client_socket.close()



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
        # self.join()
