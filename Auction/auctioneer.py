import pickle
import socket
import time
import sys
sys.path.append('../')
from _thread import *
from hashlib import sha256

from Encryption import elgamal
from Parse import parse
from Proofs import zkp
from Utils import algorithms as alg, utils

global p, g, z, h, M, price_range, max_price, prices, product

host = '127.0.0.1'
port = 5600
bidder_number = 1
bidders_integrals = []
superimposition = []
winners = []
winning_price_index = -1
end_of_search_winning_price_flag = False
end_of_search_no_winning_price_flag = False
winners_received_flag = False
auction_ended_flag_list = []
end_of_comms_flag = False


def input_parameter(user_message, variable_name, interval):
    variable = int(input(user_message))
    while variable < interval[0] or variable > interval[1]:
        variable = int(
            input(variable_name + " must be between " + str(interval[0]) + " and " + str(interval[1]) + ": "))
    return variable


def compute_product_zkp_prerequisites(bidder_differential):
    first_product = 1
    second_product = 1
    for (first_ciphertext, second_ciphertext) in bidder_differential:
        first_product = (first_product * first_ciphertext) % p
        second_product = (second_product * second_ciphertext) % p

    return first_product, second_product


def compute_challenge(first_ciphertext, second_ciphertext, first_commitment, second_commitment, plaintext):
    hash_object = sha256(
        utils.num_concat(g, h, first_ciphertext, (second_ciphertext * pow(plaintext, -1, p)) % p, first_commitment,
                         second_commitment))
    return int(hash_object.hexdigest(), 16)


def compute_integral(bidder_differential):
    bidder_integral = []
    for index, value in enumerate(list(reversed(bidder_differential))):
        if index == 0:
            bidder_integral.append(value)
        else:
            cipher1 = (value[0] * bidder_integral[index - 1][0]) % p
            cipher2 = (value[1] * bidder_integral[index - 1][1]) % p
            bidder_integral.append((cipher1, cipher2))
    return bidder_integral


def compute_superimposition():
    global superimposition
    for bidding_index in range(0, price_range):
        product_cipher_1 = 1
        product_cipher_2 = 1
        for bidder_index in range(0, len(bidders_integrals)):
            product_cipher_1 = (product_cipher_1 * bidders_integrals[bidder_index][bidding_index][0]) % p
            product_cipher_2 = (product_cipher_2 * bidders_integrals[bidder_index][bidding_index][1]) % p
        superimposition.append((product_cipher_1, product_cipher_2))
    print("Superimposition is", superimposition)


def compute_set():
    power_set = []
    for exponent in range(0, M + 1):
        y, ciphertext1, ciphertext2 = elgamal.encrypt(p, g, h, pow(z, exponent, p))
        power_set.append((ciphertext1, ciphertext2))
    return power_set


def binary_search(connection, left_limit, right_limit):
    global end_of_search_winning_price_flag, end_of_search_no_winning_price_flag
    next_element_match_response = False

    middle_index = left_limit + (right_limit - left_limit) // 2
    middle_element = superimposition[middle_index]
    print(middle_element)
    connection.send(pickle.dumps(middle_element))

    current_element_match_response = connection.recv(1024).decode() == "True"
    if not current_element_match_response:
        next_element = superimposition[middle_index + 1]
        print(next_element)
        next_element_pickled = pickle.dumps(next_element)
        connection.send(next_element_pickled)
        next_element_match_response = connection.recv(1024).decode() == "True"
        if not next_element_match_response:
            left_limit = middle_index + 1
        else:
            end_of_search_winning_price_flag = True
    elif current_element_match_response:
        right_limit = middle_index - 1

    if middle_index == len(superimposition) - 2 and not next_element_match_response:
        end_of_search_no_winning_price_flag = True

    return left_limit, right_limit


def receive_winners(connection, middle_index):
    global winning_price_index, winners_received_flag, winners
    winning_price_index = middle_index
    check_winners = [value[middle_index + 1] for value in bidders_integrals]
    connection.send(pickle.dumps(check_winners))
    winners = pickle.loads(connection.recv(1024))
    winners_received_flag = connection.recv(1024).decode() == "True"
    if winners:
        with open("../Bulletin Board/bulletin_board.txt", "a") as f:
            f.write("Winning price is: " + "${:.2f}".format(prices[winning_price_index]) + "\n")
        with open("../Bulletin Board/bulletin_board.txt", "a") as f:
            f.write("Winning bidders indexes are: " + str(winners))


def send_draw_message(connection):
    message_draw = "There is no winner because all bidders bid the same price!"
    connection.send(message_draw.encode())


def send_winn_loss_message(connection, bidder_index):
    global winners
    if bidder_index in winners:
        message_winner = "You have won! The winning price you have to pay is " + "${:.2f}".format(
            prices[winning_price_index]) + "."
        connection.send(message_winner.encode())
    else:
        message_loser = "Your bid was not high enough! Better luck next time!"
        connection.send(message_loser.encode())


