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

BUFFER_SIZE = 4096


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

    def __init__(self,
                left_socket: SocketType,
                right_socket: SocketType,
                left_to_right=None,
                right_to_left=None,
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
                self.process_and_send(message, self.right_socket)
                left_buffer.remove(message)

            # send to prev node
            for message in right_buffer:
                self.process_and_send(message, self.left_socket)
                right_buffer.remove(message)

        # One of the two closed.

        # IMPORTANT: whenever one of the nodes closes its socket, we assume
        # that whatever message may come after that point can be dumped.

        if self.left_reader.closed:
            # Prev is done sending messages. Send the the rest of its messages
            # over to next, then close next.
            for message in left_buffer:
                self.process_and_send(message, self.right_socket)
                left_buffer.remove(message)
            self.right_socket.shutdown(flag=socket.SHUT_WR)
            self.right_socket.close()

        elif self.right_reader.closed:
            # Prev is done sending messages. Send the the rest of its messages
            # over to next, then close next.
            for message in right_buffer:
                self.process_and_send(message, self.left_socket)
                right_buffer.remove(message)
            self.left_socket.shutdown(flag=socket.SHUT_WR)
            self.left_socket.close()

        else:
            raise RuntimeError("Some weird error ocurred.")

    def process_and_send(self, message, destination_socket):
        """ Processes, then sends the given message to the given
        destination_socket.
        """
        # See related function docstring
        processed_message = do_something_with_message(message)
        # convert to bytes.
        message_str = str(processed_message)
        message_bytes = message_str.encode()
        # send to previous node
        destination_socket.sendall(message_bytes)

    def do_something_with_message(self, message):
        """TODO: handle a message, maybe decrypt something, add some fields,
        whatever you need to do between receiving a message from one node and
         forwarding it to the next.
        """
        return message


class SocketReader(Thread):
    """
    Reads from a given socket, and whenever it receives a message, adds it
    in the given received_messages list.
    """
    def __init__(self, _socket: SocketType, received_messages: List):
        super().__init__()
        self.recv_socket = _socket
        self.received_messages = received_messages
        self.closed = False

    def run(self):
        received_so_far = ""

        empty = False

        while not empty:
            received_bytes = self.recv_socket.recv(BUFFER_SIZE)
            
            empty = (received_bytes == b'')
            if empty:
                break
            received_string = str(received_bytes, encoding="UTF-8")
            received_so_far += received_string

            received_objects = split_into_objects(received_so_far)

            for obj, length in received_objects:
                self.received_messages.append(obj)
                # Remove the bytes we used.
                received_so_far = received_so_far[length:]

        self.recv_socket.close()
        self.closed = True


def split_into_objects(string):
    """
    splits the given string into a series of tuples:
    (JSON object, length of string used to create that object).
    """
    import json
    string_so_far = ""
    open_bracket_count = 0
    closed_bracket_count = 0
    for char in string:
        string_so_far += char
        if char == '{':
            open_bracket_count += 1
        elif char == '}':
            closed_bracket_count += 1
        if open_bracket_count == closed_bracket_count:
            try:
                obj = json.loads(string_so_far)
                # Return the object, since the parsing worked.
                yield (obj, len(string_so_far))

            except json.JSONDecodeError:
                pass  # OK. that wasn't a valid json. Keep trying.

            else:
                # No exceptions ocurred. We reset the counter variables.
                string_so_far = ""
                open_bracket_count = 0
                closed_bracket_count = 0
