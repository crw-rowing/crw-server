from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler


def serve(host, port):
    httpd = HTTPServer((host, port), FileServer)
    httpd.serve_forever()
    httpd.server_close()


class FileServer(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200) # OK
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        self.do_HEAD()
        self.wfile.write('Hello World!')