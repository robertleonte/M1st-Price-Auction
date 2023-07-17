import errno
import socket
from socket import error as socket_error


def prepare_client_socket(host, client_port, connecting_port):
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        connection.bind((host, client_port))
    except socket.error as e:
        print(str(e))

    try:
        connection.connect((host, connecting_port))
    except socket.error as e:
        print(str(e))
    return connection


def prepare_client_socket_no_binding(host, connecting_port):
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        connection.connect((host, connecting_port))
    except socket_error as e:
        if e.errno == errno.ECONNREFUSED:
            exit("Bid subscription phase has ended!")
        else:
            print(str(e))
    return connection


def prepare_server_socket(host, port, timeout_interval):
    connection = socket.socket()
    try:
        connection.bind((host, port))
    except socket.error as e:
        print(str(e))

    connection.settimeout(timeout_interval)
    return connection
