#!/usr/bin/python3

import sys
import socket
import collections

from encryption import *


class Node(Encriptor):
    """A Node in the onion-routing network"""
    def __init__(self, name, ip_address, receiving_port):
        self._name = name
        self._ip_address = ip_address
        self._receiving_port = receiving_port
        self._started = False

    @property
    def ip_address(self):
        return self._ip_address

    @ip_address.setter
    def ip_address(self, ip_address):
        if hasattr(self, "_ip_address") and self._started:
            raise AttributeError("IP cannot be changed after node is started.")
        self._ip_address = ip_address

    def start(self):
        """
        Starts the node, initializing all the required connections
        with the onion routing network
        """
        if(self._started):
            return  # Node has already been started.
        self._receiving_socket = socket.socket()
        self._receiving_socket.bind((self._ip_address, self._receiving_port))
        self._receiving_socket.listen(5)
        self._started = True

    def stop(self):
        """
        Stops the node, closing all communications with the onion routing
        network.
        """
        if(not self._started):
            return  # Node has already been stopped or hasn't started yet.
        self._receiving_socket.close()
        self._started = False

    def say_hello(self):
        message = f"hey! my name is {self._name}"
        print(message)
        print(self.encrypt(message, 123))


def main():
    bob = Node("Bob", "127.0.0.1", 12345)
    bob.say_hello()
    bob.start()
    bob.stop()

if __name__ == '__main__':
    main()
