import pickle
import sys
sys.path.append('../')

from _thread import *
from copy import deepcopy
from hashlib import sha256
from Crypto.Random import random
from Communication import comms
from Parse import parse
from Proofs import zkp
from Utils import utils
global p, g, h

host = '127.0.0.1'
port = 5200
client_number = 1
ciphertexts = []
flag_list = [False, False, False]
match_flag = False
auctioneer_flag = False
thread_ended_flags = [False, False, False]


def take_parameters():
    global p, g, h
    p = parse.extract_parameters("Group order")
    g = parse.extract_parameters("Cyclic group generator g")
    h = parse.extract_parameters("Public key")


def subset(n):
    index_list = [value for value in range(1, n + 1)]
    return random.sample(index_list, 2)


def receive_mixed_subset(connection):
    subset_check = subset(len(ciphertexts))
    connection.send(pickle.dumps(subset_check))
    subset_mixed = pickle.loads(connection.recv(1024))
    return subset_check, subset_mixed


def compute_zkp_log_arguments(subset_check, subset_mixed, initial_ciphertexts):
    gamma = 1
    delta = 1
    for value in subset_check:
        gamma = (gamma * initial_ciphertexts[value - 1][0]) % p
        delta = (delta * initial_ciphertexts[value - 1][1]) % p

    print("gamma is", gamma)
    print("delta is", delta)
    gamma_prime = 1
    delta_prime = 1
    for value in subset_mixed:
        gamma_prime = (gamma_prime * ciphertexts[value - 1][0]) % p
        delta_prime = (delta_prime * ciphertexts[value - 1][1]) % p

    print("gamma prime", gamma_prime)
    print("delta prime", delta_prime)
    first_ciphertext = (gamma_prime * pow(gamma, -1, p)) % p
    second_ciphertext = (delta_prime * pow(delta, -1, p)) % p
    return first_ciphertext, second_ciphertext


def compute_challenge(first_log_arg, second_log_arg, first_commitment, second_commitment):
    hash_object = sha256(utils.num_concat(g, h, first_log_arg, second_log_arg, first_commitment, second_commitment))
    return int(hash_object.hexdigest(), 16)


def client_thread(connection, client_index):
    global ciphertexts, flag_list
    message = "Hello! You will be mixing client number " + str(client_index)
    connection.send(message.encode())
    while not match_flag:
        while True:
            if match_flag:
                break
            if type(ciphertexts) == list and len(ciphertexts) != 0 and not flag_list[client_index - 1]:
                if client_index == 1 or (client_index > 1 and flag_list[client_index - 2]):
                    break

        if match_flag:
            connection.send(pickle.dumps(str(match_flag)))
            continue

        initial_ciphertexts = deepcopy(ciphertexts)
        connection.send(pickle.dumps(ciphertexts))
        ciphertexts = pickle.loads(connection.recv(4096))
        print("Mixed ciphertexts from client " + str(client_index), ciphertexts)

        # checking
        subset_check, subset_mixed = receive_mixed_subset(connection)
        first_log_argument, second_log_argument = compute_zkp_log_arguments(subset_check, subset_mixed,
                                                                            initial_ciphertexts)
        first_commitment, second_commitment, response = parse.parse_product_zkp_parameters(
            "Product ZKP parameters for mixing client", client_index)
        c = compute_challenge(first_log_argument, second_log_argument, first_commitment, second_commitment)

        check_response = zkp.check_logarithm_equality(p, g, h, c, response, first_commitment,
                                                      second_commitment, first_log_argument,
                                                      second_log_argument)
        print("Response for zkp for re-encryption is", check_response)
        flag_list[client_index - 1] = check_response

    thread_ended_flags[client_index - 1] = True


def authority_com(connection):
    global auctioneer_flag, ciphertexts, match_flag, flag_list
    auctioneer_flag = True
    take_parameters()
    while not match_flag:
        ciphertexts = pickle.loads(connection.recv(4096))
        print("Ciphertexts received from the authority", ciphertexts)
        if ciphertexts == "Search completed":
            match_flag = True
            continue
        flag_list = [False, False, False]
        while True:
            if flag_list[0] and flag_list[1] and flag_list[2]:
                break
        connection.send(pickle.dumps(ciphertexts))


def communication(connection):
    global client_number, auctioneer_flag, ciphertexts, flag_list, match_flag
    connection.listen(1)
    print("I am listening")
    while not auctioneer_flag:
        conn, address = connection.accept()
        full_address = address[0] + ':' + str(address[1])
        print('Connected to: ', full_address)
        if full_address == '127.0.0.1:5700':
            authority_com(conn)
        else:
            start_new_thread(client_thread, (conn, client_number))
            client_number += 1


if __name__ == "__main__":
    mix_socket = comms.prepare_server_socket(host, port, None)
    communication(mix_socket)
    while thread_ended_flags.count(True) != 3:
        continue
    mix_socket.close()
