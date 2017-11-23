#!/usr/bin/python3

import argparse
import json
import os
import socket
import webbrowser

import onion_client as oc
import node
from node import DirectoryNode


def main():
    """
    Use: 
        > python create_dir_node.py -port 12346 [-dirIP '185.172.0.3' -dirPort 12345]
    """

    directory_node_port = None
    try:
        with open("config.json") as config_file:
            print("Loading Directory Node Info from 'config.json' file...")
            config = json.load(config_file)
            directory_node_port = int(config['DIR_NODE_PORT'])
            print("Using Directory Node PORT:", directory_node_port)
    except FileNotFoundError:
        raise RuntimeWarning("'config.json' file not found")

    parser = argparse.ArgumentParser(
        description='Initialize a directory_node in the onion_routing network.'
    )
    parser.add_argument(
        '-port',
        action='store',
        dest='port',
        type=str,
        default=directory_node_port,
        help='the port to create the directory_node on.'
    )

    args = parser.parse_args()

    dir_node = DirectoryNode(socket.gethostname(), int(args.port))
    dir_node.start()

    while("exit" not in input()):
        time.sleep(1)

    print("Closing Node")
    dir_node.stop()


if __name__ == '__main__':
    main()
