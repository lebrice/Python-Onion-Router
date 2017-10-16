#!/usr/bin/python3
"""
Module where message format, encoding and decoding is defined.
"""

import json


class OnionMessage:
    """
    Represents a message in the onion routing network.
    """

    header = "ONION ROUTING G12"

    def __init__(self, source="127.0.0.1", destination="", data=None, header=header):
        self.source = source
        self.destination = destination
        self.data = data

    @property
    def json(self):
        return self._to_json()

    def _to_json(self):
        template = f"""
        {{
            "header": "{self.header}",
            "source": "{self.source}",
            "destination": "{self.destination}"
        }}
        """
        return json.loads(template)

    def to_string(self):
        return json.dumps(self.json)

    def to_bytes(self):
        return self.to_string().encode()

    @classmethod
    def from_string(cls, str_or_bytes):
        return cls(**json.loads(str_or_bytes))


def main():
    message1 = OnionMessage()
    print(message1.to_string())

if __name__ == '__main__':
    main()