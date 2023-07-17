import pickle
from copy import deepcopy
import sys
sys.path.append('../')
from Communication import comms
from Encryption import elgamal
from Parse import parse
from Proofs import zkp
from Utils import algorithms as alg

global p, g, h
host = '127.0.0.1'
port = 5200
match_flag = False


def take_parameters():
    global p, g, h
    p = parse.extract_parameters("Group order")
    g = parse.extract_parameters("Cyclic group generator g")
    h = parse.extract_parameters("Public key")


def reencrypt(initial_ciphertexts):
    ciphertexts = []
    random_parameters = []

    for ciphertext in initial_ciphertexts:
        y, reenc_cipher1, reenc_cipher2 = elgamal.reencrypt(p, g, h, ciphertext[0], ciphertext[1])
        ciphertexts.append((reenc_cipher1, reenc_cipher2))
        random_parameters.append(y)

    print("Re-encryption list", ciphertexts)
    return ciphertexts, random_parameters


def permute(ciphertexts):
    mix_index_list = alg.generate_permutation(len(ciphertexts))
    ciphertexts_copy = deepcopy(ciphertexts)
    for index in range(0, len(ciphertexts)):
        ciphertexts[index] = ciphertexts_copy[mix_index_list[index] - 1]
    return ciphertexts, mix_index_list


def provide_correspondent_indexes(subset_check, mix_index_list):
    subset_response = []
    for index in subset_check:
        subset_response.append(mix_index_list.index(index) + 1)
    return subset_response


def compute_zkp_log_arguments(subset_check, subset_mixed, initial_ciphertexts, mixed_ciphertexts):
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
        gamma_prime = (gamma_prime * mixed_ciphertexts[value - 1][0]) % p
        delta_prime = (delta_prime * mixed_ciphertexts[value - 1][1]) % p

    print("gamma prime", gamma_prime)
    print("delta prime", delta_prime)
    first_ciphertext = (gamma_prime * pow(gamma, -1, p)) % p
    second_ciphertext = (delta_prime * pow(delta, -1, p)) % p
    return first_ciphertext, second_ciphertext


def compute_parameters_sum(subset_check, random_parameters):
    sum_random_parameters = 0
    for index in subset_check:
        sum_random_parameters += random_parameters[index - 1]
    return sum_random_parameters


def write_zkp_parameters(first_commitment, second_commitment, response, mix_client_index):
    with open("../Bulletin Board/bulletin_board.txt", "a") as f:
        f.write("Product ZKP parameters for mixing client " + str(mix_client_index) + ": " + str(
            (first_commitment, second_commitment, response)) + "\n")


def server_com(connection):
    global match_flag
    message = connection.recv(1024).decode()
    print(message)
    mix_client_index = int(message.split(" ")[-1])

    take_parameters()
    while not match_flag:
        initial_ciphertexts = pickle.loads(connection.recv(4096))

        if initial_ciphertexts == "True":
            match_flag = initial_ciphertexts == "True"
            continue

        ciphertexts, random_parameters = reencrypt(initial_ciphertexts)

        ciphertexts, mix_index_list = permute(ciphertexts)
        connection.send(pickle.dumps(ciphertexts))

        subset_check = pickle.loads(connection.recv(4096))
        subset_response = provide_correspondent_indexes(subset_check, mix_index_list)
        connection.send(pickle.dumps(subset_response))

        #    values computation
        first_log_arg, second_log_arg = compute_zkp_log_arguments(subset_check, subset_response,
                                                                  initial_ciphertexts, ciphertexts)
        sum_random_params = compute_parameters_sum(subset_check, random_parameters)
        first_commitment, second_commitment, response = zkp.generate_logarithms_equality_parameters(p, g, h,
                                                                                                    sum_random_params,
                                                                                                    first_log_arg,
                                                                                                    second_log_arg)
        write_zkp_parameters(first_commitment, second_commitment, response, mix_client_index)


if __name__ == "__main__":
    client_socket = comms.prepare_client_socket_no_binding(host, port)
    server_com(client_socket)
    client_socket.close()
