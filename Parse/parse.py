def extract_parameters(text):
    index = -1
    while index == -1:
        with open("../Bulletin Board/bulletin_board.txt", "r") as f:
            for line in f:
                index = line.find(text)
                if index != -1:
                    return extract_end_number(line)


def extract_end_number(text):
    number_string = text.split(" ")[-1]
    if "." in number_string:
        number = float(number_string)
    else:
        number = int(number_string)
    return number


def extract_tuple_list(text, bidder_number):
    index = -1
    while index == -1:
        with open("../Bulletin Board/bulletin_board.txt", "r") as f:
            for line in f:
                index = line.find(text + " " + str(bidder_number))
                if index != -1:
                    bid_differential_text = line[index + len(text) + 4:-1]
                    break
    bid_differential = []
    start_index = 0
    while start_index != len(bid_differential_text) - 2:
        start_index = bid_differential_text.find("(", start_index)
        end_index = bid_differential_text.find(")", start_index)
        ciphertexts = tuple([int(element) for element in bid_differential_text[start_index + 1:end_index].split(", ")])
        bid_differential.append(ciphertexts)
        start_index = end_index
    return bid_differential


def extract_list(text):
    index = -1
    while index == -1:
        with open("../Bulletin Board/bulletin_board.txt", "r") as f:
            for line in f:
                index = line.find(text)
                if index != -1:
                    start_index = line.find(":") + 3
                    return [float(elem) for elem in line[start_index:-2].split(", ")]


def parse_product_zkp_parameters(text, number):
    index = -1
    while index == -1:
        with open("../Bulletin Board/bulletin_board.txt", "r") as f:
            lines = reversed(f.readlines())
            for line in lines:
                index = line.find(text + " " + str(number))
                if index != -1:
                    params_text = line[index + len(text) + 4:-1]
                    break

    params = [int(elem) for elem in params_text[1:-1].split(", ")]
    return params[0], params[1], params[2]


def take_parameters():
    p = extract_parameters("Group order")
    g = extract_parameters("Cyclic group generator g")
    z = extract_parameters("Cyclic group generator z")
    h = extract_parameters("Public key")
    return p, g, h, z
