#!/usr/bin/python3
""" Integration testing """
import json
import socket
import threading
import time
import unittest

import node
import onion_client
from onion_client import OnionClient

from node import DirectoryNode, OnionNode

STARTING_PORT = 50000
NODE_COUNT = 3

DIR_IP = socket.gethostname()
DIR_PORT = STARTING_PORT

CLIENT_PORT = 55555

WEBSITE_IP = socket.gethostname()
WEBSITE_PORT = 80


class IntegrationTestCase(unittest.TestCase):
    """
    Integration Tests for the Onion Network.
    """
    def setUp(self):

        self.directory_node, self.onion_nodes = generate_nodes()
        
        self.directory_node.start()
        for node in self.onion_nodes:
            node.connect(DIR_IP, DIR_PORT)
            node.start()
        
        # Start the test website, that listens on port 80.
        self.website = TestingWebsite(port=WEBSITE_PORT)
        self.website.start()

    def tearDown(self):
        self.website.stop()
        for node in self.onion_nodes:
            node.stop()
        self.directory_node.stop()

    def test_send_through_circuit_works(self):
        time.sleep(0.5)  # Give enough time for the local network to be setup

        url = "{}:{}".format(WEBSITE_IP, WEBSITE_PORT)
        self.website.reply_message = "HI THERE"

        client = OnionClient(DIR_IP, CLIENT_PORT, NODE_COUNT)
        client.connect(DIR_IP, DIR_PORT)

        # TODO: Update onion_client, such that the separate return call is used.
        client.send_through_circuit(url)

        self.assertNotEqual(
            len(self.website.received_messages),
            0,
            "the website's list of received messages should not be empty")

        expected_received_at_website = b"GET / HTTP/1.1\r\nAccept-Encoding: identity\r\nConnection: close\r\nHost: " + DIR_IP.encode() + b":80\r\nUser-Agent: Python-urllib/3.5\r\n\r\n"
        actual_received_at_website = self.website.received_messages[0]

        self.assertEqual(
            expected_received_at_website,
            actual_received_at_website,
            "The website didn't receive what the client originally sent!")

    def test_receive_from_circuit_works(self):
        """
        tests that what is received from the circuit is the same as what the
        website originally sent.
        """
        time.sleep(0.5)  # Give enough time for the local network to be setup

        url = "{}:{}".format(WEBSITE_IP, WEBSITE_PORT)
        self.website.reply_message = "HI THERE"

        client = OnionClient(DIR_IP, CLIENT_PORT, NODE_COUNT)
        client.connect(DIR_IP, DIR_PORT)

        # TODO: Update onion_client, such that the separate return call is used.
        client.send_through_circuit(url)

        response = client.receive_from_circuit()
        self.assertEqual(response, self.website.reply_message)


class TestingWebsite(threading.Thread):
    """
    Represents a website that listens for requests.
    """
    def __init__(self, port=80):
        super().__init__()
        self.port = port
        self.running = False

        self.received_messages = []

        self.reply_message = ""

    def start(self):
        self.running = True
        super().start()

    def run(self):
        with socket.socket() as _socket:
            _socket.settimeout(1)
            _socket.bind((socket.gethostname(), self.port))
            _socket.listen()

            while self.running:
                try:
                    client_socket, address = _socket.accept()

                    done = False
                    received_chunks = []
                    while not done:
                        new_bytes = client_socket.recv(1024)
                        done = (new_bytes == b'')
                        received_chunks.append(new_bytes)
                        print("WEBSITE RECEIVED: ", new_bytes)
                    received_bytes = b''.join(received_chunks)

                    if self.reply_message:
                        client_socket.sendall(self.reply_message.encode())

                    client_socket.close()

                    self.received_messages.append(received_bytes)

                except socket.timeout:
                    continue

    def stop(self):
        self.running = False


def generate_nodes():
    """Generates a directory node and some onion nodes.

    Returns: (DirectoryNode, List[OnionNode])
    """
    directory_node = DirectoryNode(ip=DIR_IP, port=DIR_PORT)
    onion_nodes = []
    for i in range(NODE_COUNT):
        node_receiving_port = STARTING_PORT + i + 1
        node = OnionNode(ip=socket.gethostname(), port=node_receiving_port)
        onion_nodes.append(node)

    return directory_node, onion_nodes
