from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import mimetypes
import json
from datetime import datetime
import socket
import pathlib

BASE_DIR = pathlib.Path()

class MainServer(BaseHTTPRequestHandler):

    def do_GET(self):
        return self.router() 
    
    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        self.send_data_socket(data.decode())
        self.save_data_to_json(data)
        self.send_response(200)
        self.send_header('Location', '/message')
        self.end_headers()

    def send_static(self, file):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header('Content-type', mt[0])
        else:
            self.send_header('Content-type', 'text/plain')
        self.end_headers()
        with open(file, 'rb') as fd:   
            self.wfile.write(fd.read())

    def send_html(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())
    
    def save_data_to_json(self, data):
        data_parse = urllib.parse.unquote_plus(data.decode())
        data_parse = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
        new_time = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        new_data = {new_time: data_parse}
        with open(BASE_DIR.joinpath('storage/data.json'), 'a', encoding='utf-8') as fd:
            json.dump(new_data, fd, indent=3, ensure_ascii=False)
            fd.write('\n')

    def router(self):
        pr_url = urllib.parse.urlparse(self.path)

        match pr_url.path:
            case '/':
                self.send_html('index.html')
            case '/message':
                self.send_html('message.html')
            case _:
                file = BASE_DIR.joinpath(pr_url.path[1:])
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html('error.html', 404)

    def send_data_socket(self, data):
        host = socket.gethostname()
        port = 5000

        client_socket = socket.socket()
        client_socket.connect((host, port))

        client_socket.send(data.encode())
        response = client_socket.recv(1024).decode()
        print(f'Received response from socket server: {response}')

        client_socket.close()

def server_socket():
    print("start socket running")
    host = socket.gethostname()
    port = 5000

    server_socket = socket.socket()
    server_socket.bind((host, port))
    server_socket.listen(2)
    conn, address = server_socket.accept()
    print(f'Connection from {address}')
    while True:
        data = conn.recv(100).decode()

        if not data:
            break
        print(f'received message from socket client: {data}')
        # Відповідь клієнту
        response = f"Received your message: {data}"
        conn.send(response.encode())

    conn.close()  

def run(server_class=HTTPServer, handler_class=MainServer):
    server_address = ('', 3000)
    http = server_class(server_address, handler_class)
    try:
        print ("start run")
        start_socket_server = Thread(target=server_socket)
        start_socket_server.start()
        http.serve_forever()

    except KeyboardInterrupt:
        http.server_close()    

if __name__ == '__main__':
    run()
