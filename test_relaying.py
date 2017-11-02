#!/usr/bin/python3

import unittest

from relaying import *


class SplitIntoObjectsTestCase(unittest.TestCase):
    def test_split_into_objects_works(self):
        strings = [
            """{"name": "bob", "age": 21}""",
            """
            {
                "name": "clarice",
                "age": 14
            }"""
        ]
        string = ''.join(strings)

        for original_str, result in zip(strings, split_into_objects(string)):
            result_object, length_used = result
            self.assertEqual(json.loads(original_str), result_object)
            self.assertEqual(len(original_str), length_used)

    def test_split_into_objects_sows_correct_used_length(self):
        useful_chars = "{'name': 'bob', 'age': 21}"
        unused_chars = "123456789"
        string = useful_chars + unused_chars

        for result in split_into_objects(string):
            obj, length = result
            self.assertEqual(length, len(useful_chars))
            self.assertEqual(obj, json.loads(useful_chars))


class RelayTestCase(unittest.TestCase):
    pass
