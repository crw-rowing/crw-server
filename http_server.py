from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from mimetypes import guess_type
from posixpath import normpath
import errno
from crw import VERSION
from crw_jsonrpc import CrwJsonRpc
import database
import ssl


def serve(host, port, database_name, database_user):
    global httpd, database_object, rpc
    httpd = HTTPServer((host, port), FileServer)
    httpd.socket = ssl.wrap_socket(
        httpd.socket,
        server_side=True,
        # Replace with different paths if needed
        certfile='/etc/letsencrypt/live/' +
        'crw.demoprojecten.nl/cert.pem',
        keyfile='/etc/letsencrypt/live/' +
        'crw.demoprojecten.nl/privkey.pem')
    database_object = database.Database(database_name, database_user)
    rpc = CrwJsonRpc(database_object)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()


class FileServer(BaseHTTPRequestHandler):
    redirects = {
        '': 'static/promo/index.html',
        'favicon.ico': 'static/favicon.ico',
        'css/bootstrap.min.css' : 'static/promo/css/bootstrap.min.css',
        'css/landing-page.css' : 'static/promo/css/landing-page.css',
        'font-awesome/css/font-awesome.min.css' : 'static/promo/font-awesome/css/font-awesome.min.css',
        'js/jquery.js' : 'static/promo/js/jquery.js',
        'js/bootstrap.min.js' : 'static/promo/js/bootstrap.min.js',
        'img/crw_logo_golf.png' : 'static/promo/img/crw_logo_golf.png',
        'img/ipad.png' : 'static/promo/img/ipad.png',
        'img/crw_laptop1.png' : 'static/promo/img/crw_laptop1.png',
        'img/crwlogo-pc.png' : 'static/promo/img/crwlogo-pc.png',
        'img/ruud_thumbnail.jpg' : 'static/promo/img/ruud_thumbnail.jpg',
        'img/nikita_thumbnail.jpg' : 'static/promo/img/nikita_thumbnail.jpg',
        'img/marien_thumbnail.jpg' : 'static/promo/img/marien_thumbnail.jpg',
        'img/justin_thumbnail.jpg' : 'static/promo/img/justin_thumbnail.jpg',
        'img/lotte_thumbnail.jpg' : 'static/promo/img/lotte_thumbnail.jpg',
        'img/luuk_thumbnail.jpg' : 'static/promo/img/luuk_thumbnail.jpg',
        'img/background_row_blue.jpg' : 'static/promo/img/background_row_blue.jpg',
        'img/banner_coffee_blue.png' : 'static/promo/img/banner_coffee_blue.png'
    }
    server_version = "crw/{}".format(VERSION)

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
