import os
import pathlib
import sys
sys.path.append('../')


from Crypto.Random import random


def generate_random_factor(p):
    random_factor = random.randint(3, p - 2)
    while (p - 1) % random_factor == 0:
        random_factor = random.randint(3, p - 2)
    return random_factor


def num_concat(*numbers):
    result = ""
    for number in numbers:
        number_string = str(number)
        result += number_string + str(len(number_string))
    return result.encode()


def check_number(text):
    try:
        float(text)
    except ValueError:
        return False
    return True


def find_image(folder_name, keyword):
    for element in pathlib.Path(folder_name).iterdir():
        if keyword[:-2] in element.name:
            return os.path.join(os.path.dirname(element), element.name)
