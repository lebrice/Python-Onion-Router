import socket
from threading import Thread

class ClientSocket(Thread):

    """
    simple class that takes data to be transmitted,
    creates a socket, tries to send the data (including retries),
    then closes itself
    """

    def __init__(self, message):
        self.message = message

    def run(self):
        self.start()

    def start(self):
        # do we need this?
        return
