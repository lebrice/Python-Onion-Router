"""
    steps to circuit building: Alice -> Bob -> Carol
    1.  Alice generates a new circuit ID (known only for A->B) and her half of diffie-hellman
        -> control packet, cmd = create

    2.  Bob responds with his half of diffie-hellman
        -> control packet, cmd = created
    2a. (encrypt symmetric key using RSA, k1, send to Bob ??)

    3.  Alice generates a new key to be sent to Carol.
        -> relay packet, cmd = extend, sent to Bob

    4.  Bob receives extend packet. generates new circuit ID (known only for B->C)
        -> control packet, cmd = create, with key from Alice for Carol
    ??? how does Bob know Alice's address?

    5.  Carol receives control packet, takes key from Alice, responds with her half of d-h
        -> control packet, cmd = created

    6.  Bob receives created from Carol, wraps payload
        -> relay packet, cmd = extended

    7.  Alice receives packet, connection established to Carol

    ... Repeat as many times as there are nodes in circuit

"""

import packet_manager as pm
import circuit_tables as ct
import relaying
import node
import RSA

def create_connection(node, rsa_keys):
    # fetch IP of next node
    # get public key + modulus from rsa
    # make [create] control packet
    # this is public for now
    # add entry to circuit table
    # send to next node
    return

def confirm_connection():
    # parse received control [create] packet (before calling this method)
    # add ip | circID to table
    # get key from rsa
    # make [created] control packet
    # send to prev node
    return

def key_exchange_send():
    # generate new key to be sent to a node
    # make new [exch] relay packet
    # add entry to sender key table
    # send to next node
    return

def key_exchange_rcv():
    # add entry to node key table
    return

def extend_circuit():
    # fetch IP of node to add
    # get key from rsa
    # make [extend] relay packet
    # send to node
    # send to adjacent node
    return

def rcv_relay():
    # add entry to relay table
    # lookup IP
    # forward packet to next node
    return