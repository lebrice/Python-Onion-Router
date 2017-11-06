#!/usr/bin/python3

import sys
import math
from cryptography.fernet import Fernet


class Encryptor:
    """Class responsible for encrypting and decrypting messages"""
    @staticmethod
    def encrypt(message, key):
        """Encode a message using the given key"""
        # TODO: encrypt the message using the key.
        raise NotImplementedError()

    @staticmethod
    def decrypt(message, key):
        """Decode a message using the given key"""
        # TODO: encrypt the message using the key.S
        raise NotImplementedError()

    @classmethod
    def successive_encrypt(cls, message, *keys):
        result = message
        for key in keys:
            result = cls.encrypt(result, key)
        return result

    @classmethod
    def successive_decrypt(cls, message, *keys):
        result = message
        for key in keys:
            result = cls.decrypt(result, key)
        return result


class FernetEncryptor(Encryptor):
    """
        Fernet encryption using Cryptography library
        steps:
            1.  generate a key that will be used to encrypt and decrypt
                this key is symmetric: both the sender and the node have the same copy
            2.  send key to node, encrypted using RSA after a Diffie-Hellman exchange
            3.  use key for subsequent encryption layers (the "onion")
    """

    def generate_key(message):
        return Fernet.generate_key()

    def encrypt(message, key):
        cipher_suite = Fernet(key)
        return cipher_suite.encrypt(message.encrypted)

    def decrypt(message, key):
        cipher_suite = Fernet(key)
        return cipher_suite.decrypt(message.encrypted)


class SimpleAdditionEncryptor(Encryptor):
    """Simply adds and subtracts the key to the message"""

    def encrypt(message, key):
        int_value = _to_int(message)
        int_key = _to_int(key)
        encripted_int = int_value + int_key * 2  # See TODO below.
        encripted_bytes = _to_bytes(encripted_int)
        return encripted_bytes
        """
        TODO: Figure out a way of passing the messages as strings instead of
        bytes. We are currently dependant on having the right key in order to
        be able to decrypt the message into a string. If we don't use the right
        key, the continuation bits are messed up and attempting to decode
        the string produces an error.

        For now, shifting the key to the left a bit helps, since the first bit
        isn't messed up as often. However, this must be fixed.
        """
        # encripted_string = _to_string(encripted_int)
        # return encripted_string

    def decrypt(message, key):
        int_value = _to_int(message)
        int_key = _to_int(key)
        decripted_int = int_value - int_key * 2
        decripted_bytes = _to_bytes(decripted_int)
        decripted_message = _to_string(decripted_bytes)
        return decripted_message


class DoNothingEncryptor(Encryptor):
    """ An encryptor that does nothing. Used in testing."""
    def encrypt(message: bytes, key):
        return message

    def decrypt(message: bytes, key):
        return message


def _to_string(data):
    if isinstance(data, str):
        return data
    elif isinstance(data, bytes):
        return data.decode()
    # Import the object types we will check for
    import messaging
    if isinstance(data, messaging.OnionMessage):
        return str(data)
    return str(data)


def _to_bytes(data, encoding='utf-8'):
    if isinstance(data, bytes):
        return data
    elif isinstance(data, str):
        return data.encode(encoding)
    elif isinstance(data, int):
        byte_length = math.ceil(data.bit_length() / 8)
        return data.to_bytes(byte_length, byteorder=sys.byteorder)
    import messaging
    # Import the object types we will check for
    if isinstance(data, messaging.OnionMessage):
        return str(data).encode(encoding)
    return bytes(data)


def _to_int(data):
    if isinstance(data, int):
        return data
    bytes_value = _to_bytes(data)
    return int.from_bytes(bytes_value, byteorder=sys.byteorder)
