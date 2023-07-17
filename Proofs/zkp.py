from hashlib import sha256

from Utils import utils


def compute_hash(g, h, first_log_arg, second_log_arg, first_commitment, second_commitment):
    hash_object = sha256()
    hash_object.update(utils.num_concat(g, h, first_log_arg, second_log_arg, first_commitment, second_commitment))
    c = int(hash_object.hexdigest(), 16)
    return c


def generate_commitments(p, g, h):
    r = utils.generate_random_factor(p)
    first_commitment = pow(g, r, p)
    second_commitment = pow(h, r, p)
    return r, first_commitment, second_commitment


def generate_response(p, c, y, r):
    response = (c * y + r) % (p - 1)
    return response


def generate_logarithms_equality_parameters(p, g, h, y, first_log_arg, second_log_arg):
    r, first_commitment, second_commitment = generate_commitments(p, g, h)
    c = compute_hash(g, h, first_log_arg, second_log_arg, first_commitment, second_commitment)
    response = (c * y + r) % (p - 1)
    return first_commitment, second_commitment, response


def generate_logarithms_equality_parameters_sim(p, g, h, c, first_ciphertext, second_ciphertext, plaintext):
    response = utils.generate_random_factor(p)
    first_commitment = (pow(g, response, p) * pow(pow(first_ciphertext, c, p), -1, p)) % p
    second_commitment = (pow(h, response, p) * pow(pow((second_ciphertext * pow(plaintext, -1, p)) % p, c, p), -1,
                                                   p)) % p
    return first_commitment, second_commitment, response


def generate_or_proof_parameters(p, g, h, y, first_ciphertext, second_ciphertext, plaintext, plaintexts_product):
    c1 = utils.generate_random_factor(p)
    first_commit_sim, second_commit_sim, response_sim = generate_logarithms_equality_parameters_sim(p, g, h, c1,
                                                                                                    first_ciphertext,
                                                                                                    second_ciphertext,
                                                                                                    plaintext)
    r, first_commit_true, second_commit_true = generate_commitments(p, g, h)
    c = compute_hash(g, h, first_ciphertext, (second_ciphertext * pow(plaintexts_product, -1, p)) % p,
                     (first_commit_sim * first_commit_true) % p, (second_commit_sim * second_commit_true) % p)
    c2 = (c - c1) % p
    response_true = generate_response(p, c2, y, r)
    return first_commit_sim, second_commit_sim, response_sim, c1, first_commit_true, second_commit_true, response_true, c2


def check_enc_auth(p, g, h, c, response, first_commitment, second_commitment, first_ciphertext,
                   second_ciphertext, plaintext):
    second_log_argument = (second_ciphertext * pow(plaintext, -1, p)) % p
    return check_logarithm_equality(p, g, h, c, response, first_commitment, second_commitment, first_ciphertext,
                                    second_log_argument)


def check_logarithm_equality(p, g, h, c, response, first_commitment, second_commitment, first_log_argument,
                             second_log_argument):
    first_left_term = pow(g, response, p)
    first_right_term = (pow(first_log_argument, c, p) * first_commitment) % p
    second_left_term = pow(h, response, p)
    second_right_term = (pow(second_log_argument, c, p) * second_commitment) % p
    if first_left_term == first_right_term and second_left_term == second_right_term:
        return True
    else:
        return False


def check_or_proof(p, g, h, challenge, first_challenge, second_challenge, first_commitment_first_plaintext,
                   second_commitment_first_plaintext,
                   response_first_plaintext,
                   first_commitment_second_plaintext, second_commitment_second_plaintext, response_second_plaintext,
                   first_plaintext, second_plaintext, first_ciphertext, second_ciphertext):
    if check_enc_auth(p, g, h, first_challenge, response_first_plaintext, first_commitment_first_plaintext,
                      second_commitment_first_plaintext, first_ciphertext, second_ciphertext, first_plaintext) and \
            check_enc_auth(p, g, h, second_challenge, response_second_plaintext,
                           first_commitment_second_plaintext, second_commitment_second_plaintext,
                           first_ciphertext, second_ciphertext, second_plaintext) and \
            (first_challenge + second_challenge) % p == challenge % p:
        return True
    else:
        return False

