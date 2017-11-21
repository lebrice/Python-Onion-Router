import argparse
import onion_client as oc
import node
import webbrowser
import os


def _write_to_html(filename, payload):
    # create the network file if it doesn't exist,
    try:
        f = open(filename, 'x')
    except FileExistsError:
        f = open(filename, 'w')
        f.seek(0)

    f.write(payload)
    f.close()


if __name__ == "__main__":
    """Use: python main.py -u perdu.com -n 3"""
    parser = argparse.ArgumentParser(description='Initialize an onion network and make a request to the desired website.')
    parser.add_argument('-u', '--url', action='store', dest='url',
                        help='Requested url')
    parser.add_argument('-n', '--node-count', type=int, action='store', dest='node_count', default=3,
                        help='Number of nodes in circuit.')

    args = parser.parse_args()
    print("Creating onion routing with {} nodes".format(args.node_count))

    # hard set 3 nodes for now:
    dir_ip = '127.0.0.1'
    dir_port = 12340
    dir = node.DirectoryNode(dir_ip, dir_port)
    dir.start()

    node1 = node.OnionNode('127.0.0.1', 14440)
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
    will = client.send_through_circuit(args.url)
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

