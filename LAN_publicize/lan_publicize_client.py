import socket
from _thread import start_new_thread
from time import sleep

# Set server and ports here
SERVER = 'jtc1246.com'  # Server IP or domain
SERVER_PORT = 10010  # Server port
LOCAL_PORT = 10005  # Local port to make public

# Ignore this
AVAILABLE_SOCKETS_NUM = 0

def start_connecions():
    global AVAILABLE_SOCKETS_NUM
    while (True):
        if (AVAILABLE_SOCKETS_NUM >= 10):
            sleep(0.1)
            continue
        print('Creating new connection')
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((SERVER, SERVER_PORT))
            start_new_thread(handle_socket, (s,))
            AVAILABLE_SOCKETS_NUM += 1
        except:
            pass

def forward(source, target):
    while True:
        data = source.recv(1024)
        if not data:
            break
        target.send(data)

def handle_connection(user_socker, remote_socket):
    start_new_thread(forward, (user_socker, remote_socket))
    start_new_thread(forward, (remote_socket, user_socker))


def handle_socket(s):
    global AVAILABLE_SOCKETS_NUM
    try:
        data = s.recv(1024)
    except:
        AVAILABLE_SOCKETS_NUM -= 1
        return
    if (data == b''):
        return
    AVAILABLE_SOCKETS_NUM -= 1
    print('Received data')
    local_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    local_socket.connect(('127.0.0.1', LOCAL_PORT))
    local_socket.send(data)
    start_new_thread(handle_connection, (local_socket, s))
    
start_new_thread(start_connecions, ())
while True:
    sleep(10)
