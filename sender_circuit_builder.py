import socket
from threading import Thread
import packet_manager as pm
from encryption import FernetEncryptor
import RSA
import json

BUFFER_SIZE = 1024 # Constant for now
DEFAULT_TIMEOUT = 1
NUMBER_OF_NODES = 3

class SenderCircuitBuilder(Thread):

    """
    class used by a sender (onion_socket.py) to build a circuit progressively
    does the following, in order:
        takes a list of 3 nodes to establish a circuit
        sends a "create" packet to the first node, containing half of key exch + shared key
        waits until a valid "created" packet is received
        stores association between the circuit ID and the IP address in its circuit_table
        sends an "exch" packet to the first node (contains a symmetric key)
        stores association between circID and key in sender_key_table

        for each subsequent node,
        the same steps are repeated with an "extend" packet instead of a "create" packet
    """

    def __init__(self,
                 nodes,
                 rsa_keys,
                 circuit_table,
                 sender_key_table):
        super().__init__()
        self.nodes = nodes
        self.rsa_keys = rsa_keys
        self.circuit_table = circuit_table()
        self.sender_key_table = sender_key_table()

    def run(self):
        # will always send the packet through the first node to reach the others
        self._create(self.nodes[0].ip_address, self.nodes[0].receiving_port)

        for i in range(0, NUMBER_OF_NODES):
            k = FernetEncryptor.generate_key()
            ciphered_shared_key = RSA.encrypt_RSA(k, self.rsa_keys["public"], self.rsa_keys["modulus"])

            if i == 0:
                destID, pkt = pm.new_control_packet(0, "create", ciphered_shared_key)
            else:
                # data to be placed in "extend" packet payload. nodes will use circIDs to navigate,
                # until a node has decrypted the payload and finds the ip and port of the new node
                encrypted_data = {'encrypted_data': [{
                    'isDecrypted': True,
                    'ip': self.nodes[i].ip_address,
                    'port': self.nodes[i].receiving_port,
                    'data': ciphered_shared_key
                }]}

                # apply layers of encryption on shared key + key exchange before sending it
                # e.g. for node 2, apply layer 1 then layer 0
                for j in range(i-1, -1, -1):
                    layer = self.sender_key_table.get_key(destID, j)
                    encrypted_data = FernetEncryptor.encrypt(encrypted_data, layer)

                _, pkt = pm.new_relay_packet(destID, "extend", encrypted_data)

            # send first half of key exchange
            self._send(pkt)

            # wait for a response packet; 3 tries
            tries = 3
            rec_bytes = 0
            while tries != 0:
                try:
                    rec_bytes = self.client_socket.recv(BUFFER_SIZE)
                except socket.timeout:
                    tries -= 1
                    if tries == 0:
                        print("ERROR    Timeout while waiting for confirmation packet [3 tries]\n")
                        print("         Circuit building exiting. . .")
                        self._close()
                        return
                    continue

            # see if correct message was received
            message = json.load(rec_bytes.decode())
            if message['command'] != "created" or message['command'] != "extended" or 'command' not in message:
                print("ERROR    Did not receive expected confirmation packet\n")
                print("         Circuit building exiting. . .")
                self._close()
                return
            else:
                # received "created" packet successfully -- store info in tables
                self.sender_key_table.add_key_entry(destID, i, k)

                # store connection to first circID, the entry point to the circuit
                if (i == 0):
                    self.circuit_table.add_circuit_entry(self.nodes[0].ip_address, self.nodes[0].receiving_port, destID)

        print("Built circuit successfully")
        self._close()


    def _create(self, ip, port):
        self.client_socket = socket.socket(DEFAULT_TIMEOUT)
        self.client_socket.connect((ip, port))

    def _send(self, message_str):
        message_bytes = message_str.encode('utf-8')
        self.client_socket.sendall(message_bytes)

    def _close(self):
        self.client_socket.close()
