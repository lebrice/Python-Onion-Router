"""
    Encryption file.
    Deals with the header format and parsing + message encryption.

    https://svn.torproject.org/svn/projects/design-paper/tor-design.html
    http://doctrina.org/How-RSA-Works-With-Examples.html
"""
import random as rd
import ssl
import json
from cryptography.fernet import Fernet
random_function = ssl.RAND_bytes


"""
    Fernet encryption using Cryptography library
    steps:
        1.  generate a key that will be used to encrypt and decrypt
            this key is symmetric: both the sender and the node have the same copy
        2.  send key to node, encrypted using RSA after a Diffie-Hellman exchange
        3.  use key for subsequent encryption layers (the "onion")
"""

def generate_fernet_key():
    return Fernet.generate_key()

# cipher takes bytes as arg, so some format manipulation is needed
# dict -> json -> bytes -> str
def encrypt_fernet(message, key):
    cipher_suite = Fernet(key)
    message_json = json.dumps(message)
    message_enc = cipher_suite.encrypt(message_json.encode('utf-8'))
    test = message_enc.decode('utf-8')
    return test

# str -> bytes -> json -> dict
def decrypt_fernet(message, key):
    cipher_suite = Fernet(key)
    message_str = message.decode('utf-8')
    message_bytes = cipher_suite.decrypt(message_str)
    test = json.loads(message_bytes.encode('utf-8'))
    return test


"""
    RSA encryption (self-implemented)
"""

def getSamplesLargeNumber(p, iterations):
    """Generates a sample with size iterations of large numbers from 1<n<p-1"""
    aValues = []
    while len(aValues) != iterations:
        sample = rd.randrange(2, p - 1)
        if sample not in aValues:
            aValues.append(sample)
    return aValues


def primeClaim(s, p, a, d):
    """helper method for the Rabbin-Miller Algorithm"""
    for i in range(s):
        power = pow(a, pow(2, i) * d, p)
        if power == p - 1:
            return True
        elif i == 0:
            if power == 1 or power == p - 1:
                return True
    return False

def genRandom(bits):
    """generate an odd number"""
    rand = 0
    bytes = bits // 8 + 8
    while rand.bit_length() < bits:
        rand = int.from_bytes(random_function(bytes), byteorder='big')
    if not rand & 1:
        rand += 1
    return rand

def getLargePrime(length=200):
    newPrime = genRandom(length)
    while not checkIfPrime(newPrime):
        newPrime += 2
    return newPrime

def checkIfPrime(p, iterations=64):
    """check if a number if prime using the Rabin-Miller Algorithm, 64 iterations has 1/2^128 error"""
    if p == 2:
        return True
    elif not p & 1:
        return False

    pow2 = p - 1
    s = 0
    while pow2 % 2 == 0:
        pow2 >>= 1
        s += 1
    d = (p - 1) // pow(2, s)

    # ensure enough values for 64 Miller-Rabin tests
    if p < iterations:
        iterations = p // 2
    # check if prime is larger than 2^15 - 1, as rd.sample needs ssize_t
    # ssize_t can store values of at least the range [-1 ... 2^15-1] per POSIX
    if p > pow(2, 15) - 1:
        aValues = getSamplesLargeNumber(p, iterations)
    else:
        aValues = rd.sample(range(2, p - 1), iterations)
    while aValues:
        if not primeClaim(s, p, aValues.pop(), d):
            return False
    return True

def get_private_key_rsa():
    """generate a public and private key to be used in a shared key exchange
    optimization: extended Euclidean algorithm"""
    nums = [getLargePrime(), getLargePrime()]
    mod = nums[0] * nums[1]
    phi = (nums[0] - 1) * (nums[1] - 1)   # totient of n: number of coprimes of n

    # choose public exp s.t. 1 < e < phi and e is coprime to phi
    public_exp = 2**16 + 1   # 65537

    # extended euclidean algorithm
    private_exp = mulinv(public_exp, phi)

    rsa_keys = {}
    rsa_keys["modulus"] = mod
    rsa_keys["public"] = public_exp
    rsa_keys["private"] = private_exp
    return rsa_keys

# only using RSA to encode a byte key
def encrypt_RSA(message, e, n):
    return pow(convertKeyToNumber(message), int(e), int(n))

def decrypt_RSA(ciphertext, d, n):
    return convertNumberToKey(pow(ciphertext, int(d), int(n)))

#https://en.wikibooks.org/wiki/Algorithm_Implementation/Mathematics/Extended_Euclidean_algorithm
def xgcd(b, n):
    x0, x1, y0, y1 = 1, 0, 0, 1
    while n != 0:
        q, b, n = b // n, n, b % n
        x0, x1 = x1, x0 - q * x1
        y0, y1 = y1, y0 - q * y1
    return  b, x0, y0


#https://en.wikibooks.org/wiki/Algorithm_Implementation/Mathematics/Extended_Euclidean_algorithm
def mulinv(b, n):
    g, x, _ = xgcd(b, n)
    if g == 1:
        return x % n


def convertKeyToNumber(message):
    return int.from_bytes(message, 'little')

def convertNumberToKey(number):
    return number.to_bytes((number.bit_length() + 7) // 8, 'little')


def convertTextToNumber(message):
    return int.from_bytes(message.encode('utf-8'), 'little')

def convertNumberToText(number):
    return number.to_bytes((number.bit_length() + 7) // 8, 'little').decode('utf-8')