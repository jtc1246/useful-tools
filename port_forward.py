PORTS = []
SSL_PORTS = []
# ONLY MODIFY HERE
# PORTS.append((8080, '192.168.1.234', 8080)) # (local_port, target_host, target_port)
# SSL_PORTS.append((8081, '192.168.1.100', 8081))


import socket
import threading
from _thread import start_new_thread
from time import sleep
import struct
import traceback

SSL_KEY = '''-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCsvrP5NWE3rl0H
IJQmo+q0wCRWNXaunFG9sTgaoZGb7GzVhcZ21jzqgFUiRC5kQadfBIt0D/1lx/Eu
7DnrD7AMLXJdBzPdEW0kzwOScjZ5WmFApRMQU9BK23Zi5PwYnnbYHUGmaLSztQKE
CxBn/3wAZ4dRn7OUet8nDG+uqhI4nSBbZoDhZ9s5cCTb0sT5oi/VPCAPqd9Dc9hh
w3YnfL5LqLc4EWWE/Ss6huW67iFx/5WrK+0fWXd6YwTw/undzVqUWFmUpwOVPO3i
CyGgB58qLwnrc5Qg2iaL5kUt/4R1g+EzQg/ii+E1uv8OZyQfr6kHmYYEesMXHyTu
HlHYSMQtAgMBAAECggEAALYM6YsE6FH36THFyi7/0kU8SqjDNRvvJ9Vlo/gR8GyJ
R5tTgTRTE+KSG2rM06tJls7X1OcGD2Ok686uF6AvZtfU/GCOGMwthI19rspN9zod
gZxqlKWcIJ95f5uJN0cQIBt3qLE+pPjbcP0VZ63L//sde1hj6WIKk4ZLCCP1/rKV
vIY+/jT+w62CYqqR5+ssh1sWAHTz7VFhcrUtMLynmZUz1/RXmaEBNQLFo2yMNdSz
5IDbCh6N3Le0THUO+N801xG2KPCl82MAyx319B0RhaboaoS6bVH5SypDgyTqHFZ0
u8x9iwuiFdZP8uEXYtL6H6f+qvPtCnVQOCogsxsICQKBgQDjkzke6/bgWJPU/46/
r9c2iFSeJslMuO4fGynGu3l1eeVvyZtarGMxsnX1absySSigsZA6fDQ2PxdrqxWi
LtydKDNGkqwK02qUugS6vXsqJNrbu6b4zbB6T2mJ/lMBrm6dmGIZCaQyJxvSFiM0
3iLyPI6CndzPcWCMQ0/CvFMt9QKBgQDCUkU25JbJu0CW/E+1I/6EC2RYYzrN4kJd
eRlc45imLdPJESMrhRn+9Pq8ZYoCC+x4AMd1QjFZbvzj6sq0KGqJgsCxajYYWQE3
Bn0vq1Rx+cAjs/t4KlhBJqVNEqUH/eFcmmogoHg/J8z+PZsGwe4TVZ0C2X6IyF/R
89dL1u5iWQKBgEHXaXJR0LZtyi+Y1KMO69QiM2EiVaE16+biA/80ZFqhrsjd6m2c
bIKHYGtlcLyGwBNl7BWPs8dyD4OeFv86UafCZrtnWhEzw6VOAGpKweSajxt9ujxH
vmRUr3M2OqvE3MoJuXAHAxNjj0AEGaGFF1VAQfb2V1lJMybBnsT3mZU1AoGAenXI
YriaAlW8dapaPQiK/AIF4eHfDCKbujZ38l8IMynMPvlK1cFSyabvYM0ItRN4mYO8
Lzxgx0C3pJax2elignhhIS2TG7Lzng6708/ALve6y4VAY9EjvyMwpyqp0CiB3o79
dMRMI1jcyhhe21pZw9t/UG1qXZ8RK8nkk0nG/zkCgYEA2b36Gs5xcueSDc7ghYSM
zWg8nasZ0UFYdFEc/yVpj6RCeoGWlzmpxVyIodb5mNn71/CNsWMWITLliV7oBd+0
czFysER2k43sVPMSrWBRNhyHMnoV5c+nxHXY9y2bOKo/3MMULHMV7gdJ175ZR0A8
4MhQuQu1nnTFHFFlEpWiFVQ=
-----END PRIVATE KEY-----
'''

