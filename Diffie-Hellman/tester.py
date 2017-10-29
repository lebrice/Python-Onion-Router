from binascii import hexlify
import diffie_manager as dh

if __name__ == "__main__":
    a = dh.DiffieHellman()
    b = dh.DiffieHellman()

    a.genKey(b.publicKey)
    b.genKey(a.publicKey)

    if (a.getKey() == b.getKey()):
        print("Shared keys match.")
        print("Key:", hexlify(a.key))