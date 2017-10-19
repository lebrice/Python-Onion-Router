#!/usr/bin/python3

import sys
import math


class Encriptor:
    """Class responsible for encrypting and decrypting messages"""
    def encrypt(message, key):
        """Encode a message using the given key"""
        # TODO: encrypt the message using the key.
        raise NotImplementedError()

    def decrypt(message, key):
        """Decode a message using the given key"""
        # TODO: encrypt the message using the key.S
        raise NotImplementedError()


class SimpleAdditionEncriptor(Encriptor):
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


def main():
    text1 = "hello!!"
    key = 123
    encripted = SimpleAdditionEncriptor.encrypt(text1, key)
    decripted = SimpleAdditionEncriptor.decrypt(encripted, key)
    print(text1, encripted, decripted, sep='\n')


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


if __name__ == '__main__':
    main()
