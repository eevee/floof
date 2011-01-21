#!/usr/bin/env python

"""
Janrain's example server, streamlined and with most exception handling
removed for testing purposes and with an /update faculty added.
"""

__copyright__ = 'Copyright 2005-2008, Janrain, Inc.'

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from urlparse import urlparse

import time
import Cookie
import cgi
import cgitb
import sys

def quoteattr(s):
    qs = cgi.escape(s, 1)
    return '"%s"' % (qs,)

try:
    import openid
except ImportError:
    sys.stderr.write("""
Failed to import the OpenID library. In order to use this example, you
must either install the library (see INSTALL in the root of the
distribution) or else add the library to python's import path (the
PYTHONPATH environment variable).

For more information, see the README in the root of the library
distribution.""")
    sys.exit(1)

from openid.extensions import sreg
from openid.server import server
from openid.store.filestore import FileOpenIDStore
from openid.consumer import discover

class OpenIDHTTPServer(HTTPServer):
    """
    http server that contains a reference to an OpenID Server and
    knows its base URL.
    """
    def __init__(self, *args, **kwargs):
        HTTPServer.__init__(self, *args, **kwargs)

        if self.server_port != 80:
            self.base_url = ('http://%s:%s/' %
                             (self.server_name, self.server_port))
        else:
            self.base_url = 'http://%s/' % (self.server_name,)

        self.openid = None
        self.approved = {}
        self.lastCheckIDRequest = {}
        self.user = None
        self.accept = None

    def setOpenIDServer(self, oidserver):
        self.openid = oidserver


class ServerHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        BaseHTTPRequestHandler.__init__(self, *args, **kwargs)
        self.getEnv()

    def getEnv(self):
        self.user = self.server.user
        self.accept = self.server.accept

    def do_GET(self):
        self.getEnv()
        self.parsed_uri = urlparse(self.path)
        self.query = {}
        for k, v in cgi.parse_qsl(self.parsed_uri[4]):
            self.query[k] = v

        path = self.parsed_uri[2].lower()

        if path == '/':
            self.showMainPage()
        elif path == '/openidserver':
            self.serverEndPoint(self.query)
        elif path.startswith('/id/'):
            self.showIdPage(path)
        elif path.startswith('/yadis/'):
            self.showYadis(path[7:])
        elif path == '/serveryadis':
            self.showServerYadis()
        else:
            raise ValueError('404 Not Found: {0}'.format(path))

    def do_POST(self):
        self.getEnv()
        self.parsed_uri = urlparse(self.path)

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        self.query = {}
        for k, v in cgi.parse_qsl(post_data):
            self.query[k] = v

        path = self.parsed_uri[2]
        if path == '/openidserver':
            self.serverEndPoint(self.query)
        elif path == '/allow':
            self.handleAllow(self.query)
        elif path == '/update':
            self.updateParams(self.query)
        else:
            raise ValueError('404 Not Found: {0}'.format(path))

    def updateParams(self, query):
        self.server.user = self.user = query['user']
        self.server.accept = self.accept = (query['accept'] == 'true')
        self.showPage(200, 'Updated')

    def handleAllow(self, query):
        request = self.server.lastCheckIDRequest.get(self.user)

        if self.accept:
            if request.idSelect():
                identity = self.server.base_url + 'id/' + query['identifier']
            else:
                identity = request.identity

            response = self.approved(request, identity)

        else:
            response = request.answer(False)

        self.displayResponse(response)

    def isAuthorized(self, identity_url, trust_root):
        if self.user is None:
            return False
        if identity_url != self.server.base_url + 'id/' + self.user:
            return False
        return self.accept

    def serverEndPoint(self, query):
        request = self.server.openid.decodeRequest(query)

        if request.mode in ["checkid_immediate", "checkid_setup"]:
            self.handleCheckIDRequest(request)
        else:
            response = self.server.openid.handleRequest(request)
            self.displayResponse(response)

    def approved(self, request, identifier=None):
        response = request.answer(True, identity=identifier)
        sreg_req = sreg.SRegRequest.fromOpenIDRequest(request)
        sreg_data = {
            'nickname':self.user,
            'email':'{0}@example.com'.format(self.user),
            }
        sreg_resp = sreg.SRegResponse.extractResponse(sreg_req, sreg_data)
        response.addExtension(sreg_resp)
        return response

    def handleCheckIDRequest(self, request):
        is_authorized = self.isAuthorized(request.identity, request.trust_root)
        if is_authorized:
            response = self.approved(request)
            self.displayResponse(response)
        elif request.immediate:
            response = request.answer(False)
            self.displayResponse(response)
        else:
            self.server.lastCheckIDRequest[self.user] = request
            self.showDecidePage(request)

    def displayResponse(self, response):
        webresponse = self.server.openid.encodeResponse(response)

        self.send_response(webresponse.code)
        for header, value in webresponse.headers.iteritems():
            self.send_header(header, value)
        self.end_headers()

        if webresponse.body:
            self.wfile.write(webresponse.body)

    def showDecidePage(self, request):
        id_url_base = self.server.base_url+'id/'
        # XXX: This may break if there are any synonyms for id_url_base,
        # such as referring to it by IP address or a CNAME.
        assert (request.identity.startswith(id_url_base) or
                request.idSelect()), repr((request.identity, id_url_base))
        expected_user = request.identity[len(id_url_base):]

        if request.idSelect(): # We are being asked to select an ID
            # POST /allow --> identifier, yes/no
            pass
        elif expected_user == self.user:
            # POST /allow --> yes/no
            pass
        else:
            raise ValueError('Request recieved for user "{0}"; expected {1}'
                    .format(expected_user, self.user))
            
        self.showPage(200, 'Approve OpenID request?')

    def showIdPage(self, path):
        link_tag = '<link rel="openid.server" href="%sopenidserver">' %\
              self.server.base_url
        yadis_loc_tag = '<meta http-equiv="x-xrds-location" content="%s">'%\
            (self.server.base_url+'yadis/'+path[4:])
        disco_tags = link_tag + yadis_loc_tag

        self.showPage(200, 'An Identity Page', head_extras=disco_tags)

    def showYadis(self, user):
        self.send_response(200)
        self.send_header('Content-type', 'application/xrds+xml')
        self.end_headers()

        endpoint_url = self.server.base_url + 'openidserver'
        user_url = self.server.base_url + 'id/' + user
        self.wfile.write("""\
<?xml version="1.0" encoding="UTF-8"?>
<xrds:XRDS
xmlns:xrds="xri://$xrds"
xmlns="xri://$xrd*($v*2.0)">
<XRD>

<Service priority="0">
<Type>%s</Type>
<Type>%s</Type>
<URI>%s</URI>
<LocalID>%s</LocalID>
</Service>

</XRD>
</xrds:XRDS>
"""%(discover.OPENID_2_0_TYPE, discover.OPENID_1_0_TYPE,
     endpoint_url, user_url))

    def showServerYadis(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/xrds+xml')
        self.end_headers()

        endpoint_url = self.server.base_url + 'openidserver'
        self.wfile.write("""\
<?xml version="1.0" encoding="UTF-8"?>
<xrds:XRDS
xmlns:xrds="xri://$xrds"
xmlns="xri://$xrd*($v*2.0)">
<XRD>

<Service priority="0">
<Type>%s</Type>
<URI>%s</URI>
</Service>

</XRD>
</xrds:XRDS>
"""%(discover.OPENID_IDP_2_0_TYPE, endpoint_url,))

    def showMainPage(self):
        yadis_tag = '<meta http-equiv="x-xrds-location" content="%s">'%\
            (self.server.base_url + 'serveryadis')
        self.showPage(200, 'Main Page', head_extras = yadis_tag)

    def showPage(self, response_code, title,
                 head_extras='', msg=None, err=None, form=None):

        if self.user is None:
            user_link = '<a href="/login">not logged in</a>.'
        else:
            user_link = 'logged in as <a href="/id/%s">%s</a>.<br /><a href="/loginsubmit?submit=true&success_to=/login">Log out</a>' % \
                        (self.user, self.user)

        body = ''

        if err is not None:
            body += '''\
<div class="error">
%s
</div>
''' % err

        if msg is not None:
            body += '''\
<div class="message">
%s
</div>
''' % msg

        if form is not None:
            body += '''\
<div class="form">
%s
</div>
''' % form

        contents = {
            'title': 'Python OpenID Server Example - ' + title,
            'head_extras': head_extras,
            'body': body,
            'user_link': user_link,
            }

        self.send_response(response_code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        self.wfile.write('''<html>
<head>
<title>%(title)s</title>
%(head_extras)s
</head>
<body>
%(body)s
</body>
</html>
''' % contents)


def main(host, port, data_path):
    addr = (host, port)
    httpserver = OpenIDHTTPServer(addr, ServerHandler)

    # Instantiate OpenID consumer store and OpenID consumer. If you
    # were connecting to a database, you would create the database
    # connection and instantiate an appropriate store here.
    store = FileOpenIDStore(data_path)
    oidserver = server.Server(store, httpserver.base_url + 'openidserver')

    httpserver.setOpenIDServer(oidserver)
    httpserver.serve_forever()


if __name__ == '__main__':
    host = sys.argv[1]
    port = int(sys.argv[2])
    data_path = sys.argv[3]

    main(host, port, data_path)
