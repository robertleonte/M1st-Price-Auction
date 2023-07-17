from Utils import utils


def encrypt(p, g, h, plaintext):
    y = utils.generate_random_factor(p)
    s = pow(h, y, p)
    c1 = pow(g, y, p)
    c2 = (plaintext * s) % p
    return y, c1, c2


def reencrypt(p, g, h, cipher1, cipher2):
    y = utils.generate_random_factor(p)
    s = pow(h, y, p)
    c1 = (cipher1 * pow(g, y, p)) % p
    c2 = (cipher2 * s) % p
    return y, c1, c2


def encrypt_zkp(p, g, h, y, plaintext):
    s = pow(h, y, p)
    c1 = pow(g, y, p)
    c2 = (plaintext * s) % p
    return c1, c2


def decrypt(c1, c2, p, x):
    s = pow(c1, x, p)
    plaintext = (c2 * pow(s, -1, p)) % p
    return plaintext
