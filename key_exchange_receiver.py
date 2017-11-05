import socket
import sys
from threading import Thread, Lock
import RSA
import json

BUFFER_SIZE = 1024 #Constant for now, no defined header format

class KeyExchangeReceiver(Thread):
    """
    Takes care of a key exchange request. Receives the socket where the request was made
    """

    def __init__(self, client_socket, shared_secrets, rsa_keys):
        super().__init__()
        self._client_socket = client_socket
        self.shared_secrets = shared_secrets
        self.modulus = rsa_keys["modulus"]
        self.public_key = rsa_keys["public"]
        self.private_key = rsa_keys["private"]

    def run(self):
        self.send_public_keys()

    def send_public_keys(self):
        public_keys = {"public_key" : self.public_key, "modulus" : self.modulus}
        json_keys = json.dumps(public_keys)
        self._client_socket.send(json_keys.encode(encoding='UTF-8'))
        try:
            rec_bytes = self._client_socket.recv(BUFFER_SIZE)
        except socket.timeout:
            self._client_socket.close()
            return
        json_shared_key = json.loads(rec_bytes)
        if "cipher_key" not in json_shared_key or "id" not in json_shared_key:
            self._client_socket.close()
            return
        cipher_shared_key = json_shared_key['cipher_key']
        circuit_id = json_shared_key['id']
        try:
            cipher_shared_key = int(cipher_shared_key)
            circuit_id = int(circuit_id)
        except ValueError:
            self._client_socket.close()
            return
        shared_key = RSA.decrypt_RSA(cipher_shared_key, self.private_key, self.modulus)
        #index shared key by circuit
        self.shared_secrets[circuit_id] = shared_key


