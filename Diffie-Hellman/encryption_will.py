"""
    Encryption file.
    Deals with the header format and parsing + message encryption.

    https://svn.torproject.org/svn/projects/design-paper/tor-design.html
    http://doctrina.org/How-RSA-Works-With-Examples.html
"""

import random as rd
import math
#from Crypto.Cipher import AES
import ssl
random_function = ssl.RAND_bytes



def getSamplesLargeNumber(p, iterations):
    aValues = []
    while len(aValues) != iterations:
        sample = rd.randrange(2, p - 1)
        if sample not in aValues:
            aValues.append(sample)
    return aValues


def primeClaim(s, p, a, d):
    for i in range(s):
        power = pow(a, pow(2, i) * d, p)
        if power == p - 1:
            return True
        elif i == 0:
            if power == 1 or power == p - 1:
                return True
    return False


def genRandom(bits):
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

# returns true if a number's only divisors are 1 and itself
# 0 and 1 are not prime numbers by definition
# optimization: use a better algorithm
def check_if_prime(n):
    if n <= 1:
        return False
    for i in range(2, int(math.sqrt(n))):   # n exclusive
        if n % i == 0:
            return False
    return True

# returns true if two numbers share no factors except 1
# e.g.  21 and 16 are coprime
#       14 and 2 are not coprime
def check_if_coprime(n, m):
    if n <= 1 or m <= 1:
        return False
    if n > m: max = n
    else: max = m
    for i in range(2, int(math.sqrt(max + 1))):
        if n % i == 0 and m % i == 0:
            return False
    return True


# returns true if two numbers yield the same remainder when divided by a constant
# also: n is a factor of (a - b)
def check_if_congruent(a, b, n):
    if a % n == b % n:
        return True


# extended Euclidean algorithm, used to determine public and private exponents
# used to find a public exponent e s.t. gcd(e, phi) = 1
# as + bt = gcd(a,b) -> find coeffs s and t, find gcd
def extended_gcd(a, b):
    s, s_prev = 0, 1
    t, t_prev = 1, 0
    if (a > b):
        rem, rem_prev = b, a
    else:
        rem, rem_prev = a, b

    while rem != 0:
        quotient = rem_prev / rem

        temp = rem
        rem = rem_prev - quotient * rem
        rem_prev = temp

        temp = s
        s = s_prev - quotient * s
        s_prev = temp

        temp = t
        t = t_prev - quotient * t
        t_prev = temp


# returns two random prime numbers in interval [min, max]
def generate_random_prime_numbers(min, max):
    # generate list of all primes in range
    primes = [i for i in range(min,max) if check_if_prime(i)]

    # choose two in the list
    p = rd.choice(primes)
    q = rd.choice(primes)
    while p == q:
        q = rd.choice(primes)

    return [p, q]


def generate_random_prime_number_bits(min, max):
    return

# Miller-Rabin primality test
# is fast but can fail with low probability
def miller_rabin(num):
    return


# generate a public and private key to be used in a Diffie-Hellman exchange
# optimization: extended Euclidean algorithm
def RSA():
    #nums = generate_random_prime_numbers(10,1000)
    nums = [getLargePrime(), getLargePrime()]
    print("p =", nums[0], "q =", nums[1])
    mod = nums[0] * nums[1]
    #print("binary representation of mod: %s", bin(mod))
    #print("length of bin rep of mod: %d", len(bin(mod)) - 2)
    phi = (nums[0] - 1) * (nums[1] - 1)   # totient of n: number of coprimes of n

    # choose public exp s.t. 1 < e < phi and e is coprime to phi
    # temp = [e for e in range(2, phi) if check_if_coprime(e, phi)]
    # public_exp = random.choice(temp)
    public_exp = 2**16 + 1   # 65537

    # choose private exp congruent to public exp
    # extended euclidean algorithm
    #temp = [d for d in range(2, phi) if check_if_congruent(d, public_exp, phi)]
    #private_exp = rd.choice(temp)
    private_exp = mulinv(public_exp, phi)

    return mod, public_exp, private_exp

"""def encrypt_AES(key, message):
    obj = AES.new(key, AES.MODE_CBC, 'This is an IV456')
    return obj.encrypt(message)


def decrypt_AES(key, ciphertext):
    obj = AES.new(key, AES.MODE_CBC, 'This is an IV456')
    return obj.decrypt(ciphertext)"""


def create_header():
    return


def encrypt_RSA(message, e, n):
    return pow(message, e, n)


def decrypt_RSA(ciphertext, d, n):
    return pow(ciphertext, d, n)

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


def convertTextToNumber(message):
    return int.from_bytes(message.encode('utf-8'), 'little')


def convertNumberToText(number):
    return number.to_bytes((number.bit_length() + 7) // 8, 'little').decode('utf-8')


def main():
    n, e, d = RSA()
    print("mod = ", n)
    print("public exp e = ", e)
    print("private exp d = ", d)

    message = "RSA in the house"
    print("Message: ", message)
    cipherRSA = encrypt_RSA(convertTextToNumber(message), e, n)
    print("Cipher RSA: ", cipherRSA)
    decryptedRSA = decrypt_RSA(cipherRSA, d, n)
    originalMessage = convertNumberToText(decryptedRSA)
    print("Original: ", originalMessage)


if __name__ == "__main__":
    main()