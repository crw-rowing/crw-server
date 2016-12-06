from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from mimetypes import guess_type
from posixpath import normpath
import errno
import crw
from crw_jsonrpc import CrwJsonRpc
import database


def serve(host, port, database_name, database_user):
    global httpd, user_database, rpc
    httpd = HTTPServer((host, port), FileServer)
    database_object = database.Database(database_name, database_user)
    user_database = database.UserDatabase(database_object)
    rpc = CrwJsonRpc(user_database)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()


class FileServer(BaseHTTPRequestHandler):
    redirects = {
        '': 'static/index.html',
        'favicon.ico': 'static/favicon.ico',
    }
    server_version = "crw/{}".format(crw.VERSION)

    def resolve_filename(self, fname):
        """
        Gives the right filename to be read and sent to the client,
        based on the request path.
        """
        fname = normpath(fname)
        if fname[0] == '/':
            fname = fname[1:]
        return FileServer.redirects[fname] if fname in FileServer.redirects \
            else fname

    def send_file(self, fname, write=True):
        """
        Reads a file and sends as HTTP response, including the MIME type.
        write indicates if the file should actually be sent,
        or only the headers
        """
        fname = self.resolve_filename(fname)
        if not fname.startswith('static/'):
            self.send_response(403)  # Forbidden
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            if write:
                self.wfile.write('Forbidden')
        else:
            try:
                mime = guess_type(fname)[0] or 'text/plain'
                f = open(fname, 'rb')

                self.send_response(200)  # OK
                self.send_header('Content-type', mime)
                self.end_headers()

                if write:
                    self.wfile.write(f.read())

                f.close()
            except IOError, e:
                self.send_response(404 if e.errno == errno.ENOENT else 403)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                if write:
                    self.wfile.write(
                        'IOError ({})'.format(errno.errorcode[e.errno]))

    def do_HEAD(self):
        self.send_file(self.path, write=False)

    def do_GET(self):
        self.send_file(self.path)

    def do_POST(self):
        if self.path == '/rpc':
            length = int(self.headers.getheader('content-length'))
            request = self.rfile.read(length)
            response = rpc.rpc_invoke(request)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(response)
