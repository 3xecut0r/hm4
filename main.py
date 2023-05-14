import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import pathlib
import mimetypes
import json
from datetime import datetime
import socket
from threading import Thread

BASE_DIR = pathlib.Path()
DATA = {}
UDP_IP = '127.0.0.1'
UDP_PORT = 5000
HTTP_PORT = 3000
BUFFER = 1024
OK = 200
STATUS_ERROR = 404
STORAGE_DIR = BASE_DIR / 'storage'
DATA_FILE = STORAGE_DIR / 'data.json'


def send_data_to_socket(body):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.sendto(body, (UDP_IP, UDP_PORT))
    client_socket.close()


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_POST(self): # noqa
        body = self.rfile.read(int(self.headers['Content-Length']))
        send_data_to_socket(body)
        self.send_response(302)
        self.send_header('Location', '/index.html')
        self.end_headers()

    def do_GET(self): # noqa
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case "/":
                self.send_html('index.html')
            case "/message.html":
                self.send_html('message.html')
            case _:
                file = BASE_DIR / route.path[1:]
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html('error.html', STATUS_ERROR)

    def send_html(self, filename, status=OK):
        self.send_response(status)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as f:
            self.wfile.write(f.read())

    def send_static(self, filename):
        self.send_response(OK)
        mt, *rest = mimetypes.guess_type(filename)
        if mt:
            self.send_header('Content-Type', mt)
        else:
            self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        with open(filename, 'rb') as f:
            self.wfile.write(f.read())


def run(server=HTTPServer, handler=SimpleHTTPRequestHandler):
    address = ('', HTTP_PORT)
    http_server = server(address, handler)
    logging.info(f'Start http server {http_server.server_name}')
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()


def save_data(data):
    body = urllib.parse.unquote_plus(data.decode())
    try:
        payload = {str(datetime.now()): {key: value for key, value in [el.split('=') for el in body.split('&')]}}
        DATA.update(payload)
        with open(BASE_DIR.joinpath('storage/data.json'), 'w', encoding='utf-8') as f:
            json.dump(DATA, f, ensure_ascii=False)
    except ValueError as e:
        logging.error(f'Field parse data: {data} with error {e}')
    except OSError as er:
        logging.error(f'Field write data: {data} with error {er}')


def run_socket_server(ip, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    server_socket.bind(server)
    logging.info(f'Start echo server {server_socket.getsockname()}')
    try:
        while True:
            data, address = server_socket.recvfrom(BUFFER)
            save_data(data)
    except KeyboardInterrupt:
        logging.info('Server socket stopped')
    finally:
        server_socket.close()


if __name__ == '__main__':
    if not STORAGE_DIR.exists():
        STORAGE_DIR.mkdir()
    if not DATA_FILE.exists():
        with open(DATA_FILE, 'w') as fd:
            json.dump({}, fd)
    logging.basicConfig(level=logging.INFO, format='%(threadName)s %(message)s')
    thread_server = Thread(target=run)
    thread_server.start()

    thread_socket = Thread(target=run_socket_server(UDP_IP, UDP_PORT))
    thread_socket.start()
