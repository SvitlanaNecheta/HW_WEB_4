import urllib.parse
import mimetypes
import logging
import json
import socket
from pathlib import Path
from datetime import datetime
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from jinja2 import Environment, FileSystemLoader

BASE_DIR = Path()
BUFFER_SIZE = 1024
HTTP_PORT = 3000
HTTP_HOST ='0.0.0.0'
SOCKET_PORT=5000
SOCKET_HOST='127.0.0.1'

jinja = Environment(loader=FileSystemLoader(BASE_DIR / 'templates'))

#***************************************


class GoITFramework(BaseHTTPRequestHandler):

    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case '/':
                self.send_html('index.html')
            case '/message':
                self.render_template('message.html')
            case _:
                file=BASE_DIR.joinpath(route.path[1:])
                if file.exists():
                    self.send_static(file, 200)
                else:
                    self.send_html('error.html', 404)


    def do_POST(self):
        size=self.headers.get('Content-Length')
        data = self.rfile.read(int(size))
        #_______________
        client_socket =socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(data,(SOCKET_HOST,SOCKET_PORT))
        client_socket.close()
        #________________
        self.send_response(302)
        self.send_header('Location', '/message.html')
        self.end_headers()


    def send_html(self, filename, statuscode=200):
        self.send_response(statuscode)
        self.send_header('Content-type','text/html')
        self.end_headers()
        with open(filename,'rb') as file:
            self.wfile.write(file.read())
    
    def render_template(self, filename, statuscode=200):
        self.send_response(statuscode)
        self.send_header('Content-Type','text/html')
        self.end_headers()
        with open('storage/data.json','r',encoding='utf-8') as file:
            data = json.load(file)
        template = jinja.get_template(filename)
        html = template.render(messages=data)
        self.wfile.write(html.encode())


    def send_static(self, filename, statuscode):
        self.send_response(statuscode)
        mime_type, *_=mimetypes.guess_type(filename)
        if mime_type:
            self.send_header('Content-type', mime_type)
        else:
            self.send_header('Content-type','text/plain')
        self.end_headers()
        with open(filename,'rb') as file:
            self.wfile.write(file.read())

#****************************************


def save_data_from_form(data):
    parse_data = urllib.parse.unquote_plus(data.decode())
    print(parse_data)
    try:
        # Парсинг даних із форми
        parse_dict = {key: value for key, value in [el.split('=') for el in parse_data.split('&')]}
        
        # Отримуємо поточний час як ключ
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        
        # Формуємо новий запис
        new_entry = {
            current_time: {
                "username": parse_dict.get('username', 'Unknown'),
                "message": parse_dict.get('message', '')
            }
        }
        
    
        try:
            with open('storage/data.json', 'r', encoding='utf-8') as file:
                data = json.load(file)
        except FileNotFoundError:
            
            data = {}

        
        data.update(new_entry)
        
        
        with open('storage/data.json', 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
    except ValueError as err:
        logging.error(f"ValueError: {err}")
    except OSError as err:
        logging.error(f"OSError: {err}")

#****************************************
def run_socket_server(host, port):
    server_socket=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    server_socket.bind((host,port))
    logging.info("Starting socket server")
    try:
        while True:
            msg, address = server_socket.recvfrom(BUFFER_SIZE)
            logging.info(f"Socket received {address} : {msg}")
            save_data_from_form(msg)
    except KeyboardInterrupt:
        pass
    finally:
        server_socket.close()
        print("Server socket closed.")

#****************************************
def run_http_server(host, port):
    address = (host, port)
    http_server = HTTPServer(address, GoITFramework)
    logging.info("Starting http server")
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        http_server.server_close()
        print("Server stopped.")
#****************************************
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(threadName)s %(message)s')

    server = Thread(target=run_http_server, args=(HTTP_HOST,HTTP_PORT))
    server.start()

    server_socket = Thread(target=run_socket_server, args=(SOCKET_HOST, SOCKET_PORT))
    server_socket.start()