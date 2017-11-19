import socket
from threading import Thread
import json
import random
from random import randint
import string
import encryption as enc
import packet_manager as pm
import get_request as gr

BUFFER_SIZE = 4096

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
        self.circuit_table = circuit_table
        self.node_key_table = node_key_table
        self.node_relay_table = node_relay_table
        self.rsa_keys = rsa_keys

    def run(self):
        message_bytes = self.client_socket.recv(BUFFER_SIZE)
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

        print("received packet\n")
        message = json.loads(json_object)
        if 'type' in message and message['type'] == "relay":
            self._process_relay(message)
        elif 'type' in message and not message['type'] == "control":
            self._process_control(message)
        else:
            print("ERROR    Received message has invalid type\n")
            return


    def _process_relay(self, message):
        # message is going forwards,  decrypt one layer
        if message['command'] == "extend" or message['command'] == "relay_data":
            key = self.node_key_table.get_key(message['circID'])
            decrypted_payload = enc.decrypt_fernet(message['encrypted_data'], key)

            if 'isDecrypted' in decrypted_payload:
                if message['command'] == "extend":
                    # message has extend command and managed to decrypt it
                    # -> create a new control packet cmd=create, send to next node
                    destID = self._generate_new_circID()
                    self.node_relay_table.add_relay_entry(message['circID'], destID)

                    pkt = pm.new_control_packet(destID, "create", decrypted_payload['data'])
                    self._send(pkt, decrypted_payload['ip'], decrypted_payload['port'])
                elif message['command'] == "relay_data":
                    # fully decrypted a relay_data packet
                    # -> node is an exit node; make a GET request, wait for answer,
                    #    send encrypted answer back to connecting node using same key
                    print("Received message: ", decrypted_payload)
                    ans = gr.web_request(decrypted_payload)
                    if ans == '':
                        print("ERROR    Could not complete get request; sending back gibberish")
                        ans = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in
                                      range(len(16)))

                    # TODO: place address of website here
                    payload = pm.new_relay_payload(0, 0, ans)
                    encrypted_payload = enc.encrypt_fernet(payload, key)

                    pkt = pm.new_relay_packet(message['circID'], "relay_ans", encrypted_payload)
                    ip, port = self.circuit_table.get_address(message['circID']).split(':')
                    self._send(pkt, ip, port)

            else:
                # could not decrypt payload, meant for a node further along
                # -> get next node addr from table, replace circID, remove one layer, and send packet along
                destID = self.node_relay_table.get_dest_id(message['circID'])
                message['circID'] = destID
                message['encrypted_data'] = decrypted_payload
                ip, port = self.circuit_table.get_address(message['circID']).split(':')

                self._send(message, ip, port)

        # message is going backwards, encrypt one layer
        elif message['command'] == "extended" or message['command'] == "relay_ans":
            # if A -> B and message was received from B and goes backwards, send it to A
            fromID = self.node_relay_table.get_from_id(message['circID'])
            key = self.node_key_table.get_key(fromID)
            encrypted_payload = enc.encrypt_fernet(message['encrypted_data'], key)

            pkt = pm.new_relay_packet(fromID, message['command'], encrypted_payload)
            ip, port = self.circuit_table.get_address(fromID).split(':')
            self._send(pkt, ip, port)


    def _process_control(self, message):
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
            shared_key = enc.decrypt_RSA(cipher_shared_key, self.rsa_keys['private'], self.rsa_keys['modulus'])

            ip, port = self.addr.split(':')
            self.circuit_table.add_circuit_entry(ip, port, message['circID'])
            self.node_key_table.add_key_entry(message['circID'], shared_key)

            # send back useless data with the same length as the shared key
            pad = ''.join(
                random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(len(shared_key)))

            pm.new_control_packet(message['circID'], "created", pad)

        elif message['command'] == "created":
            # node was appended to circuit, is adjacent, and confirms its creation
            # -> wrap payload in "extended" packet, send it backwards
            fromID = self.node_relay_table.get_from_id(message['circID'])
            key = self.node_key_table.get_key(fromID)
            encrypted_payload = enc.encrypt_fernet(message['data'], key)

            pkt = pm.new_relay_packet(fromID, "extended", encrypted_payload)
            ip, port = self.circuit_table.get_address(fromID).split(':')
            self._send(pkt, ip, port)

        elif message['command'] == "destroy":
            # destroy association to sender, then forward message to next node
            destID = self.node_relay_table.get_dest_id(message['circID'])

            # exit node, i.e. reached end of circuit
            if destID == -1:
                return

            self.node_key_table.remove_key_entry(message['circID'])
            self.node_relay_table.remove_relay_entry(message['circID'])
            message['circID'] = destID

            ip, port = self.circuit_table.get_address(message['circID']).split(':')
            self.circuit_table.remove_circuit_entry(ip, port)

            self._send(message, ip, port)
