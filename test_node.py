#!/usr/bin/python3
import unittest
import time
from node import *


class NodeTestCase(unittest.TestCase):
    @unittest.skip
    def test_node_init_works(self):
        print("TODO: write some good tests for the Node class.")

        dir_node = DirectoryNode()
        dir_node.start()

        onion_node = OnionNode("bob", 12346, 1235123)
        onion_node.start()

        time.sleep(1)
        dir_node.stop()
        onion_node.stop()
