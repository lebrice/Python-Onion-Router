import json

# TODO: padding for fixed packet length
def new_control_packet(circID, command, data):
    """
    build a packet (header + payload) according to its type
    circID: circuit ID. different for each connection between nodes.

    control: packet is to be interpreted by the node
        -> create   : create a new circuit (circID arg will be ignored)
        -> created  : new circuit has been created
        -> destroy  : destroy a circuit

        -> dir_query  : query directory node for a list of all nodes in onion network
        -> dir_update : update a node's public RSA key information

    """
    if command == "create" or command == "created" or command == "destroy":
        return json.dumps({
            'circID': circID,
            'relayFlag': False,
            'command': command,
            'data': data
        })
    elif command == "dir_query" or command == "dir_update":
        return json.dumps({
            'command' : command,
            'public_exp' : data["public"],
            'modulus' : data["modulus"]
        })


# TODO: complete this header with additional Tor functionality e.g. multiple streams (if needed)
#       if this feature is not added, merge this with create_control_packet method and add "relay" command
def new_relay_packet(circID, command, encrypted_data):
    """
    build a packet (header + payload) according to its type
    circID: circuit ID. different for each connection between nodes.

    relay:      packet is to be forwarded by the node
                -> TODO additional header fields: checksum, length of payload, stream cmds

    valid commands:
        -> extend: packet contains RSA key and next node's IP addr
        -> extended: circuit was successfully extended
    """

    return json.dumps({
            'circID': circID,
            'relayFlag': True,
            'command': command,
            'encrypted_data': encrypted_data
    })