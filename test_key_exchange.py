import key_exchange_sender as keysend
import socket
import RSA
import key_exchange_receiver as kr
from messaging import IpInfo
from threading import Thread
import json
import unittest
from time import sleep

TCP_IP = '127.0.0.1'
TCP_PORT = 5019
BUFFER_SIZE = 1024


class KeyExchangeTestCase(unittest.TestCase):

    shared_secrets_rec = {}
    shared_secrets_send = {}

    def start_receiver(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((TCP_IP, TCP_PORT))
        s.listen(1)
        conn, addr = s.accept()
        key_request = conn.recv(1024)

        #This next step would normally be done in process message
        #it would then give the socket to keyexchangereceiver
        json_shared_key = json.loads(key_request)
        if json_shared_key['type'] != "key_exchange_request":
            print("Not a Key request")
            return
        ker = kr.KeyExchangeReceiver(conn, self.shared_secrets_rec, RSA.get_private_key_rsa())
        ker.start()

    def start_sender(self):
        neighbour = IpInfo(TCP_IP, TCP_PORT)
        k = keysend.KeyExchangeSender(self.shared_secrets_send, neighbour)
        k.start()

    def test_key_exchange(self):
        thread_rec = Thread(target=self.start_receiver)
        thread_send = Thread(target=self.start_sender)
        thread_rec.start()
        thread_send.start()
        thread_rec.join()
        thread_send.join()

        #attend que le key exchange soit fait avant de checker si les shared secret dict sont pareil
        #pas tres tres beau
        sleep(1)
        self.assertEqual(self.shared_secrets_rec[0], self.shared_secrets_send[0])