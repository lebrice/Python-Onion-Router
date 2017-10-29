"""
    Encryption file.
    Deals with the header format and parsing + message encryption.

    https://svn.torproject.org/svn/projects/design-paper/tor-design.html
"""

import random
import math

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
    p = random.choice(primes)
    q = random.choice(primes)
    while p == q:
        q = random.choice(primes)

    return [p, q]


def generate_random_prime_number_bits(min, max):
    return

# Miller-Rabin primality test
# is fast but can fail with low probability
def miller_rabin(num):
    return


# generate a public and private key to be used in a Diffie-Hellman exchange
# optimization: extended Euclidean algorithm
def encrypt_RSA():
    nums = generate_random_prime_numbers(10,1000)
    print("p =", nums[0], "q =", nums[1])
    mod = nums[0] * nums[1]
    #print("binary representation of mod: %s", bin(mod))
    #print("length of bin rep of mod: %d", len(bin(mod)) - 2)
    phi = (nums[0] - 1) * (nums[1] - 1)   # totient of n: number of coprimes of n

    # choose public exp s.t. 1 < e < phi and e is coprime to phi
    # temp = [e for e in range(2, phi) if check_if_coprime(e, phi)]
    # public_exp = random.choice(temp)
    public_exp = 2**6 + 1   # 65537

    # choose private exp congruent to public exp
    # extended euclidean algorithm
    temp = [d for d in range(2, phi) if check_if_congruent(d, public_exp, phi)]
    private_exp = random.choice(temp)

    return [mod, public_exp, private_exp]


def encrypt_AES():
    return

def create_header():
    return

def main():
    results = encrypt_RSA()
    print("mod = ", results[0])
    print("public exp e = ", results[1])
    print("private exp d = ", results[2])

if __name__ == "__main__":
    main()