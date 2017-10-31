import socket
import sys
from threading import Thread, Lock
import RSA

BUFFER_SIZE = 1024 #Constant for now, no defined header format

class KeyExchangeReceiver(Thread):
    """ Defines a worker responsible for answering key-exchange requests.

    Whenever a request is received at the :receiving_port:, the key exchange
    takes place, and the resulting shared_key and public_key are put until the
    :shared_secrets: dict.
    """

    def __init__(self, receiving_socket, shared_secrets):
        super().__init__()
        self._receiving_socket = receiving_socket
        self.shared_secrets = shared_secrets

        self._running_flag = False
        self._running_lock = Lock()

    def run(self):
        self.send_public_keys()

    @property
    def running(self) -> bool:
        with self._running_lock:
            return self._running_flag

    @running.setter
    def running(self, value: bool):
        with self._running_lock:
            self._running_flag = value

    def stop(self):
        self.running = False

    def send_public_keys(self):
        """Create a public key, private key and modulus for key exchange, add shared key to shared secrets
        TODO: Determine how the shared keys will be indexed"""
        n, e, d = RSA.get_private_key_rsa()
        public_keys = "{}:{}".format(e, n)
        self._receiving_socket.send(public_keys.encode())
        cipher_shared_key = int((self._receiving_socket.recv(BUFFER_SIZE)).decode())
        if not cipher_shared_key:
            return
        self._receiving_socket.close()
        shared_key = RSA.decrypt_RSA(cipher_shared_key, d, n)
        #currently just appending shared key to the list, need to determine how they will be indexed
        self.shared_secrets.append(shared_key)


