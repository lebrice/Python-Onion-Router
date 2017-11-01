from threading import Thread
import RSA
import socket
import json
import random
import string
from messaging import IpInfo

BUFFER_SIZE = 1024 #Constant for now, no defined header format
DEFAULT_TIMEOUT = 1

class KeyExchangeSender(Thread):
    """
    Starts a key exchange request. Receives shared secret dict and neighbour to make request
    """

    def __init__(self, shared_secrets, neighbour: IpInfo):
        super().__init__()
        self.shared_secrets = shared_secrets
        self._neighbour = neighbour
        self.client_socket = socket.socket()
        self.client_socket.settimeout(DEFAULT_TIMEOUT)
        self.client_socket.connect((neighbour.ip, neighbour.port))


    def run(self):
        self.send_shared_key()

    def send_shared_key(self):
        key_request = {"type": "key_exchange_request"}
        json_keys = json.dumps(key_request)
        self.client_socket.send(json_keys.encode(encoding='UTF-8'))
        try:
            rec_bytes = self.client_socket.recv(BUFFER_SIZE)
        except socket.timeout:
            self.client_socket.close()
            return
        json_public_keys = json.loads(rec_bytes)
        if "modulus" not in json_public_keys or "public_key" not in json_public_keys:
            self.client_socket.close()
            return
        public_key = json_public_keys["public_key"]
        modulus = json_public_keys["modulus"]
        #generate random shared key, length of 16
        #generate circuit id, not currently used
        shared_key = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(16))
        ciphered_shared_key = RSA.encrypt_RSA(shared_key, public_key, modulus)
        circuit_id = 0
        while circuit_id in self.shared_secrets:
            circuit_id += 1
        shared_key_pair = {"id":circuit_id, "cipher_key":ciphered_shared_key}
        json_shared_key = json.dumps(shared_key_pair)
        self.client_socket.send(json_shared_key.encode(encoding='UTF-8'))
        self.shared_secrets[circuit_id] = shared_key
        self.client_socket.close()