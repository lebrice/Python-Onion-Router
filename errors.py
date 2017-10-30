#!/usr/bin/python
""" Module containing our user-defined errors """


class OnionSocketError(Exception):
    def __init__(self, *args):
        super().__init__(args)
