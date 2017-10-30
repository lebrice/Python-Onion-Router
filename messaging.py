#!/usr/bin/python3
"""
Module where message format, encoding and decoding is defined.
"""

import json
from json import JSONEncoder, JSONDecodeError


class JsonConversionMixin(object):
    """
    Defines a base class that can be converted to/from json.

    The class :must: have a *to_dict(self)* method, and a constructor
    accepting all required object fields as keyword arguments.
    """
    @classmethod
    def from_json_string(cls, string):
        """
        Transforms the given String or bytes into an instance of the class
        string: - a valid JSON with all required fields
        """
        kwargs = json.loads(string)
        return cls(**kwargs)

    @classmethod
    def is_valid_string(cls, string):
        try:
            bob = cls.from_json_string(string)
            return True
        except JSONDecodeError as err:
            # print("Error: Provided string is not a valid JSON.", err)
            return False
        except TypeError as err:
            # print("Error: JSON does not match required arguments:", err)
            return False

    def to_json_string(self):
        """
        Serializes the object into a JSON-formatted string
        """
        return json.dumps(self.to_dict())


class ToDictMixin(object):
    """ Mixin for converting an object to a dictionary """
    def to_dict(self):
        return self._traverse_dict(self.__dict__)

    def _traverse_dict(self, instance_dict):
        output = {}
        for key, value in instance_dict.items():
            output[key] = self._traverse(key, value)
        return output

    def _traverse(self, key, value):
        if isinstance(value, ToDictMixin):
            return value.to_dict()
        elif isinstance(value, dict):
            return self._traverse_dict(value)
        elif isinstance(value, list):
            return [self._traverse(key, v) for v in value]
        elif hasattr(value, '__dict__'):
            return self._traverse_dict(value.__dict__)
        else:
            return value


class OnionMessage(ToDictMixin, JsonConversionMixin):
    """
    Represents a message in the onion routing network.
    """
    HEADER = "ONION ROUTING G12"

    def __init__(self,
                 source=None,
                 destination=None,
                 data=None,
                 header=HEADER,
                 ):
        self.header = header
        self.source = source
        self.destination = destination
        self.data = data

    def __repr__(self):
        """
        Returns a Json-formatted string representation of the message.
        """
        return self.to_json_string()

    def to_bytes(self):
        return str(self).encode()

    @classmethod
    def from_json(cls, json_object):
        string = json.dumps(json_object)
        return cls.from_json_string(string)

    def __eq__(self, value):
        return str(self) == str(value)
