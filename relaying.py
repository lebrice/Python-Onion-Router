#!usr/bin/python3
"""
This module defines the Workers/Threads that are used to handle relaying
messages from one socket to another.
"""
import json
import socket
from socket import SocketType
from threading import Thread
from typing import List

from messaging import OnionMessage
import workers
from workers import SocketReader

BUFFER_SIZE = 4096


class IntermediateRelay(Thread):
    """
    Relays messages from one Node to another.

    Params:
        - left_socket: Socket connected to the previous node.
        - right_socket: Socket connected to the next node.
        - left_to_right: function to be applied for each item taken from
        left_socket before putting it on right_socket.
        - right_to_left: function to be applied for each item taken from
        right_socket before putting it on left_socket.abs

        NOTE: the functions given should be function(JSON) -> JSON (or
        OnionMessage, for that matter.)

    TODO: Would it be a good idea to use a field in a message, to indicate if
    the connection is to be held open, or closed ?
    (analogous to TCP's 'connection' field?)
    """

    def __init__(self,
                left_socket: SocketType,
                right_socket: SocketType,
                left_to_right=None,
                right_to_left=None
                ):
        """ Initializes the relay. """
        super().__init__()
        self.left_socket = left_socket
        self.right_socket = right_socket
        self.left_to_right = left_to_right
        self.right_to_left = right_to_left
        self.left_reader: SocketReader = None
        self.right_reader: SocketReader = None

    def run(self):
        """ Begin relaying messages from one socket to another.
        idea:
            - Listen for messages from prev
            - copy the messages to the next socket

            AND
            
            - Listen for messages from next socket
            - copy the messages to the prev socket

            until either of them closes its socket.
        """
        left_buffer = []  # messages received from the prev_socket.
        right_buffer = []  # messages received from the next_socket.

        self.left_reader = SocketReader(self.left_socket, left_buffer)
        self.right_reader = SocketReader(self.right_socket, right_buffer)

        self.left_reader.start()
        self.right_reader.start()

        while (not self.left_reader.closed) and (not self.right_reader.closed):
            # send to next node
            for message in left_buffer:
                if self.left_to_right:
                    # If we were given a function to execute
                    message = self.left_to_right(message)
                self._send(message, self.right_socket)
                left_buffer.remove(message)

            # send to prev node
            for message in right_buffer:
                if self.right_to_left:
                    # If we were given a function to execute
                    message = self.right_to_left(message)
                self._send(message, self.left_socket)
                right_buffer.remove(message)

        # One of the two closed.

        # IMPORTANT: whenever one of the nodes closes its socket, we assume
        # that whatever message may come after that point can be dumped.

        if self.left_reader.closed:
            # Prev is done sending messages. Send the the rest of its messages
            # over to next, then close next.
            for message in left_buffer:
                if self.left_to_right:
                    # If we were given a function to execute
                    message = self.left_to_right(message)
                self._send(message, self.right_socket)
                left_buffer.remove(message)
            self.right_socket.close()

        elif self.right_reader.closed:
            # Prev is done sending messages. Send the the rest of its messages
            # over to next, then close next.
            for message in right_buffer:
                if self.right_to_left:
                    # If we were given a function to execute
                    message = self.right_to_left(message)
                self._send(message, self.left_socket)
                right_buffer.remove(message)
            self.left_socket.close()

        else:
            raise RuntimeError("Some weird error ocurred.")

    def _send(self, message, destination_socket):
        """ Processes, then sends the given message to the given
        destination_socket.
        """
        # convert to bytes.
        message_str = json.dumps(message)
        message_bytes = message_str.encode()
        # send to previous node
        destination_socket.sendall(message_bytes)
