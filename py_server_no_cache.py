#!/opt/homebrew/bin/python3.9

from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from time import time, sleep
from _thread import start_new_thread
import sys

PORT = 8080
if (len(sys.argv) > 1):
    PORT = int(sys.argv[1])


resp_404 = '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>

<head>
    <meta http-equiv="Content-Type" content="text/html;charset=utf-8">
    <title>Error response</title>
</head>

<body>
    <h1>Error response</h1>
    <p>Error code: 404</p>
    <p>Message: File not found.</p>
    <p>Error code explanation: HTTPStatus.NOT_FOUND - Nothing matches the given URI.</p>
</body>

</html>'''
resp_404 = resp_404.encode('utf-8')


def check_path(p: str):
    # 这里只检查这个 path 是否可能具有危害，不检查文件是否存在或合法性
    if (len(p) == 0):
        return False
    if (p[0] != '/'):
        return False
    if (p.find('/../') != -1):
        return False
    if (p.endswith('/..')):
        return False
    return True


class Request(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path
        if (path == '/'):
            path = '/index.html'
        path_legal = check_path(path)
        exist = True
        data = b''
        if (path_legal):
            try:
                with open('.' + path, 'rb') as f:
                    data = f.read()
            except:
                exist = False
        if (exist == False or path_legal == False):
            self.send_response(404)
            self.send_header('Content-Type', 'text/html;charset=utf-8')
            self.send_header('Content-Length', len(resp_404))
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', 'Thu, 01 Jan 1970 00:00:00 GMT')
            self.end_headers()
            self.wfile.write(resp_404)
            return
        path = path.lower()
        content_type = ''
        if (path.endswith('.html')):
            content_type = 'text/html;charset=utf-8'
        if (path.endswith('.css')):
            content_type = 'text/css;charset=utf-8'
        if (path.endswith('.js')):
            content_type = 'application/javascript;charset=utf-8'
        if (path.endswith('.jpg') or path.endswith('.jpeg')):
            content_type = 'image/jpg'
        if (path.endswith('.png')):
            content_type = 'image/png'
        if (path.endswith('.gif')):
            content_type = 'image/gif'
        if (path.endswith('.ico')):
            content_type = 'image/x-icon'
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', len(data))
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', 'Thu, 01 Jan 1970 00:00:00 GMT')
        self.end_headers()
        self.wfile.write(data)


def start(port: int):
    server = ThreadingHTTPServer(('0.0.0.0', port), Request)
    server.serve_forever()


start_new_thread(start, (PORT,))
print(f'[*] Listening on 0.0.0.0:{PORT}')
while True:
    sleep(10)
