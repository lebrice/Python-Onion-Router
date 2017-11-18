import socket
from threading import Thread
import json
import random
from random import randint
import string
from encryption import FernetEncryptor
import RSA
import packet_manager as pm

class NodeSwitchboard(Thread):

    """
    class that is created when a node (node.py) accepts a connection from a socket.
    it does the following, in order:
        receives the packet from the connecting socket,
        parses the packet and decides what to do with the data
        creates and sends a new packet as appropriate
        closes itself
    """

    def __init__(self,
                 client_socket : socket,
                 addr,
                 circuit_table,
                 node_key_table,
                 node_relay_table,
                 rsa_keys):
        super().__init__()
        self.client_socket = client_socket
        self.addr = addr
        self.circuit_table = circuit_table()
        self.node_key_table = node_key_table()
        self.node_relay_table = node_relay_table()
        self.rsa_keys = rsa_keys

    def run(self):
        message_bytes = self.client_socket.recv()
        message_json = message_bytes.decode('utf-8')
        self._process_message(message_json)

    def _send(self, message_str, ip, port):
        message_bytes = message_str.encode('utf-8')
        self.client_socket.connect((ip, port))
        self.client_socket.sendall(message_bytes)
        self._close()

    def _close(self):
        self.client_socket.close()

    def _generate_new_circID(self):
        # define a limit to how many circuits the node can be part of
        max_circuit_no = 100

        if self.node_relay_table.get_length() == max_circuit_no:
            print("ERROR    Too many active circuits; could not create circuit. Current max is ", max_circuit_no)
            print("         Try deleting a circuit before creating a new one")
            return

        # generate a circID that is not in use in the node_relay_table
        while True:
            circID = randint(0, 10000)
            if self.node_relay_table.get_from_id(circID) == -1 and self.node_relay_table.get_dest_id(circID) == -1:
                break

        return circID

    def _process_message(self, json_object):
        """
        parses the packet that was received, and acts accordingly
        """

        message = json.load(json_object)

        if 'relayFlag' in message and message['relayFlag']:
                # message is a relay message; try decrypting the payload
                key = self.node_key_table.get_key(message['circID'])
                decrypted_payload = FernetEncryptor.decrypt(message['encrypted_data'], key)

                if 'isDecrypted' in decrypted_payload:
                    if message['command'] == "extend":
                        # message has extend command and managed to decrypt it
                        # -> create a new control packet cmd=create, send to next node
                        destID = self._generate_new_circID()
                        self.node_relay_table.add_relay_entry(message['circID'], destID)

                        pkt = pm.new_control_packet(destID, "create", decrypted_payload['data'])
                        self._send(pkt, decrypted_payload['ip'], decrypted_payload['port'])
                    elif message['command'] == "extended":
                        #TODO
                        return
                    elif message['command'] == "relay_data":
                        # fully decrypted a relay_data packet
                        # -> node is an exit node; make a GET request, wait for answer, send it backwards
                        return

                else:
                    # could not decrypt payload, meant for a node further along
                    # -> get next node addr from table, replace circID, remove one layer, and send packet along
                    destID = self.node_relay_table.get_dest_id(message['circID'])
                    message['circID'] = destID
                    message['encrypted_data'] = decrypted_payload
                    addr = self.circuit_table.get_address(message['circID'])
                    ip, port = addr.split(':')

                    self._send(message, ip, port)

        elif 'relayFlag' in message and not message['relayFlag']:
            # received message is a control message
            if message['command'] == "create":
                # received half of a RSA key exchange
                # -> create association with sender in table, deal with keys, send back a "created" packet
                cipher_shared_key = message['data']
                try:
                    cipher_shared_key = int(cipher_shared_key)
                except ValueError:
                    print("ERROR    Could not interpret cipher shared key\n")
                    self._close()
                    return
                shared_key = RSA.decrypt_RSA(cipher_shared_key, self.rsa_keys['private'], self.rsa_keys['modulus'])

                self.circuit_table.add_circuit_entry(self.addr[0], self.addr[1], message['circID'])
                self.node_key_table.add_key_entry(message['circID'], shared_key)

                # send back useless data with the same length as the shared key
                pad = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(len(shared_key)))

                pm.new_control_packet(message['circID'], "created", pad)

            elif message['command'] == "created":
                # node was appended to circuit, is adjacent, and confirms its creation
                # TODO: -> create a confirmation relay extended
                return

            elif message['command'] == "destroy":
                # destroy association to sender, then forward node
                # TODO: implement this
                return
        else:
            print("ERROR    Received message has invalid format\n")
            return