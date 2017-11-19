import json

####################################### #
# TODO: padding for fixed packet length #
#########################################

def new_control_packet(circID, command, data):
    """
    build a packet (header + payload) according to its type
    circID: circuit ID. different for each connection between nodes.

    control: packet is to be interpreted by the node
        -> create   : create a new circuit (circID arg will be ignored)
        -> created  : new circuit has been created
        -> destroy  : destroy a circuit

    """
    return json.dumps({
        'type' : "control",
        'circID': circID,
        'command': command,
        'data': data
    })


def new_dir_packet(command, updated, data):
    """
    packets used to contact directory node
    don't need to be encrypted, as all information here is safe

        -> dir_query    : client queries directory for network list only.
        -> dir_update   : node queries directory for network list, and is added to the list
        -> dir_answer   : dir node sends all connected nodes back to node
                          if node was already in directory, update its rsa_keys

    """
    if command == "dir_query":
        return json.dumps({
            'type' : "dir",
            'command' : command
        })
    elif command == "dir_update":
        return json.dumps({
            'type' : "dir",
            'command' : command,
            'public_exp' : data["public"],
            'modulus' : data["modulus"]
        })
    elif command == "dir_answer":
        return json.dumps({
            'type' : "dir",
            'command' : command,
            'updated' : updated,
            'table' : data
        })

# TODO: complete this header with additional Tor functionality e.g. multiple streams (if needed)
#       if this feature is not added, merge this with create_control_packet method and add "relay" command
def new_relay_packet(circID, command, encrypted_data):
    """

    relay:      packet is to be forwarded by the node
                -> TODO additional header fields: checksum, length of payload, stream cmds

    valid commands:
        -> extend: packet contains RSA key and next node's IP addr
        -> extended: circuit was successfully extended
        -> relay_data : packet contains forward message (client -> server)
        -> relay_ans :  packet message contains backward message (server -> client)
    """

    return json.dumps({
            'type' : "relay",
            'circID': circID,
            'command': command,
            'encrypted_data': encrypted_data
    })


def new_relay_payload(ip, port, data):
    """
    list used for relay packet payload
    contains the part of the relay packet that needs to be encrypted
    """

    return {'isDecrypted': True,
            'ip': ip,
            'port': port,
            'data': data
    }