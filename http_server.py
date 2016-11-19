from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from mimetypes import guess_type
import errno


def serve(host, port):
    httpd = HTTPServer((host, port), FileServer)
    httpd.serve_forever()
    httpd.server_close()


class FileServer(BaseHTTPRequestHandler):
    def resolve_filename(self, fname):
        """
        Gives the right filename to be read and sent to the client,
        based on the request path.
        """
        if fname in ('', '/'):
            return 'static/index.html'
        if fname[0] == '/':
            return fname[1:]
        return fname

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
            self.wfile.write('Forbidden')
        else:
            try:
                f = open(fname)
                self.send_response(200)  # OK
                mime = guess_type(fname)[0] or 'text/plain'
                self.send_header('Content-type', mime)
                self.end_headers()
                if write:
                    self.wfile.write(f.read())
                f.close()
            except IOError, e:
                if e.errno == errno.ENOENT:
                    self.send_response(404)  # Not Found
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                else:
                    self.send_response(403)  # Forbidden
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()

                if write:
                    self.wfile.write(
                        'IOError ({})'.format(errno.errorcode[e.errno]))

    def do_HEAD(self):
        self.send_file(self.path, write=False)

    def do_GET(self):
        self.send_file(self.path)
