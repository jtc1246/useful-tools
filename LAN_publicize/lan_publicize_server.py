import socket
from _thread import start_new_thread
from time import sleep

# Set your ports here
PUBLIC_PORT = 10005  # public users to access
CONNECT_PORT = 10010  # LAN device to connect

# Ignore these
ALLOWED_IP = ''
AVAILABLE_SOCKETS = []

def listen_connect_port():
    global ALLOWED_IP
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', CONNECT_PORT))
    server.listen(100)
    print(f'[*] Connection port from LAN device: {CONNECT_PORT}')
    
    while True:
        client_socket, addr = server.accept()
        if (ALLOWED_IP == ''):
            ALLOWED_IP = addr[0]
        if (ALLOWED_IP != addr[0]):
            return
        print(f'Received connection from LAN device, {addr[0]}:{addr[1]}')
        AVAILABLE_SOCKETS.append(client_socket)

def forward(source, target):
    while True:
        data = source.recv(1024)
        if not data:
            break
        target.send(data)

def handle_connection(user_socker, remote_socket):
    start_new_thread(forward, (user_socker, remote_socket))
    start_new_thread(forward, (remote_socket, user_socker))
    

def listen_public_port():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', PUBLIC_PORT))
    server.listen(100)
    print(f'[*] Public port: {PUBLIC_PORT}')
    
    while True:
        client_socket, addr = server.accept()
        print(f'Received connection from public network, {addr[0]}')
        try:
            remote_socket = AVAILABLE_SOCKETS.pop()
            start_new_thread(handle_connection, (client_socket, remote_socket))
        except:
            pass


start_new_thread(listen_connect_port, ())
start_new_thread(listen_public_port, ())

while (True):
    sleep(10)
