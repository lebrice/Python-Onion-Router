#!/usr/bin/python3

import json
import unittest

from messaging import OnionMessage


class ToFromJsonCase(unittest.TestCase):
    def test_invalid_json(self):
        bob = """
        {
            "header": "ONION ROUTING G12",
            "source": "127.0.0.1",
            "destination": "",
            "data": null
        """
        self.assertFalse(OnionMessage.is_valid_string(bob))

    def test_invalid_parameters(self):
        bob = """
        {
            "header": "ONION ROUTING G12",
            "source": "127.0.0.1",
            "destination": "",
            "data": null,
            "afwe": 1
        }
        """
        self.assertFalse(OnionMessage.is_valid_string(bob))

    def test_valid_parameters(self):
        bob = """
        {
            "header": "ONION ROUTING G12",
            "source": "127.0.0.1",
            "destination": "",
            "data": null
        }
        """
        self.assertTrue(OnionMessage.is_valid_string(bob))

    def test_to_json_equals_original(self):
        obj_str = """
        {
            "header": "ONION ROUTING G12",
            "source": "127.0.0.1",
            "destination": "",
            "data": null
        }
        """
        obj1 = OnionMessage.from_json_string(obj_str)
        # Since indenting changes the answer, we check if the objects
        #  are dumped to the same string by both libraries
        obj2 = json.loads(obj_str)

        str1 = obj1.to_json_string()
        str2 = json.dumps(obj2)
        self.assertEqual(str1, str2)
