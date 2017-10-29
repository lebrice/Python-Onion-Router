#!usr/bin/python3
""" Defines the external API for the OnionNode class.

TODO: Add the methods that make sense here, then make OnionNode a subclass,
and then implement the methods.
"""


class OnionNodeApi():
    @classmethod
    def new(cls, receiving_port):
        """Creates a new OnionNode, to be used to communicate
        via the onion routing network.
        """
        raise NotImplementedError()

    def connect(self, target_ip, target_port):
        """Connects to a remote host using the Onion Routing network."""
        raise NotImplementedError()

    def send(self, message):
        """Send the given message to the remote host using the Onion network.
        """
        raise NotImplementedError()

    def receive(self, byte_count):
        """Reads the given number of bytes from the OnionRouting 'socket'."""
        raise NotImplementedError()