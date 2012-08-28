import functools
import json

from base64 import b64encode
from copy import deepcopy
from random import getrandbits
from urlparse import parse_qs

from lxml import etree
from oauthlib.oauth2.draft25 import WebApplicationClient

from floof import model
from floof.tests import FunctionalTests
from floof.tests import sim


def expect_api_error(response, name, desc_hint=None):
    body = json.loads(response.body)
    print body
    status = '401' if name == 'invalid_client' else '400'
    assert response.status.startswith(status)
    assert body['error'] == name
    if desc_hint:
        assert desc_hint.lower() in body['error_description'].lower()


def post_api_error(test, headers, params, name, desc_hint=None, *args,
                   **kwargs):
    print 'Headers:', headers
    print 'Params: ', params
    response = test.app.post(
###        '/api/oauth/2.0/token',
        test.api_url('oauth2.token'),
        *args,
        params=params,
        headers=headers,
        expect_errors=True,
        extra_environ={'wsgi.url_scheme': 'https'},
        **kwargs
    )
    expect_api_error(response, name, desc_hint)
    return response


def byteify_dict(dictionary):
    def byteify(stringish):
        if isinstance(stringish, unicode):
            return stringish.encode('utf-8')
        return stringish
    return dict((byteify(k), byteify(v))
                for k, v in dictionary.iteritems())


class TestOAuthFlows(FunctionalTests):

    def setUp(self):
        """Creates a user to be used as a fake login."""
        super(TestOAuthFlows, self).setUp()

        self.user = sim.sim_user()
        self.provider = sim.sim_user()

        self.client_w = sim.sim_oauth_client(self.provider, type_=u'web')
        self.client_n = sim.sim_oauth_client(self.provider, type_=u'native')
        model.session.flush()
        print model.session.query(model.OAuth2Client).get(self.client_n.id)

        self.default_environ = {
            'tests.user_id': self.user.id,
            'wsgi.url_scheme': 'https',  # pass the only-over-SSL/TLS test
        }

    def test_token_endpoint(self):
        headers = []
        params = []

        response = self.app.get(
            self.api_url('oauth2.token'),
            status=400,
            headers=headers,
        )
        expect_api_error(response, 'invalid_request', 'accept only POST')

        post = functools.partial(post_api_error, self)

        response = post(headers, params, 'invalid_client', 'authentication')

        headers.append(('Authorization', 'wrh 24 rty   me56'))
        response = post(headers, params, 'invalid_client', 'Basic authentication scheme')

        headers.pop()
        headers.append(('Authorization', 'Basic '))
        response = post(headers, params, 'invalid_client', 'client ID')

        headers.pop()
        headers.append(('Authorization', 'Basic #@*&%) *&(#*'))
        response = post(headers, params, 'invalid_client', 'client ID')

        headers.pop()
        auth = self.client_n.identifier.encode('base64')
        headers.append(('Authorization', 'Basic ' + auth))
        response = post(headers, params, 'invalid_request', 'x-www-form-urlencoded')

        headers.append(('Content-Type', 'application/x-www-form-urlencoded'))
        response = post(headers, params, 'invalid_request', 'grant_type')

        params.append(('grant_type', 'blah'))
        response = post(headers, params, 'unsupported_grant_type', 'authorization_code')

        params.pop()
        params.append(('grant_type', 'code'))
        response = post(headers, params, 'unsupported_grant_type', 'authorization_code')

        params.pop()
        params.append(('grant_type', 'authorization_code'))
        response = post(headers, params, 'invalid_request', 'code')

        # Test multiple parameters
        params.append(('grant_type', 'authorization_code'))
        response = post(headers, params, 'invalid_request', 'parameters')
        params.pop()

        params.append(('grant_type', ''))
        response = post(headers, params, 'invalid_request', 'parameters')
        params.pop()

        params.append(('code', '123456'))
        response = post(headers, params, 'invalid_grant', 'authorization code')

        grant, code = sim.sim_oauth_grant(self.client_n, self.user)
        model.session.flush()

        params.pop()
        params.append(('code', code))
        response = self.app.post(
            self.api_url('oauth2.token'),
            params=params,
            headers=headers,
            extra_environ={'wsgi.url_scheme': 'https'},
        )

    def test_flow(self):
        self._test_flow(self.client_n)
        self._test_flow(self.client_w)

    def _test_flow(self, orm_client):
        client_id = orm_client.identifier
        public = orm_client.auth_type == 'public'
        client_secret = None if public else orm_client.secret
        scope = 'art comments'
        state = str(getrandbits(128))

        default_token_headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        default_access_headers = deepcopy(default_token_headers)
        if public:
            b64auth = b64encode(client_id)
        else:
            b64auth = b64encode(client_id + ':' + client_secret)
        default_token_headers['Authorization'] = 'Basic {0}'.format(b64auth)

        client = WebApplicationClient(client_id)

        authz_url = client.prepare_request_uri(
            self.url('oauth2.authorize'),
            scope=scope,
            state=state
        ).encode('utf-8')  # app.post requires a bytestring

        # TODO: Test login here

        response = self.app.get(authz_url, extra_environ=self.default_environ)
        assert orm_client.name in response

        # TODO: Test re-auth here
        # TODO: Test revocation on double grant submission

        form = response.forms['oauth-authorize']
        form['accept'].force_value('accept')
        response = self.app.post(
            authz_url,
            form.submit_fields() + [('accept', 'accept')],
            extra_environ=self.default_environ,
        )

        if public:
            root = etree.HTML(response.body)
            path = etree.XPath('//p[@id="oauth-code"]/text()')
            code = path(root)[0]
            body = client.prepare_request_body(code=code)
        else:
            status = response.status_int
            assert status >= 300 and status < 400
            returned_uri = response.headers['location']
            client.parse_request_uri_response(returned_uri, state=state)
            body = client.prepare_request_body()

        # Retreive tokens
        token_endpoint = '/api/oauth/2.0/token'
        response = self.app.post(
            token_endpoint,
            parse_qs(body),
            headers=default_token_headers,
            extra_environ={'wsgi.url_scheme': 'https'},
        )
        client.parse_request_body_response(response.body, scope=scope)

        # Retreive auth state
        authstate_endpoint = '/api/whoami'
        headers = deepcopy(default_access_headers)
        uri, headers, body = client.add_token(
            authstate_endpoint, 'GET', headers=headers)
        response = self.app.get(
            uri,
            headers=byteify_dict(headers),
            extra_environ={'wsgi.url_scheme': 'https'},
        )

        # Retreive second access token via refresh token
        body = client.prepare_refresh_body()
        response = self.app.post(
            token_endpoint,
            parse_qs(body),
            headers=default_token_headers,
            extra_environ={'wsgi.url_scheme': 'https'},
        )

        # Retreive auth state again
        headers = deepcopy(default_access_headers)
        uri, headers, body = client.add_token(
            authstate_endpoint, 'GET', headers=headers)
        response = self.app.get(
            uri,
            headers=byteify_dict(headers),
            extra_environ={'wsgi.url_scheme': 'https'},
        )
