#!/usr/bin/python3

import sys
import socket
import threading

from encryption import *
from workers import *
from queues import *

MOM_IP = socket.gethostname()
MOM_RECEIVING_PORT = 12345

class Node(threading.Thread, SimpleAdditionEncriptor):
    """A Node in the onion-routing network"""
    def __init__(self, name, receiving_port, private_key):
        self._name = name
        self._ip_address = socket.gethostname()
        self._receiving_port = receiving_port
        self._private_key = private_key

        self.neighbours = []
        self.shared_keys = []

        self._running_lock = Lock()
        self._running_flag = False

        self._socket_reader: SocketReader = None

        super().__init__()

    def run(self):
        """
        Starts the node, initializing all the required connections
        with the onion routing network
        """
        self._running_flag = True

        self.contact_directory_node()
        neighbours = self.get_neighbouring_nodes_addresses()

        for neighbour in neighbours:
            shared_key = self.perform_key_exchange_with(neighbour)
            self.shared_keys.append(shared_key)

        self._socket_reader = SocketReader(self._receiving_port)

        while self.is_running():
            message = self._socket_reader.next()  # Wait for the next message to arrive.
            self.process_message(message)

    def is_running(self):
        """ returns if the node is currently running """
        with self._running_lock:
            return self._running_flag
    
    def stop(self):
        """ tells the node to shutdown. """
        with self._running_lock:
            self._running_flag = False
        self._socket_reader.stop()

    def process_message(self, message):
        """ 
        TODO: main application logic.
        - Figure out what to do with a message: is it supposed to be forwarded to another node ?
        """
        # if OnionMessage.is_meant_for_me(self, message):
        #     # Do something
        # else:
        #     # Forward the message along.
        pass

    def contact_directory_node(self):
        """
        TODO: Tell the directory node that we exist, exchange keys with it, then get some information from it.
        """
        with socket.socket() as mom_socket:
            mom_socket.connect((MOM_IP, MOM_RECEIVING_PORT))
            # TODO:
            mom_socket.send("Hey! I'm alive.")
            
        
    def get_neighbouring_nodes_addresses(self):
        #TODO: Get a list of all neighbouring nodes.
        neighbours = [
            ("mom", "127.0.0.1", "12345"),
            ("bob", "127.0.0.1", "12346"),
            ("alice", "127.0.0.1", "12347"),
            ("john", "127.0.0.1", "12348")
        ]
        return neighbours
