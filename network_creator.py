#!/usr/bin/python3
"""Module containing functions that create and initialize an onion network"""

from node import DirectoryNode, OnionNode


def create_network():
    directory_node, onion_nodes = generate_nodes()


def generate_nodes(onion_node_count=10, starting_port=12345):
    """Generates a directory node and some onion nodes.

    Returns: (DirectoryNode, List[OnionNode])
    """
    directory_node = DirectoryNode(receiving_port=starting_port)
    onion_nodes = []
    for i in range(onion_node_count):
        node_name = f"ONION_NODE_{i}"
        node_receiving_port = starting_port + i
        node_private_key = 127 + i  # Some lousy private key.
        node = OnionNode(node_name, node_receiving_port, node_private_key)
        onion_nodes.append(node)

    return directory_node, onion_nodes
