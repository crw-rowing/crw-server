import http_server


VERSION = '0.1'

HOST = ''
PORT = 8000
# Requires a database named 'ergon-database' owned by the user root,
# or you can change these to select another database.
DATABASE = 'ergon-database'
DATABASE_USER = 'root'

if __name__ == '__main__':
    http_server.serve(HOST, PORT, DATABASE, DATABASE_USER)
