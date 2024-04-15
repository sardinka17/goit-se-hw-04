import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
from pathlib import Path
import mimetypes
import json
from datetime import datetime
from threading import Thread
import socket

BASE_DIR = Path()
BUFFER_SIZE = 1024
PORT_HTTP = 3000
HOST_HTTP = "0.0.0.0"
SOCKET_HOST = "127.0.0.1"
SOCKET_PORT = 5000


class CustomFramework(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)

        if pr_url.path == "/":
            self.send_html_file("index.html")
        elif pr_url.path == "/message.html":
            self.send_html_file("message.html")
        elif pr_url.path == "/logo.png":
            self.send_html_file("logo.png")
        elif pr_url.path == "/styles.css":
            self.send_css_file("styles.css")
        else:
            file = BASE_DIR.joinpath(pr_url.path[1:])
            if file.exists():
                self.send_static(file)
            else:
                self.send_html_file("error.html", 404)

    def do_POST(self):
        size = self.headers.get("Content-Length")
        data = self.rfile.read(int(size))
        logging.info(data)

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(data, (SOCKET_HOST, SOCKET_PORT))
        client_socket.close()

        self.send_response(302)
        self.send_header("Location", "message.html")
        self.end_headers()

    def send_html_file(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html")
        self.end_headers()

        with open(filename, "rb") as file:
            self.wfile.write(file.read())

    def send_css_file(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header("Content-Type", "text/css")
        self.end_headers()

        with open(filename, "rb") as file:
            self.wfile.write(file.read())

    def send_static(self, filename, status_code=200):
        self.send_response(status_code)
        mime_type = mimetypes.guess_type(filename)

        if mime_type:
            self.send_header("Content-Type", mime_type[0])
        else:
            self.send_header("Content-Type", "text/plain")

        with open(filename, "rb") as file:
            self.wfile.write(file.read())


def parse_data(data):
    time_now = str(datetime.now())
    parsed_data = urllib.parse.unquote_plus(data.decode())
    logging.info(parsed_data)

    try:
        with open("storage/data.json", "r", encoding="utf-8") as file:
            current_json = json.load(file)

        logging.info(current_json)
        parsed_dict = {key: value for key, value in [el.split("=") for el in parsed_data.split("&")]}
        logging.info(parsed_dict)

        current_json[time_now] = parsed_dict

        with open("storage/data.json", "w", encoding="utf-8") as file:
            json.dump(current_json, file, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(e)


def run_http_server(host, port):
    address = (host, port)
    http_server = HTTPServer(address, CustomFramework)
    logging.info("Starting http server")

    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()


def run_socket_server(host, port):
    socket_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = host, port
    socket_server.bind(server)
    logging.info("Starting socket server")

    try:
        while True:
            message, address = socket_server.recvfrom(BUFFER_SIZE)
            parse_data(message)
    except KeyboardInterrupt:
        pass
    finally:
        socket_server.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(threadName)s %(message)s')

    server_http = Thread(target=run_http_server, args=(HOST_HTTP, PORT_HTTP))
    server_http.start()

    server_socket = Thread(target=run_socket_server, args=(SOCKET_HOST, SOCKET_PORT))
    server_socket.start()
