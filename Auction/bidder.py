import time
import sys
sys.path.append('../')

from Encryption import elgamal
from Parse import parse
from Proofs import zkp

global p, g, z, h, price_range, prices, final_message

host = '127.0.0.1'
port = 5600
bid_differential = []
random_parameters = []
price_index = -1


def take_parameters():
    global p, g, z, h, price_range, prices
    price_range = parse.extract_parameters("Price range")
    prices = parse.extract_list("Price list")
    p, g, h, z = parse.take_parameters()


def compute_differential():
    global bid_differential
    for i in range(0, price_range):
        if i == price_index - 1:
            y, c1, c2 = elgamal.encrypt(p, g, h, z)
            bid_differential.append((c1, c2))
            random_parameters.append(y)
        else:
            y, c1, c2 = elgamal.encrypt(p, g, h, 1)
            bid_differential.append((c1, c2))
            random_parameters.append(y)


def compute_random_parameters_sum():
    sum_random_parameters = 0
    for random_parameter in random_parameters:
        sum_random_parameters = (sum_random_parameters + random_parameter) % (p - 1)
    return sum_random_parameters


def compute_log_arguments(plaintext):
    global bid_differential
    first_product = 1
    second_product = 1
    for (first_ciphertext, second_ciphertext) in bid_differential:
        first_product = (first_product * first_ciphertext) % p
        second_product = (second_product * second_ciphertext) % p

    return first_product, (second_product * pow(plaintext, -1, p)) % p


def write_differential(my_number):
    with open("../Bulletin Board/bulletin_board.txt", "a") as f:
        f.write("Encrypted list for bidder " + str(my_number) + ": " + str(bid_differential) + "\n")


def write_product_zkp_parameters(first_commitment, second_commitment, response, bidder_index):
    with open("../Bulletin Board/bulletin_board.txt", "a") as f:
        f.write("Product ZKP parameters for bidder " + str(bidder_index) + ": " + str(
            (first_commitment, second_commitment, response)) + "\n")


def write_or_proof_parameters(or_proof_params, bidder_index):
    with open("../Bulletin Board/bulletin_board.txt", "a") as f:
        f.write("OR Proof parameters for bidder " + str(bidder_index) + ": " + str(or_proof_params) + "\n")


def generate_or_proof_parameters_list():
    or_proof_parameters = []
    for index, ciphertext in enumerate(bid_differential):
        if index == price_index - 1:
            first_commit_sim, second_commit_sim, response_sim, c1, first_commit_true, second_commit_true, response_true, \
                c2 = zkp.generate_or_proof_parameters(p, g, h, random_parameters[index], ciphertext[0], ciphertext[1], 1, z)
            or_proof_parameters.append(
                (first_commit_sim, second_commit_sim, response_sim, c1, first_commit_true, second_commit_true,
                 response_true, c2))
        else:
            first_commit_sim, second_commit_sim, response_sim, c1, first_commit_true, second_commit_true, response_true, \
                c2 = zkp.generate_or_proof_parameters(p, g, h, random_parameters[index], ciphertext[0], ciphertext[1], z, z)
            or_proof_parameters.append(
                (first_commit_true, second_commit_true, response_true, c2, first_commit_sim, second_commit_sim,
                 response_sim, c1))

    return or_proof_parameters


def configure_output_label(message, output_label):
    output_label.setText(final_message)
    if message == "Your bid was not high enough! Better luck next time!" or message == "Auction aborted because of lack of bidders!" or message == "There is no winner because all bidders bid the same price!":
        output_label.setStyleSheet("border: 3px solid red;")
    elif "You have won!" in message:
        output_label.setStyleSheet("border: 3px solid green;")
    output_label.setVisible(True)


def auctioneer_com(connection, output_label):
    global final_message
    message = connection.recv(1024).decode()
    print(message)
    my_number = int(message[-1])

    while price_index < 0:
        time.sleep(2)

    compute_differential()

    write_differential(my_number)
    first_log_argument, second_log_argument = compute_log_arguments(z)
    sum_random_parameters = compute_random_parameters_sum()

    # ZKP for delta_b_1,i * delta_b_2,i * .. * delta_b_price_range,i = E(z)

    first_commitment, second_commitment, response = zkp.generate_logarithms_equality_parameters(p, g, h,
                                                                                                sum_random_parameters,
                                                                                                first_log_argument,
                                                                                                second_log_argument)
    write_product_zkp_parameters(first_commitment, second_commitment, response, my_number)
    # ZKP for delta_b_j,i = E(1) OR delta_b_j,i = E(z)
    or_proof_parameters = generate_or_proof_parameters_list()
    write_or_proof_parameters(or_proof_parameters, my_number)
    # Final message
    final_message = connection.recv(1024).decode()
    configure_output_label(final_message, output_label)
