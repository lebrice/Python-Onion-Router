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

STARTING_PORT = 12345
NODE_COUNT = 3

DIR_IP = socket.gethostname()
DIR_PORT = STARTING_PORT


class IntegrationTestCase(unittest.TestCase):
    """
    Integration Tests for the Onion Network.
    """
    def setUp(self):

        self.directory_node, self.onion_nodes = generate_nodes(
            onion_node_count=NODE_COUNT,
            starting_port=STARTING_PORT
        )
        
        self.directory_node.start()
        for node in self.onion_nodes:
            node.connect(DIR_IP, DIR_PORT)
            node.start()
        
        # Start the test website, that listens on port 80.
        self.website = TestingWebsite(port=80)
        self.website.start()

    def tearDown(self):
        self.website.stop()
        for node in self.onion_nodes:
            node.stop()
        self.directory_node.stop()

    def test_directory_node_builds_list_correctly(self):
        time.sleep(0.5)  # Give enough time for the local network to be setup

        url = "www.perdu.com"

        client = OnionClient(dir_ip, 55555, args.node_count)
        client.connect(dir_ip, dir_port)
        #client.start()

        print("#####REQUESTING#####")
        will = client.send_through_circuit(url)
        filename = 'returned.html'
        _write_to_html(filename, will)

        webbrowser.get().open('file://' + os.path.realpath(filename), 1)
        #client.send("hello")


class TestingWebsite(threading.Thread):
    """
    Represents a website that listens for requests.
    """
    def __init__(self, port=80):
        super().__init__()
        self.port = port
        self.running = False

        self.received_messages = []

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

                    received_bytes = b''.join(received_chunks)
                except socket.timeout:
                    continue

    def stop(self):
        self.running = False


def generate_nodes(onion_node_count=10, starting_port=12345):
    """Generates a directory node and some onion nodes.

    Returns: (DirectoryNode, List[OnionNode])
    """
    directory_node = DirectoryNode(ip=socket.gethostname(), port=starting_port)
    onion_nodes = []
    for i in range(onion_node_count):
        node_name = "ONION_NODE_{}".format(i)
        node_receiving_port = starting_port + i
        node_private_key = 127 + i  # Some lousy private key.
        node = OnionNode(ip=socket.gethostname(), port=node_receiving_port)
        onion_nodes.append(node)

    return directory_node, onion_nodes
