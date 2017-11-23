#!/usr/bin/python3

import argparse
import json
import os
import socket
import webbrowser

import onion_client as oc
import node

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
        type=int,
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
        raise RuntimeError("Invalid Argument Error")
    return

    node = node.OnionNode(socket.gethostname(), 14440)
    node1.connect(dir_ip, dir_port)
    node1.start()

    node2 = node.OnionNode('127.0.0.1', 8880)
    node2.connect(dir_ip, dir_port)
    node2.start()

    node3 = node.OnionNode('127.0.0.1', 55610)
    node3.connect(dir_ip, dir_port)
    node3.start()

    client = oc.OnionClient('127.0.0.1', 54320, args.node_count)
    client.connect(dir_ip, dir_port)
    #client.start()

    print("#####REQUESTING#####")
    client.make_get_request_to_url(args.url)
    will = client.recv(10000)
    filename = 'returned.html'
    _write_to_html(filename, will)

    webbrowser.get().open('file://' + os.path.realpath(filename), 1)
    #client.send("hello")

    # print("Request for {}".format(args.url))
    # print("{} returned:".format(args.url))
    #
    # #get request
    # web_data = get_request.web_request(args.url)
    # print(web_data.decode("UTF-8"))

if __name__ == '__main__':
    main()
