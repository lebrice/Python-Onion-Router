#!/usr/bin/python3

import sys
import socket
import threading

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
        self.shared_keys = []

        self._running_lock = Lock()
        self._running_flag = False

    def run(self):
        """
        Starts the node, initializing all the required connections
        with the onion routing network
        """
        self._running_flag = True
        with read_socket(self._receiving_port) as socket_reader:
            while self.is_running():
                # Wait for the next message to arrive.
                message = socket_reader.next()
                self.process_message(message)

    def _initialize(self):
        """Initializes the node.

        Calls the directory node and performs key exchanges
        TODO: Implement this for real. This is just pseudocode
        """
        self.contact_directory_node()
        neighbours = self.get_neighbouring_nodes_addresses()

        for neighbour in neighbours:
            shared_key = self.perform_key_exchange_with(neighbour)
            self.shared_keys.append(shared_key)

    def is_running(self):
        """ returns if the node is currently running """
        with self._running_lock:
            return self._running_flag

    def stop(self):
        """ tells the node to shutdown. """
        with self._running_lock:
            self._running_flag = False
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
        pass

    def contact_directory_node(self):
        """TODO: Tell the directory node that we exist, exchange keys with it,
        then get some information from it.
        """
        with write_to_socket(MOM_IP, MOM_RECEIVING_PORT) as writer:
            # TODO:
            message = "Hey! I'm alive!"
            print("OnionNode is writing a message:", message)
            writer.write(message)

    def get_neighbouring_nodes_addresses(self):
        # TODO: Get a list of all neighbouring nodes.
        # neighbours = [
        #     ("mom", "127.0.0.1", "12345"),
        #     ("bob", "127.0.0.1", "12346"),
        #     ("alice", "127.0.0.1", "12347"),
        #     ("john", "127.0.0.1", "12348")
        # ]
        return []


class DirectoryNode(Thread, SimpleAdditionEncriptor):
    """ Central node, coordinates the onion network.
    TODO: implement this.
    """

    def __init__(self, receiving_port=12345):
        self._receiving_port = 12345
        self._running = False
        super().__init__()

    def run(self):
        self._running = True
        with read_socket(MOM_RECEIVING_PORT) as socket_reader:
            while self._running:
                print("Directory Node is running.")
                message = socket_reader.out.get()
                print("Directory node received message:", message)
                # # TODO: Implement something like this.
                # if(is_key_exchange(message)):
                #     self.key_exchange_receiver.handle(client_socket, address, message)
                # client_socket.send("Hey,thanks for connecting.".encode())

    def stop(self):
        """ tells the node to shutdown. """
        self._running = False
        self.join()
