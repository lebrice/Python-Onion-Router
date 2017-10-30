#!/usr/bin/python
""" Module containing our user-defined errors """


class OnionError(Exception):
    def __init__(self, *args):
        super().__init__(args)


class OnionSocketError(OnionError):
    pass


class OnionNetworkError(OnionError):
    pass