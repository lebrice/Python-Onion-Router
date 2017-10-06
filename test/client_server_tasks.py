#!/usr/bin/python3

import socket
import sys
import threading


class ServerTask(object):

    def __init__(self):
        print("starting a server thread")
        self._socket = socket.socket()
        self._host = socket.gethostname()
        # port number that clients will use to contact the server.
        self._port = 12345
        self._socket.bind((self._host, self._port))

    def __call__(self):
        self._socket.listen(5)  # Listen, with up to 5 queued up connections
        count = 0
        while count < 2:
            client_socket, address = self._socket.accept()
            # Do something with the connection, perhaps run a thread.
            print(f"Got a connection from {address}")
            client_socket.send("hey there!, thanks for connecting".encode())
            client_socket.close()
            count += 1


class ClientTask(object):

    def __init__(self):
        print("starting a client thread")
        self._socket = socket.socket()

    def __call__(self):
        # Could be a remote host, in this case its the same machine.
        remotehost = socket.gethostname()
        self._socket.connect((remotehost, 12345))
        somebytes = self._socket.recv(1024)
        print(somebytes.decode())
        self._socket.close()


def main(role="client"):
    if role == "server":
        server_thread = threading.Thread(None, ServerTask())
        server_thread.start()
    elif role == "client":
        client_thread = threading.Thread(None, ClientTask())
        client_thread.start()
    else:
        print(f"invalid role: {role}")

if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) > 0:
        role = args[0]
        main(role)
    else:
        main()