def write_auction_configurations():
    global prices
    with open("../Bulletin Board/bulletin_board.txt", "w") as f:
        if product == "Shoes":
            f.write("Products auctioned: " + str(M) + " pairs of " + product.lower() + "\n")
        else:
            f.write("Products auctioned: " + str(M) + " " + product.lower() + "\n")
        f.write("Price range is: " + str(price_range) + "\n")
        prices = alg.generate_prices(price_range, max_price)
        f.write("Price list is: " + str(prices) + "\n")


def check_or_proofs(bidder_differential, bidder_index):
    or_proof_params = parse.extract_tuple_list("OR Proof parameters for bidder", bidder_index)
    for index, ciphertext in enumerate(bidder_differential):
        first_main_commitment = (or_proof_params[index][0] * or_proof_params[index][4]) % p
        second_main_commitment = (or_proof_params[index][1] * or_proof_params[index][5]) % p
        c = compute_challenge(ciphertext[0], ciphertext[1], first_main_commitment, second_main_commitment, z)
        print("OR proof check for client " + str(bidder_index) + " on element " + str(index + 1),
              zkp.check_or_proof(p, g, h, c, or_proof_params[index][3], or_proof_params[index][7],
                                 or_proof_params[index][0],
                                 or_proof_params[index][1],
                                 or_proof_params[index][2],
                                 or_proof_params[index][4], or_proof_params[index][5],
                                 or_proof_params[index][6],
                                 1, z, ciphertext[0], ciphertext[1]))


def threaded_client(connection, bidder_index):
    global bidders_integrals, auction_ended_flag_list
    connection.send(str.encode('[Auctioneer]: Welcome to the Bid! You are bidder number ' + str(bidder_index)))
    bidder_differential = parse.extract_tuple_list("Encrypted list for bidder", bidder_index)
    first_commitment, second_commitment, response = parse.parse_product_zkp_parameters(
        "Product ZKP parameters for bidder", bidder_index)
    first_ciphertext, second_ciphertext = compute_product_zkp_prerequisites(bidder_differential)
    c = compute_challenge(first_ciphertext, second_ciphertext, first_commitment, second_commitment, z)
    print("Product non-interactive zkp for bidder " + str(bidder_index),
          zkp.check_enc_auth(p, g, h, c, response, first_commitment, second_commitment, first_ciphertext,
                             second_ciphertext, z))

    # ZKP for delta_b_j,i = E(1) OR delta_b_j,i = E(z)
    check_or_proofs(bidder_differential, bidder_index)

    bidder_integral = compute_integral(bidder_differential)
    bidders_integrals[bidder_index - 1] = list(reversed(bidder_integral))

    while not end_of_comms_flag:
        continue

    if len(bidders_integrals) <= M:
        connection.send("Auction aborted because of lack of bidders!".encode())
    else:
        while not end_of_search_no_winning_price_flag and not (
                end_of_search_winning_price_flag and winners_received_flag):
            continue

        if end_of_search_no_winning_price_flag:
            send_draw_message(connection)

        if end_of_search_winning_price_flag:
            if not winners:
                send_draw_message(connection)
            else:
                send_winn_loss_message(connection, bidder_index)

    auction_ended_flag_list[bidder_index - 1] = True
    connection.close()


def authority_thread(connection):
    global winning_price_index, winners, winners_received_flag
    global end_of_search_no_winning_price_flag, end_of_search_winning_price_flag, superimposition

    connection.send(str.encode('[Auctioneer]: Welcome to the Bid\n'))
    authority_reply = connection.recv(2048).decode()
    print(authority_reply)

    while not end_of_comms_flag or bidders_integrals.count([]) != 0:
        continue

    if len(bidders_integrals) <= M:
        connection.send(pickle.dumps("Auction aborted because of lack of bidders!"))
    else:
        compute_superimposition()

        # Mix and match
        left_limit = 0
        right_limit = price_range - 1

        while not end_of_search_winning_price_flag and not end_of_search_no_winning_price_flag:
            # Set computation
            power_set = compute_set()
            connection.send(pickle.dumps(power_set))
            # Binary search
            left_limit, right_limit = binary_search(connection, left_limit, right_limit)
            connection.send(pickle.dumps((end_of_search_winning_price_flag, end_of_search_no_winning_price_flag)))

        if end_of_search_winning_price_flag:
            receive_winners(connection, left_limit + (right_limit - left_limit) // 2)
    connection.close()


def communication(connection):
    global p, g, h, z, bidder_number

    print('Waiting for a connection..')
    connection.listen(5)

    start = time.time()
    end = time.time()
    while end - start < 80:
        try:
            client, address = connection.accept()
        except socket.timeout:
            end = time.time()
            continue

        full_address = address[0] + ':' + str(address[1])
        print('Connected to: ', full_address)
        if full_address == '127.0.0.1:5100':
            print("Hello, mr authority")
            start_new_thread(authority_thread, (client,))
            p, g, h, z = parse.take_parameters()
        else:
            start_new_thread(threaded_client, (client, bidder_number,))
            bidders_integrals.append([])
            bidder_number += 1
        end = time.time()
