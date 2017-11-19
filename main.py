import argparse
import get_request

if __name__ == "__main__":
    """Use: python onion_router.py -u perdu.com -n 4"""
    parser = argparse.ArgumentParser(description='Initialize an onion network and make a request to the desired website.')
    parser.add_argument('-u', '--url', action='store', dest='url',
                        help='Requested url')
    parser.add_argument('-n', '--node-count', type=int, action='store', dest='node_count', default=3,
                        help='Number of nodes in circuit.')

    args = parser.parse_args()
    print("Creating onion routing with {} nodes".format(args.node_count))
    print("Request for {}".format(args.url))
    print("{} returned:".format(args.url))

    #get request
    web_data = get_request.web_request(args.url)
    print(web_data.decode("UTF-8"))

