#!/usr/bin/python3
"""
Module where message format, encoding and decoding is defined.
"""

import json
from json import JSONEncoder, JSONDecodeError


class JsonMixin(object):
    @classmethod
    def from_json_string(cls, data):
        kwargs = json.loads(data)
        return cls(**kwargs)

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def is_valid_json_string(cls, string):
        try:
            bob = cls.from_json_string(string)
            return True
        except JSONDecodeError as err:
            # print("Error: Provided string is not a valid JSON.", err)
            return False
        except TypeError as err:
            # print("Error: JSON does not match required arguments:", err)
            return False


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


class OnionMessage(ToDictMixin, JsonMixin):
    """
    Represents a message in the onion routing network.
    """

    HOME = "127.0.0.1"
    HEADER = "ONION ROUTING G12"

    def __init__(self,
                 source=HOME,
                 destination="",
                 data=None,
                 header=HEADER,
                 ):
        self.header = header
        self.source = source
        self.destination = destination
        self.data = data

    def to_string(self):
        """
        Returns a Json-formatted string representation of the message.
        """
        return str(self.to_json())

    def to_bytes(self):
        return self.to_string().encode()


def main():
    message1 = OnionMessage()
    str1 = message1.to_string()

    json1 = json.loads(str1)
    # json1 = OnionMessage.from_json(str1)
    message2 = OnionMessage.from_json_string(str1)

    bob = """
    {
        "header": "ONION ROUTING G12", 
        "source": "127.0.0.1",
        "destination": "",
        "data": null,
        "afwe": 1
    }
    """
    assert not OnionMessage.is_valid_json_string(bob)

if __name__ == '__main__':
    main()