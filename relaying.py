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

import errors
from errors import OnionRuntimeError
from messaging import OnionMessage
import workers
from workers import SocketReader

BUFFER_SIZE = 4096


class IntermediateRelay(Thread):
    """
    Relays messages from one socket to another, using the provided functions.

    Params:
        - left_socket: Socket connected to the previous node.
        - right_socket: Socket connected to the next node.
        - left_to_right: function to be applied for each item taken from
        left_socket before putting it on right_socket.
        - right_to_left: function to be applied for each item taken from
        right_socket before putting it on left_socket.

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

        # processing functions described above.
        self.left_to_right = left_to_right
        self.right_to_left = right_to_left

        self._left_buffer = []  # messages received from the left socket.
        self._right_buffer = []  # messages received from the right socket.

        self.left_reader = SocketReader(self.left_socket, self._left_buffer)
        self.right_reader = SocketReader(self.right_socket, self._right_buffer)

    def start(self):
        """ Starts the Relay. """
        self.left_reader.start()
        self.right_reader.start()
        super().start()

    def run(self):
        """ Begin relaying messages from one socket to another.
        idea:
            - Listen for messages from left
            - copy the messages to the right socket

            AND

            - Listen for messages from right socket
            - copy the messages to the left socket

            until either of them closes its side of the connection.
        """

        while (not self.left_reader.closed) and (not self.right_reader.closed):
            # send to next node
            for message in self._left_buffer:
                if self.left_to_right:
                    # If we were given a function to execute
                    message = self.left_to_right(message)
                self._send(message, self.right_socket)
                self._left_buffer.remove(message)

            # send to prev node
            for message in self._right_buffer:
                if self.right_to_left:
                    # If we were given a function to execute
                    message = self.right_to_left(message)
                self._send(message, self.left_socket)
                self._right_buffer.remove(message)

        # One of the two closed.

        # IMPORTANT: whenever one of the nodes closes its socket, we assume
        # that whatever message may come after that point can be dumped.

        if self.left_reader.closed:
            # Prev is done sending messages. Send the the rest of its messages
            # over to next, then close next.
            for message in self._left_buffer:
                if self.left_to_right:
                    # If we were given a function to execute
                    message = self.left_to_right(message)
                self._send(message, self.right_socket)
                self._left_buffer.remove(message)
            self.right_socket.close()

        elif self.right_reader.closed:
            # Prev is done sending messages. Send the the rest of its messages
            # over to next, then close next.
            for message in self._right_buffer:
                if self.right_to_left:
                    # If we were given a function to execute
                    message = self.right_to_left(message)
                self._send(message, self.left_socket)
                self._right_buffer.remove(message)
            self.left_socket.close()

        else:
            raise OnionRuntimeError("Some weird error ocurred.")

    def _send(self, message, destination_socket):
        """ Processes, then sends the given message to the given
        destination_socket.

        NOTE: This should never be called outside the relay, as indicated by
        the "_" field prefix.
        """
        # convert to bytes.
        message_str = json.dumps(message)
        message_bytes = message_str.encode()
        # send to previous node
        destination_socket.sendall(message_bytes)
