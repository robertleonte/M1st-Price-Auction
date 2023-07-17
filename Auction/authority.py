import pickle
import time
import sys
sys.path.append('../')
from Crypto.Util import number

from Communication import comms
from Encryption import elgamal
from Utils import algorithms as alg, utils

global p, g, z, h, x
host = '127.0.0.1'
auctioneer_port = 5600
auctioneer_com_port = 5100
mixing_port = 5200
mixing_com_port = 5700
M = 2
ciphertexts = []
end_of_search_flag = False


def preparation():
    global p, g, z
    p = number.getStrongPrime(1024)
    g = alg.primitive_root(p)
    z = alg.primitive_root_from_another(g, p)[1]
    with open("../Bulletin Board/bulletin_board.txt", "a") as f:
        f.write("Group order (Zp) is: " + str(p) + "\n")
        f.write("Cyclic group generator g is: " + str(g) + "\n")
        f.write("Cyclic group generator z is: " + str(z) + "\n")


def generate_key():
    global x, h
    x, h = alg.primitive_root_from_another(g, p)
    with open("../Bulletin Board/bulletin_board.txt", "a") as f:
        f.write("Public key is: " + str(h) + "\n")


def compute_division(element):
    division_list = []
    for ciphertext in ciphertexts:
        division_cipher1 = (element[0] * pow(ciphertext[0], -1, p)) % p
        division_cipher2 = (element[1] * pow(ciphertext[1], -1, p)) % p
        random_factor = utils.generate_random_factor(p)
        division_list.append((pow(division_cipher1, random_factor, p), pow(division_cipher2, random_factor, p)))
    return division_list


def check_match(response):
    for value in response:
        plaintext = elgamal.decrypt(value[0], value[1], p, x)
        if plaintext == 1:
            return True
    return False


def search_element(connection, element):
    check_list = compute_division(element)
    print("Ciphertexts to be mixed first time", check_list)
    connection.send(pickle.dumps(check_list))
    response = pickle.loads(connection.recv(4096))
    print("Response for first mixing is", response)
    match_found = check_match(response)
    return match_found


def find_winners(check_winners_list):
    winners_list = []
    for index, value in enumerate(check_winners_list):
        plaintext = elgamal.decrypt(value[0], value[1], p, x)
        if plaintext == z:
            winners_list.append(index + 1)
    return winners_list


def send_winners(connection):
    check_winners_list = pickle.loads(connection.recv(4096))
    winners_list = find_winners(check_winners_list)
    print("Winners list", winners_list)
    connection.send(pickle.dumps(winners_list))
    time.sleep(1)
    connection.send(str.encode(str(True)))


def communication(first_connection, second_connection):
    global end_of_search_flag, ciphertexts

    print(first_connection.recv(1024).decode())
    first_connection.send(str.encode("Thanks glad to be here!"))

    preparation()
    generate_key()

    end_of_search_winning_price_flag = False
    while not end_of_search_flag:
        ciphertexts = pickle.loads(first_connection.recv(4096))
        if ciphertexts == "Auction aborted because of lack of bidders!":
            end_of_search_flag = True
            end_of_search_winning_price_flag = False
            continue

        middle_element = pickle.loads(first_connection.recv(4096))
        match_found = search_element(second_connection, middle_element)
        first_connection.send(str.encode(str(match_found)))

        if not match_found:
            next_element = pickle.loads(first_connection.recv(4096))
            match_found = search_element(second_connection, next_element)
            first_connection.send(str(match_found).encode())
        end_of_search_winning_price_flag, end_of_search_no_winning_price_flag = pickle.loads(
            first_connection.recv(1024))
        if end_of_search_winning_price_flag or end_of_search_no_winning_price_flag:
            end_of_search_flag = True

    second_connection.send(pickle.dumps("Search completed"))

    # check winners
    if end_of_search_winning_price_flag:
        send_winners(first_connection)


if __name__ == "__main__":
    client_socket = comms.prepare_client_socket(host, auctioneer_com_port, auctioneer_port)
    mixing_socket = comms.prepare_client_socket(host, mixing_com_port, mixing_port)
    communication(client_socket, mixing_socket)
    mixing_socket.close()
    client_socket.close()
