from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import pathlib
import mimetypes
import json
from datetime import datetime
import socket


BASE_DIR = pathlib.Path()
DATA = {}


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_POST(self): # noqa
        body = self.rfile.read(int(self.headers['Content-Length']))
        body = urllib.parse.unquote_plus(body.decode())
        payload = {str(datetime.now()): {key: value for key, value in [el.split('=') for el in body.split('&')]}}
        DATA.update(payload)
        with open(BASE_DIR.joinpath('storage/data.json'), 'w', encoding='utf-8') as f:
            json.dump(DATA, f, ensure_ascii=False)
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
                    self.send_html('error.html', 404)

    def send_html(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as f:
            self.wfile.write(f.read())

    def send_static(self, filename):
        self.send_response(200)
        mt, *rest = mimetypes.guess_type(filename)
        if mt:
            self.send_header('Content-Type', mt)
        else:
            self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        with open(filename, 'rb') as f:
            self.wfile.write(f.read())


def run(server=HTTPServer, handler=SimpleHTTPRequestHandler):
    address = ('', 3000)
    http_server = server(address, handler)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()


if __name__ == '__main__':
    run()
