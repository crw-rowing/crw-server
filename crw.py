import ConfigParser
import thread

VERSION = '0.1'
CONFIG_FILE = 'crw.cfg'

cfg = ConfigParser.ConfigParser()
cfg.read(CONFIG_FILE)

HOST = cfg.get('http', 'host')
PORT = int(cfg.get('http', 'port'))

USE_HTTPS = cfg.get('https', 'enabled') == 'True'
HTTPS_PORT = cfg.get('https', 'port')
HTTPS_CERT = cfg.get('https', 'certfile')
HTTPS_KEY = cfg.get('https', 'keyfile')

DATABASE_HOST = cfg.get('database', 'host')
DATABASE_PORT = cfg.get('database', 'port')
DATABASE_NAME = cfg.get('database', 'name')
DATABASE_USER = cfg.get('database', 'user')
DATABASE_PASS = cfg.get('database', 'password')

USE_REDIRECTOR = cfg.get('redirector', 'enabled') == 'True'
REDIRECT_TARGET = cfg.get('redirector', 'target')

if __name__ == '__main__':
    try:
        import http_redirector
        thread.start_new_thread(http_redirector.serve, ())
        import http_server
        http_server.serve()
    except KeyboardInterrupt:
        print 'Exiting...'
        raise SystemExit
