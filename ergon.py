import http_server


VERSION = '0.1'

HOST = ''
PORT = 8000

if __name__ == '__main__':
    http_server.serve(HOST, PORT)
