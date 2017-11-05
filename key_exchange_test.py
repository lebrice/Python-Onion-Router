import key_exchange_sender as keysend
import socket
import RSA
import key_exchange_receiver as kr
from messaging import IpInfo
from threading import Thread
import json

TCP_IP = '127.0.0.1'
TCP_PORT = 5019
BUFFER_SIZE = 1024

def start_receiver():
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
    shared_secrets_rec = {}
    ker = kr.KeyExchangeReceiver(conn, shared_secrets_rec, RSA.get_private_key_rsa())
    ker.start()

def start_sender():
    shared_secrets_send = {}
    neighbour = IpInfo(TCP_IP, TCP_PORT)
    k = keysend.KeyExchangeSender(shared_secrets_send, neighbour)
    k.start()

if __name__ == "__main__":
    thread_rec = Thread(target=start_receiver)
    thread_send = Thread(target=start_sender)
    thread_rec.start()
    thread_send.start()
    thread_send.join()
    thread_rec.join()