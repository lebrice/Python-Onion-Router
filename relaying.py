#!usr/bin/python3
"""
This module defines the Workers/Threads that are used to handle relaying
messages from one socket to another.
"""

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

    def __init__(self, previous_socket: SocketType, next_socket: SocketType):
        """ Initializes the relay. """
        super().__init__()
        self.prev_socket = previous_socket
        self.next_socket = next_socket

        self.prev_reader: List[OnionMessage] = None
        self.next_reader: List[OnionMessage] = None

    def run(self):
        """ Begin relaying messages from one socket to another.
        idea:
            - Listen for messages from prev
            - copy the messages to the next socket

            AND
            
            - Listen for messages from next socket
            - copy the messages to the prev socket

        TODO: This is just pseudocode for now.
        """
        prev_buffer = []  # messages received from the prev_socket.
        next_buffer = []  # messages received from the next_socket.

        self.prev_reader = SocketReader(self.prev_socket, prev_buffer)
        self.next_reader = SocketReader(self.next_socket, next_buffer)

        self.prev_reader.start()
        self.next_reader.start()

        while (not self.prev_reader.closed) and (not self.next_reader.closed):
            # send to next node
            for message in prev_buffer:
                self.process_and_send(message, self.next_socket)

            # send to prev node
            for message in next_buffer:
                self.process_and_send(message, self.prev_socket)

        # One of the two closed.

        # IMPORTANT: whenever one of the nodes closes its socket, we assume
        # that whatever message may come after that point can be dumped.

        if self.prev_reader.closed:
            # Prev is done sending messages. Send the the rest of its messages
            # over to next, then close next.
            for message in prev_buffer:
                self.process_and_send(message, self.next_socket)
            self.next_socket.shutdown(flag=socket.SHUT_WR)
            self.next_socket.close()

        elif self.next_reader.closed:
            # Prev is done sending messages. Send the the rest of its messages
            # over to next, then close next.
            for message in next_buffer:
                self.process_and_send(message, self.prev_socket)
            self.prev_socket.shutdown(flag=socket.SHUT_WR)
            self.prev_socket.close()

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
    def __init__(self, p_socket, received_buffer):
        self.sock = p_socket
        self.received_buffer = received_buffer

    def read_from_socket(self, p_socket: SocketType):
        """ Read from the given socket.
        """
        received_string = ""
        empty = False

        while not empty:
            buffer = p_socket.recv(1024)
            empty = (buffer == b'')
            string = str(buffer, encoding='UTF-8')
            received_string += string

            objects = list(split_into_objects(received_string))
            object_count = len(objects)
            if object_count > 0:
                pass
                # We made an object out of what we have so far!
                # Proceed to return this object, and 
            else:
                # We have not received an object yet. keep going.
                continue





        # print("Received string:", received_string)

        # TODO: Might want to take this out, and simply return the
        # bytes that we receive, one at a time, since not everyone
        # might want to use this "split into objects" functionality.
        objects = split_into_objects(received_string)
        count = 0

        with self._out_queue:
            for obj in objects:
                self._out_queue.put(obj)
                count += 1
                # print("received_object: ", obj)

        print(f"done receiving {count} objects for this connection.")

    def both_are_open(self):
        """ Check that both sockets are open. """
        raise NotImplementedError()



def split_into_objects(string):
    """
    splits the given string into a series of JSON objects.
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
                yield obj  # Return the object, since the parsing worked.

            except json.JSONDecodeError:
                pass  # OK. that wasn't a valid json. Keep trying.

            else:
                # No exceptions ocurred. We reset the counter variables.
                string_so_far = ""
                open_bracket_count = 0
                closed_bracket_count = 0
