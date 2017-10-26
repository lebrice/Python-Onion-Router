#!/usr/bin/python3

import unittest
from encryption import *


class SimpleAdditionEncriptorTestCase(unittest.TestCase):
    def setUp(self):
        self.key = 12345

    def test_decrypt_encrypt_equals_original_message(self):
        message = "Hello there!"
        encrypted = SimpleAdditionEncriptor.encrypt(message, self.key)
        decrypted = SimpleAdditionEncriptor.decrypt(encrypted, self.key)
        self.assertEqual(message, decrypted)

    def test_wrong_key_does_not_decrypt_message(self):
        message = "Some private message"
        wrongKey = self.key + 1231  # some other key
        encrypted = SimpleAdditionEncriptor.encrypt(message, self.key)
        decrypted = SimpleAdditionEncriptor.decrypt(encrypted, wrongKey)
        self.assertNotEqual(message, decrypted)




