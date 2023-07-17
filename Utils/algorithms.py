from Crypto.Random import random
from Crypto.Util import number


def jacobi_symbol(a, b):
    if b <= 0 or b % 2 == 0:
        return 0
    j = 1
    if a < 0:
        a *= -1
        if b % 4 == 3:
            j = -j

    while a != 0:
        while a % 2 == 0:
            a /= 2
            if b % 8 == 3 or b % 8 == 5:
                j = -j
        temp = a
        a = b
        b = temp
        if a % 4 == 3 and b % 4 == 3:
            j = -j
        a = a % b
    if b == 1:
        return j
    else:
        return 0


def quadratic_residue(p_arg, alpha):
    if jacobi_symbol(alpha, p_arg) == -1:
        return alpha
    else:
        return p_arg - alpha


def primitive_root(p_arg):
    while True:
        alpha = random.randint(2, p_arg - 1)
        quadr_res = quadratic_residue(p_arg, alpha)
        if pow(quadr_res, 2, p_arg) != 1:
            return quadr_res


def primitive_root_from_another(prim_root, p):
    while True:
        exp = random.randint(3, p - 2)
        if number.GCD(exp, p - 1) == 1:
            return exp, pow(prim_root, exp, p)


def generate_permutation(n):
    index_list = [value for value in range(1, n + 1)]
    random.shuffle(index_list)
    return index_list


def generate_prices(price_range, max_price):
    prices = []
    division = max_price / price_range
    for iterator in range(price_range):
        prices.append(max_price - division * iterator)
    prices.reverse()
    return prices
