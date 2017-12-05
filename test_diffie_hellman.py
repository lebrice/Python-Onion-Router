#!/usr/bin/python3
import unittest
from diffie_hellman import *


class DiffieHellmanTestCase(unittest.TestCase):
    def test_diffie_hellman_receiver(self):
        server_port = 12345
        server_private_key = 11313
        server_shared_secrets = {}

        client_ip = socket.gethostname()
        client_private_key = 14

        receiver = DiffieHellmanReceiver(
            server_port,
            server_private_key,
            server_shared_secrets
        )
        receiver.start()

        receiver_public_key, shared_secret = get_shared_secret(
            socket.gethostname(),
            server_port,
            client_private_key
        )
        receiver.stop()
        receiver.join()
        # print(server_shared_secrets)
        
        self.assertEqual(
            receiver_public_key,
            compute_public_key(server_private_key)
        )
        # self.assertDictContainsSubset(server_shared_secrets, {shared_secret})
