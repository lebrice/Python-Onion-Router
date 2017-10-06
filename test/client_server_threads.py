#!/usr/bin/python3

import socket
import sys
import threading


class ClientThread(threading.Thread):
    def __init__(self, client_socket=None, *args):
        """Creates a client thread, using a specific socket, if given,
        or a new one (using socket.socket())
        """
        super().__init__(*args)
        self.log("starting a Client thread")
        if not client_socket:
            self._socket = socket.socket()
        else:
            self._socket = client_socket

    def run(self):
        # Could be a remote host, in this case its the same machine.
        remotehost = socket.gethostname()
        self._socket.connect((remotehost, 12345))
        somebytes = self._socket.recv(1024)
        self.log("received: ", somebytes.decode())
        self._socket.close()

    def log(self, *message):
        print("Client: ", *message)


class ServerThread(threading.Thread):

    def __init__(self, *args):
        super().__init__(*args)
        self.log("starting a server thread")
        self._socket = socket.socket()
        self._host = socket.gethostname()
        self._port = 12345
        self._socket.bind((self._host, self._port))

    def run(self):
        self._socket.listen(5)  # Listen, with up to 5 queued up connections
        count = 0
        while count < 2:
            client_socket, address = self._socket.accept()
            task = RespondToClientTask(self, client_socket, address)
            client_specific_thread = threading.Thread(None, task)
            client_specific_thread.start()
            count += 1
        self._socket.close()

    def log(self, *message):
        print("Server: ", *message)


class RespondToClientTask(object):

    def __init__(self, server_thread, client_socket, address):
        self._server_thread = server_thread
        self._client_socket = client_socket
        self._address = address

    def __call__(self):
        # Do something with the connection, perhaps run a thread.
        self._server_thread.log(f"Got a connection from {self._address}")
        name_bytes = self._client_socket.recv(1024)
        self._client_socket.send("hey there!, thanks for connecting".encode())
        self._client_socket.close()


def main():
    server = ServerThread()
    server.start()
    client1 = ClientThread()
    client1.start()
    client2 = ClientThread()
    client2.start()
    print("done")


if __name__ == '__main__':
    main()
