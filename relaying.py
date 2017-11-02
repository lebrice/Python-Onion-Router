#!usr/bin/python3
"""
This module defines the Workers/Threads that are used to handle relaying
messages from one socket to another.
"""

from threading import Thread


class IntermediateRelay(Thread):
    """
    Relays messages from one Node to another.

    Params:
        - previous_socket: Socket connected to the previous node.
        - next_socket: Socket connected to the next node.


    Whenever either socket is closed, the relayer 
        - One of the sockets is closed

    TODO: Would it be a good idea to use a field in a message, to indicate if
    the connection is to be held open, or closed ?
    (analogous to TCP's 'connection' field?)
    """

    def __init__(self, previous_socket, next_socket):
        """ Initializes the relay.

        """
        super().__init__()
        self.previous_s = previous_socket
        self.next_s = next_socket

    def run(self):
        """ Begin relaying messages from one socket to another.
        """
        # Listen for messages from prev
        # copy the messages to the next socket

        # OR

        #listen for messages from the next socket
        # copy the messages to the prev socket.

