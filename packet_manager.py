import json
from random import randint
import circuit_tables

# keep track of used circuit IDs locally, preventing the reuse of circuit IDs
# faster than indexing into table; circID is added later
usedCircIDs = [ ]

# TODO: padding for fixed packet length
def new_control_packet(circID, command, data):
    """
    build a packet (header + payload) according to its type
    circID: circuit ID. different for each connection between nodes.

    control: packet is to be interpreted by the node
        -> create   : create a new circuit
        -> created  : new circuit has been created
        -> destroy  : destroy a circuit

    """

    if command == "create":
        minID = 10
        maxID = 99

        if len(usedCircIDs) > maxID - minID:
            print("ERROR    Too many active circuits; could not create circuit. Current max is ", maxID - minID + 1)
            print("         Try deleting a circuit before creating a new one")
            return

        circID = randint(minID, maxID)
        while True:
            try:
                usedCircIDs.index(circID)
            except ValueError:
                break

            # ID is taken somewhere along the line -> generate new one
            circID = randint(minID, maxID)

        usedCircIDs.append(circID)

    elif command == "created":
        try:
            usedCircIDs.index(circID)
        except ValueError:
            print("ERROR    Received a created circuit control packet for a circuit that was not created")

    elif command == "destroy":
        try:
            usedCircIDs.remove(circID)
        except ValueError:
            print("ERROR    Circuit ID to be destroyed does not match any existing circuit IDs")

    else:
        print("ERROR    Invalid command. Commands for control packets are [create], [created], [destroy]")

    return circID, json.dumps({'circID': circID,
                       'command': command,
                       'data': data
                       })


# TODO: complete this header with additional Tor functionality e.g. multiple streams (if needed)
#       if this feature is not added, merge this with create_control_packet method and add "relay" command
def new_relay_packet(circID, command, data):
    """
    build a packet (header + payload) according to its type
    circID: circuit ID. different for each connection between nodes.

    relay:      packet is to be forwarded by the node
                -> additional header: checksum, length of payload
                -> TODO: more stream commands

    valid commands:
        -> exch: packet contains symmetric key
        -> extend: packet contains RSA key, forward to next node
    """

    return circID, json.dumps({'circID': circID,
                       'relayFlag': True,
                       'command': command,
                       'data': data
                       })