SSL_CERT = '''-----BEGIN CERTIFICATE-----
MIIDbTCCAlWgAwIBAgIUYadH/k25RZ8fip4WN19BLCAJcAwwDQYJKoZIhvcNAQEL
BQAwRTELMAkGA1UEBhMCQVUxEzARBgNVBAgMClNvbWUtU3RhdGUxITAfBgNVBAoM
GEludGVybmV0IFdpZGdpdHMgUHR5IEx0ZDAgFw0yNTEwMjQxNDE1MzVaGA8yMTI1
MDkzMDE0MTUzNVowRTELMAkGA1UEBhMCQVUxEzARBgNVBAgMClNvbWUtU3RhdGUx
ITAfBgNVBAoMGEludGVybmV0IFdpZGdpdHMgUHR5IEx0ZDCCASIwDQYJKoZIhvcN
AQEBBQADggEPADCCAQoCggEBAKy+s/k1YTeuXQcglCaj6rTAJFY1dq6cUb2xOBqh
kZvsbNWFxnbWPOqAVSJELmRBp18Ei3QP/WXH8S7sOesPsAwtcl0HM90RbSTPA5Jy
NnlaYUClExBT0ErbdmLk/BiedtgdQaZotLO1AoQLEGf/fABnh1Gfs5R63ycMb66q
EjidIFtmgOFn2zlwJNvSxPmiL9U8IA+p30Nz2GHDdid8vkuotzgRZYT9KzqG5bru
IXH/lasr7R9Zd3pjBPD+6d3NWpRYWZSnA5U87eILIaAHnyovCetzlCDaJovmRS3/
hHWD4TNCD+KL4TW6/w5nJB+vqQeZhgR6wxcfJO4eUdhIxC0CAwEAAaNTMFEwHQYD
VR0OBBYEFNj5t9d0aOs4UY9B3Rkku/iEzoVzMB8GA1UdIwQYMBaAFNj5t9d0aOs4
UY9B3Rkku/iEzoVzMA8GA1UdEwEB/wQFMAMBAf8wDQYJKoZIhvcNAQELBQADggEB
AAZTr39getDjZrtrrv1g6fNEmDcQq4/3bP+51q6j2DwgJip1pL7Ju8OmcLcD+gpO
N99kSHUihEle73x+fEuu0NPMwRqyjL1uJlQqUcVz+j0NngTUf2XeQ8iysTlfpgBg
wrz+oRgPupP3xdDj/dRMH3wBDM8vzQH4/1g90Uag2GCW+Ai+O8xuAu7lWViIdMkS
NuluOqC6oc5DnZk8l+XOBdZhg2x1Tg2f1T8ak/7eIRNUF05OCB9/RhJOL7WlzKSl
OCnZTF8kCMTNFTW1oaMUlKHiOFkALXujuPBA+KDQ6B2q/e+c/ak4wJDJUp9m0WJm
NuTXim1jmQzaSyEhb28kw3A=
-----END CERTIFICATE-----
'''


if (len(SSL_PORTS) > 0):
    import os, ssl
    file_path = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(f'{file_path}/.pf_ssl_tmp', exist_ok=True)
    with open(f'{file_path}/.pf_ssl_tmp/pf_ssl.key', 'w') as f:
        f.write(SSL_KEY)
    with open(f'{file_path}/.pf_ssl_tmp/pf_ssl.crt', 'w') as f:
        f.write(SSL_CERT)
    

def force_close(sock: socket.socket):
    """
    强制立即关闭 socket，发送 RST 包而不是 FIN
    """
    try:
        linger = struct.pack('ii', 1, 0)  # 启用 SO_LINGER，timeout=0 秒，立即重置连接
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, linger)
    except Exception as e:
        pass
    try:
        sock.close()
    except:
        pass


def forward(client_socket: socket.socket, target_socket: socket.socket, direction: int):
    src, dest = None, None
    if (direction == 0):
        src, dest = client_socket, target_socket
    else:
        src, dest = target_socket, client_socket
    while True:
        try:
            data = src.recv(1024)
        except: # 让 dest 收到异常
            print(f'Dircetion {direction} src 读取数据失败')
            traceback.print_exc()
            force_close(dest)
            return
        if not data: # 正常关闭 dest
            print(f'Direction {direction} 收到为空, 关闭连接')
            dest.shutdown(socket.SHUT_RDWR)
            return
        try:
            dest.send(data)
        except: # 让 src 收到异常
            print(f'Dircetion {direction} dest 发送数据失败')
            traceback.print_exc()
            force_close(src)
            return


def handle_client(client_socket, target_host, target_port):
    target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        target_socket.connect((target_host, target_port))
    except:
        print(f'建立连接 {target_host}:{target_port} 失败')
        traceback.print_exc()
        force_close(client_socket)
        return

    client_thread = threading.Thread(target=forward, args=(client_socket, target_socket, 0))
    client_thread.start()

    server_thread = threading.Thread(target=forward, args=(client_socket, target_socket, 1))
    server_thread.start()


def start_server(is_ssl: bool, local_host, local_port, target_host, target_port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    server.bind((local_host, local_port))
    server.listen(10000)
    if is_ssl:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile=f'{file_path}/.pf_ssl_tmp/pf_ssl.crt', keyfile=f'{file_path}/.pf_ssl_tmp/pf_ssl.key')
        server = context.wrap_socket(server, server_side=True)
        print(f"[SSL] Listening with SSL on {local_host}:{local_port}")
    else:
        print(f"[*] Listening on {local_host}:{local_port}")

    while True:
        try:
            client_socket, addr = server.accept()
            print(f"[*] Accepted connection from {addr[0]}:{addr[1]}")
            client_thread = threading.Thread(target=handle_client, args=(client_socket, target_host, target_port))
            client_thread.start()
        except:
            pass


def start_all(ports, is_ssl: bool):
    for port in ports:
        start_new_thread(start_server, (is_ssl, '0.0.0.0',) + port)


if __name__ == '__main__':
    start_all(PORTS, False)
    start_all(SSL_PORTS, True)
    while True:
        sleep(1)

