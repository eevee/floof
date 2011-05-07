from floof import model
from floof.model import meta
from floof.tests import *
import floof.tests.openidspoofer as oidspoof
import floof.tests.sim as sim

import copy
from openid import oidutil
import OpenSSL.crypto as ssl
import time
from urlparse import parse_qs, urlparse

PORT = 19614
DATA_PATH = '/tmp'

# Hook OpenID's stderr log to stop it spewing all over our nosetest
def null_log(message, level=0):
    pass
oidutil.log = null_log

class TestControlsController(TestController):
    
    @classmethod
    def setup_class(cls):
        """Creates a user to be used as a fake login."""
        cls.user = sim.sim_user()
        meta.Session.commit()

        # Force a refresh of the user, to get id populated
        # XXX surely there's a better way!
        meta.Session.refresh(cls.user)

        cls.default_environ = {
                'tests.user_id': cls.user.id,
                'tests.auth_openid_uid': cls.user.id,
                'tests.auth_openid_time': time.time(),
                }

        cls.spoofer = oidspoof.OpenIDSpoofer('localhost', PORT, DATA_PATH)

    @classmethod
    def teardown_class(cls):
        del cls.spoofer

    def test_index(self):
        """Test display of user controls index."""
        response = self.app.get(
                url(controller='controls', action='index'),
                extra_environ={'tests.user_id': self.user.id},
                )
        # Test response...

    def test_user_info(self):
        """Test modification of basic user info options."""
        response = self.app.get(
                url(controller='controls', action='user_info'),
                extra_environ={'tests.user_id': self.user.id},
                )
        assert 'Display Name' in response, 'User Info control page does not appear to have loaded.'

        # Test setting some new user details
        response = self.app.post(
                url(controller='controls', action='user_info'),
                params=[
                    ('display_name', u'Barack Obama'),
                    ('timezone', u'US/Eastern'),
                    ('email', u'abc@example.org'),
                ],
                extra_environ={'tests.user_id': self.user.id},
                )
        response = self.app.get(
                url(controller='controls', action='user_info'),
                extra_environ={'tests.user_id': self.user.id},
                )
        assert 'Barack Obama' in response, 'Failed to set display name.'
        assert 'selected="selected" value="US/Eastern"' in response, 'Failed to set timezone.'

        # TODO: Test normalization of the display name

    def test_openids(self):
        """Test display of user OpenID controls page."""
        response = self.app.get(
                url(controller='controls', action='openid'),
                extra_environ=self.default_environ,
                )
        assert 'Add a New OpenID Identity' in response, 'OpenID control page does not appear to have loaded.'

    def test_openids_add_del(self):
        """Test addition and deletion of OpenID URLs."""
        test_openids = [
                u'flooftest1',
                u'flooftest2',
                ]
        responses = []

        spoofer = self.spoofer

        # Test adding two OpenID identities
        for user in test_openids:
            spoofer.update(user=user, accept=True)
            response_begin = self.app.post(
                    url(controller='controls', action='openid'),
                    params=[
                        ('add_openid', u'Add OpenID'),
                        ('new_openid', spoofer.url),
                    ],
                    extra_environ=self.default_environ,
                    )
            location = response_begin.headers['location']
            path, params = spoofer.spoof(location)
            assert path is not None
            response_end = self.app.get(
                    path,
                    params=params,
                    extra_environ=self.default_environ,
                    )
            assert response_end.status == '200 OK'
            responses.append(response_end)
        assert 'http://localhost:{0}/id/flooftest1</label>'.format(PORT) in responses[0], 'Addition of OpenID identity URL failed.'
        assert 'http://localhost:{0}/id/flooftest2</label>'.format(PORT) not in responses[0], 'App appears to have guessed our next OpenID URL....'
        assert 'http://localhost:{0}/id/flooftest1</label>'.format(PORT) in responses[1], 'Addition of OpenID identity URL was not retained.'
        assert 'http://localhost:{0}/id/flooftest2</label>'.format(PORT) in responses[1], 'Addition of second OpenID identity URL failed.'

        # Test denial of double-entries
        response_begin = self.app.post(
                url(controller='controls', action='openid'),
                params=[
                    ('add_openid', u'Add OpenID'),
                    ('new_openid', spoofer.url),
                ],
                extra_environ=self.default_environ,
                )
        location = response_begin.headers['location']
        path, params = spoofer.spoof(location)
        assert path is not None
        response_end = self.app.get(
                path,
                params=params,
                extra_environ=self.default_environ,
                )
        assert 'can already authenticate with that OpenID' in response_end

        # Test deletion
        oid = meta.Session.query(model.IdentityURL) \
                .filter_by(url=spoofer.url) \
                .one()
        response = self.app.post(
                url(controller='controls', action='openid'),
                params=[
                    ('del_openids', u'Delete Selected Identities'),
                    ('openids', oid.id),
                ],
                extra_environ=self.default_environ,
                )
        assert 'http://localhost:{0}/id/flooftest1</label>'.format(PORT) in response, 'An OpenID identity URL that should have been found was not.'
        assert 'http://localhost:{0}/id/flooftest2</label>'.format(PORT) not in response, 'Deletion of OpenID identity URL failed.'

        # Test rejection of deletion of final OpenID URL
        q = meta.Session.query(model.IdentityURL).filter_by(user_id=self.user.id)
        assert q.count() < 2, 'Test user has more that one OpenID URL, when they should not.'
        assert q.count() > 0, 'Test user no OpenID URLs, when they should have one.'
        oid = q.one()
        response = self.app.post(
                url(controller='controls', action='openid'),
                params=[
                    ('del_openids', u'Delete Selected Identities'),
                    ('openids', oid.id),
                ],
                extra_environ=self.default_environ,
                )
        assert 'http://localhost:{0}/id/flooftest1</label>'.format(PORT) in response, 'Test user\'s final OpenID URL was deleted.  It should not have been.'
        assert 'http://localhost:{0}/id/flooftest2</label>'.format(PORT) not in response, 'Found an OpenID identity URL that should not have been.'

    def test_certificates(self):
        """Test generation, viewing, downloading and revocation of SSL certificates."""
        # Test generation
        response = self.app.get(
                url(controller='controls', action='certificates'),
                extra_environ=self.default_environ,
                )
        assert 'Generate New Certificate' in response, 'Could not find the anticipated page title.'
        for days, time in [(31, '30 days, 23 hours'), (366, '365 days, 23 hours')]:
            response = self.app.post(
                    url(controller='controls', action='certificates_server', name=self.user.name),
                    params=[
                        ('days', days),
                        ('passphrase', u'1234'),
                        ('generate_server', u'Generate On Server'),
                        ],
                    extra_environ=self.default_environ,
                    )
            assert response.content_type == 'application/x-pkcs12', 'Anticipated a response MIME type of "application/x-pkcs12", got {0}'.format(response.content_type)
            pkcs12 = ssl.load_pkcs12(response.response.content, u'1234')
            # TODO: Test pkcs12 further... ?

        # Test viewing details
        response = self.app.get(
                url(controller='controls', action='certificates_details', id=2),
                extra_environ=self.default_environ,
                )
        assert 'Certificate ID 2' in response, 'Unable to find appropriate time to expiry for new certificate.'
        assert 'OU=Users, CN={0}'.format(self.user.name) in response, 'Unable to find appropriate Subject field.'
        assert 'X509v3 Authority Key Identifier:' in response, 'Unable to find Authority Key Identifier X.509 extension.'
        assert 'X509v3 Subject Key Identifier:' in response, 'Unable to find Subject Key Identifier X.509 extension.'
        assert """
            X509v3 Basic Constraints: 
                CA:FALSE
            X509v3 Key Usage: critical
                Digital Signature
            X509v3 Extended Key Usage: critical
                TLS Web Client Authentication\n""" in response, 'Unable to find anticipated X.509 extensions.'

        # Test revocation
        response = self.app.get(
                url(controller='controls', action='certificates_revoke', id=1),
                extra_environ=self.default_environ,
                )
        assert 'Permanently Revoke Certificate ID 1' in response, 'Unable to find anticipated heading in page.'
        response = self.app.post(
                url(controller='controls', action='certificates_revoke', user=self.user.name, id=1),
                params=[('ok', u'Revoke Certificate')],
                extra_environ=self.default_environ,
                )
        response = self.app.get(
                url(controller='controls', action='certificates'),
                extra_environ=self.default_environ,
                )
        assert url(controller='controls', action='certificates_details', id=1) in response, 'Revoked cert not found on certificates pasge at all/'
        assert url(controller='controls', action='certificates_revoke', id=1) not in response, 'Revocation link found for supposedly revoked certificate.'


    def test_cert_auth_change(self):
        """Test changing the user certificate authentication option."""
        response = self.app.get(
                url(controller='controls', action='authentication'),
                extra_environ=self.default_environ,
                )
        assert 'selected="selected" value="disabled"' in response, 'Could not find evidence of anticipated default value.'
        response = self.app.post(
                url(controller='controls', action='authentication'),
                params=[
                    ('confirm', u'Confirm Authentication Method Change'),
                    ('cert_auth', u'required')
                    ],
                extra_environ=self.default_environ,
                )
        response = self.app.get(
                url(controller='controls', action='authentication'),
                extra_environ=self.default_environ,
                )
        assert 'selected="selected" value="disabled"' in response, 'Allowed change to method requiring a certificate when user has no certificates.'
        response = self.app.post(
                url(controller='controls', action='certificates_server', name=self.user.name),
                params=[
                    ('days', 31),
                    ('generate_server', u'Generate On Server'),
                    ],
                extra_environ=self.default_environ,
                )
        response = self.app.post(
                url(controller='controls', action='authentication'),
                params=[
                    ('confirm', u'Confirm Authentication Method Change'),
                    ('cert_auth', u'required')
                    ],
                extra_environ=self.default_environ,
                )
        response = self.app.get(
                url(controller='controls', action='authentication'),
                extra_environ=self.default_environ,
                )
        assert 'selected="selected" value="disabled"' in response, 'Allowed change to method requiring a certificate when user did not present one in request.'
        user = meta.Session.query(model.User).filter_by(id=self.user.id).one()
        assert len(user.valid_certificates) > 0, 'User does not appear to have any valid certificates, even though we just created one.'
        serial = user.valid_certificates[0].serial
        environ = copy.deepcopy(self.default_environ)
        environ['tests.auth_cert_serial'] = serial
        response = self.app.post(
                url(controller='controls', action='authentication'),
                params=[
                    ('confirm', u'Confirm Authentication Method Change'),
                    ('cert_auth', u'required')
                    ],
                extra_environ=environ,
                )
        response = self.app.get(
                url(controller='controls', action='authentication'),
                extra_environ=environ,
                )
        assert 'selected="selected" value="required"' in response, 'The authentication method did not appear to update.'

    def test_reauth(self):
        """Test re-authentication redirection sequence."""
        environ = copy.deepcopy(self.default_environ)
        environ['tests.auth_openid_time'] = 0.0  # Set it to the epoch; definitely invalid
        response = self.app.get(
                url(controller='controls', action='authentication'),
                extra_environ=self.default_environ,
                status=200,
                )
        assert 'selected="selected" value="disabled"' in response, 'Expected existing cert_auth value of "disabled" not found.'

        # Pretend to try to change our cert_auth options while our auth is too old
        response = self.app.post(
                url(controller='controls', action='authentication'),
                params=[('cert_auth', u'allowed')],
                extra_environ=environ,
                status=303,
                )
        # We should be redirected to the login/re-auth page
        try:
            return_key = parse_qs(urlparse(response.headers['location'])[4])['return_key'][0]
        except ValueError:
            raise AssertionError('Return key not in login GET request.')
        response = self.app.get(response.headers['location'], extra_environ=environ)
        assert 'you need to re-authenticate' in response, 'Did not appear to give a message about the need to re-authenticate.'
        assert 'name="openid_identifier"' in response, 'Did not appear to prompt for OpenID URL.'
        assert 'value="{0}"'.format(return_key) in response, 'Could not find the return key hidden input in the login page.'

        # Spoof a successful OpenID login
        spoofer = self.spoofer
        spoofer.update(user=u'user', accept=True)
        user = meta.Session.query(model.User).filter_by(id=self.user.id).one()
        idurl = model.IdentityURL()
        idurl.url = spoofer.url
        user.identity_urls.append(idurl)
        meta.Session.commit()
        response = self.app.post(
                url(controller='account', action='login_begin'),
                params=[
                    ('return_key', return_key),
                    ('openid_identifier', idurl.url),
                ],
                extra_environ=environ,
                status=303,
                )
        location = response.headers['location']
        try:
            return_url = parse_qs(urlparse(location)[4])['openid.return_to'][0]
        except ValueError:
            raise AssertionError('Return URL not in OpenID OP login request.')
        path, params = spoofer.spoof(location)
        assert path == url(controller='account', action='login_finish'), 'Unexpected redirect path: {0}'.format(path)
        assert 'return_key={0}'.format(return_key) in params, 'Return key did not appear in the OpenID redirect URL.'
        del environ['tests.auth_openid_time']  # Allow c.auth.openid_time to be reset by the re-auth
        response = self.app.get(
                path,
                params=params,
                extra_environ=environ,
                status=303,
                )

        # We should now be redirected to the Authentication Options page,
        # with the contents of our original POST set as the
        # default/selected parameters.
        pu = urlparse(response.headers['location'])
        path, params = pu[2], pu[4]
        assert path == url(controller='controls', action='authentication'), 'Unexpected redirect path: {0}'.format(path)
        assert 'return_key={0}'.format(return_key) in params, 'Return key did not appear in the post-re-auth redirect URL.'
        response = self.app.get(
                path,
                params=params,
                extra_environ=environ,
                status=200,
                )
        assert 'selected="selected" value="allowed"' in response, 'POST\'d choice prior to re-auth did not appear to persist.'
