#!/usr/bin/python3

import argparse
import json
import os
import socket
import webbrowser

import onion_client as oc
import node
from node import OnionNode


def main():
    """
    Use: 
        > python create_node.py -port 12346 [-dirIP '185.172.0.3' -dirPort 12345]
    """

    directory_node_ip = None
    directory_node_port = None
    try:
        with open("config.json") as config_file:
            print("Loading Directory Node Info from 'config.json' file...")
            config = json.load(config_file)
            directory_node_ip = config['DIR_NODE_IP']
            directory_node_port = config['DIR_NODE_PORT']
            print("Using Directory Node IP:", directory_node_ip)
            print("Using Directory Node PORT:", directory_node_port)
    except FileNotFoundError:
        raise RuntimeWarning("'config.json' file not found")

    parser = argparse.ArgumentParser(
        description='Initialize a node in the onion_routing network.'
    )
    parser.add_argument(
        '-port',
        action='store',
        dest='port',
        type=str,
        help='the port to create the node on.'
    )
    parser.add_argument(
        '-dirIP',
        action='store',
        dest='dirIP',
        type=str,
        default=directory_node_ip,
        help='the IP address of the Directory Node.'
    )
    parser.add_argument(
        '-dirPort',
        action='store',
        dest='dirPort',
        type=int,
        default=directory_node_port,
        help='the Port the Directory Node is listening on.'
    )

    args = parser.parse_args()

    if args.port is None:
        raise RuntimeError("Invalid 'port' argument")

    node = OnionNode(socket.gethostname(), int(args.port))
    node.connect(directory_node_ip, int(directory_node_port))
    node.start()

    while("exit" not in input()):
        time.sleep(1)

    print("Closing Node")
    node.stop()


if __name__ == '__main__':
    main()
