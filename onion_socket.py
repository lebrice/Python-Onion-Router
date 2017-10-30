#!/usr/bin/python3
""" Module that defines the OnionSocket, used by the user. """


class OnionSocket():
    def __init__(self):
        """ TODO: Create the OnionSocket."""

    @staticmethod
    def socket():
        """ Creates a new OnionSocket.

        (Made to imitate *socket.socket()* method.)
        """
        raise NotImplementedError()

    def connect(self, target_ip_info):
        """ Connects to the given remote host, through the onion network.
        """
        target_ip, target_port = target_ip_info
        # NOTE: This might be a good place to build/initialize the circuit?
        raise NotImplementedError()

    def send(data: bytes):
        """ Sends the given data to the remote host through the OnionSocket.
        """
        raise NotImplementedError()

    def recv(self, buffer_size):
        """ Receives the given number of bytes from the Onion socket. """
        raise NotImplementedError()
