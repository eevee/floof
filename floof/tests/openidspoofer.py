import httplib
import os
import subprocess
import sys
import time
from urllib import urlencode
from urlparse import urlparse

SERVER_PATH = os.path.join(os.path.dirname(__file__), 'openid_server.py')

class OpenIDSpoofer(object):
    """
    Spawns and manages an dummy OpenID server.

    The server will only accept one username at a time and will respond
    based on the value of accept, given in the update method.
    """
    def __init__(self, host, port, data_path):
        self.host = host
        self.port = str(port)
        self.data_path = data_path
        self.server = subprocess.Popen([
                sys.executable,
                SERVER_PATH,
                self.host,
                self.port,
                self.data_path
                ])
        # XXX: Disgusting hack to wait until the server is set up before
        # connecting to it.  I'm trying to minimise complexity.
        time.sleep(1)
        self._check_server()
        self.conn = httplib.HTTPConnection(self.host, self.port)

    def __del__(self):
        # Be clean
        self.conn.close()
        self.server.terminate()

    def _check_server(self):
        if self.server.poll() is not None:
            raise RuntimeError('The OpenID server appears to have unexpectedly died.')
                
    def update(self, user, accept):
        """
        Configures the dummy OpenID server.

        Arguments:
        user -- string: the user name to which to respond successfully
        accept -- boolean: whether to pretend that the user has authorised
                the consumer to authenticate them
        """
        self._check_server()
        post = [('user', user),
                ('accept', 'true' if accept else 'false'),
                ]
        body = urlencode(post)
        self.conn.request('POST', '/update', body)
        self.conn.getresponse()

    def spoof(self, location):
        """
        Convenience function to pretend to be a User-Agent following the
        passed location header to the dummy OpenID server.

        XXX: We may just end up getting the dummy server to skip the
        client authorisation bit and send the client response itself.
        """
        self._check_server()

        # First, follow the location
        url = urlparse(location)
        path = '{0}?{1}'.format(url[2], url[4])
        self.conn.request('GET', path)
        response = self.conn.getresponse()

        # Then, return the redirect back to the test function
        location = response.getheader('location')
        if location is None:
            return None, None
        parse = urlparse(location)
        path = parse[2]
        params = parse[4]
        return path, params

