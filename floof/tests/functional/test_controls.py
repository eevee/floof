import copy
import hashlib
import OpenSSL.crypto as ssl
import time

from openid import oidutil
from urlparse import parse_qs, urlparse

from floof import model
from floof.lib.helpers import friendly_serial
from floof.tests import FunctionalTests
import floof.tests.openidspoofer as oidspoof
import floof.tests.sim as sim

PORT = 19614
DATA_PATH = '/tmp'

# Hook OpenID's stderr log to stop it spewing all over our nosetest
def null_log(message, level=0):
    pass
oidutil.log = null_log

class TestControls(FunctionalTests):

    def setUp(self):
        """Creates a user to be used as a fake login."""
        super(TestControls, self).setUp()

        self.user = sim.sim_user()
        model.session.flush()

        self.default_environ = {
                'tests.user_id': self.user.id,
                'tests.auth_trust': ['openid', 'openid_recent'],
                }

    @classmethod
    def setUpClass(cls):
        cls.spoofer = oidspoof.OpenIDSpoofer('localhost', PORT, DATA_PATH)

    @classmethod
    def tearDownClass(cls):
        del cls.spoofer

    def test_index(self):
        """Test display of user controls index."""
        response = self.app.get(
                self.url('controls.index'),
                extra_environ={'tests.user_id': self.user.id},
                )
        assert 'Index' in response
        # Test response...

    def test_user_info(self):
        """Test modification of basic user info options."""
        response = self.app.get(
                self.url('controls.info'),
                extra_environ={'tests.user_id': self.user.id},
                )
        assert 'Display name' in response, 'User Info control page does not appear to have loaded.'

        # Test setting some new user details
        test_email = u'abc@example.org'
        response = self.app.post(
                self.url('controls.info'),
                params=[
                    ('display_name', u'Barack Obama'),
                    ('timezone', u'US/Eastern'),
                    ('email', test_email),
                ],
                extra_environ={'tests.user_id': self.user.id},
                )
        model.session.flush()
        response = self.app.get(
                self.url('controls.info'),
                extra_environ={'tests.user_id': self.user.id},
                )
        assert 'Barack Obama' in response, 'Failed to set display name.'
        assert 'selected="selected" value="US/Eastern"' in response, 'Failed to set timezone.'

        # TODO: Test normalization of the display name

        # Test Gravatar
        response = self.app.get(
                self.url('users.view', user=self.user),
                extra_environ={'tests.user_id': self.user.id},
                )
        assert hashlib.md5(test_email.encode()).hexdigest() in response, 'Failed to generate appropriate Gravatar.'

    def test_openids(self):
        """Test display of user OpenID controls page."""
        response = self.app.get(
                self.url('controls.openid'),
                extra_environ=self.default_environ,
                )
        assert 'OpenID Identity Settings' in response, 'OpenID control page does not appear to have loaded.'

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
                    self.url('controls.openid.add'),
                    params=[
                        ('new_openid', spoofer.url),
                    ],
                    extra_environ=self.default_environ,
                    )
            location = response_begin.headers['location']
            path, params = spoofer.spoof(location)
            assert path is not None
            response_finish = self.app.get(
                    path,
                    params=params,
                    extra_environ=self.default_environ,
                    status=303,
                    )
            location = response_finish.headers['location']
            response_end = self.app.get(
                    location,
                    extra_environ=self.default_environ,
                    status=200,
                    )
            responses.append(response_end)
        assert ':{0}/id/flooftest1</option>'.format(PORT) in responses[0], 'Addition of OpenID identity URL failed.'
        assert ':{0}/id/flooftest2</option>'.format(PORT) not in responses[0], 'App appears to have guessed our next OpenID URL....'
        assert ':{0}/id/flooftest1</option>'.format(PORT) in responses[1], 'Addition of OpenID identity URL was not retained.'
        assert ':{0}/id/flooftest2</option>'.format(PORT) in responses[1], 'Addition of second OpenID identity URL failed.'

        # Test denial of double-entries
        response_begin = self.app.post(
                self.url('controls.openid.add'),
                params=[
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
        oid = model.session.query(model.IdentityURL) \
                .filter_by(url=spoofer.url) \
                .one()
        response = self.app.post(
                self.url('controls.openid.remove'),
                params=[
                    ('openids', oid.id),
                ],
                extra_environ=self.default_environ,
                status=303,
                )
        location = response.headers['location']
        response_end = self.app.get(
                location,
                extra_environ=self.default_environ,
                status=200,
                )
        assert ':{0}/id/flooftest1</option>'.format(PORT) in response_end, 'An OpenID identity URL that should have been found was not.'
        assert ':{0}/id/flooftest2</option>'.format(PORT) not in response_end, 'Deletion of OpenID identity URL failed.'

        # Test rejection of deletion of final OpenID URL
        q = model.session.query(model.IdentityURL).filter_by(user_id=self.user.id)
        assert q.count() < 2, 'Test user has more that one OpenID URL, when they should not.'
        assert q.count() > 0, 'Test user no OpenID URLs, when they should have one.'
        oid = q.one()
        response = self.app.post(
                self.url('controls.openid.remove'),
                params=[
                    ('openids', oid.id),
                ],
                extra_environ=self.default_environ,
                status=200,
                )
        assert ':{0}/id/flooftest1</option>'.format(PORT) in response, 'Test user\'s final OpenID URL was deleted.  It should not have been.'
        assert ':{0}/id/flooftest2</option>'.format(PORT) not in response, 'Found an OpenID identity URL that should not have been.'

    def test_certificates(self):
        """Test generation, viewing, downloading and revocation of SSL certificates."""
        # Test generation
        response = self.app.get(
                self.url('controls.certs'),
                extra_environ=self.default_environ,
                )
        assert 'Generate New Certificate' in response, 'Could not find the anticipated page title.'

        times = ((31, '30 days, 23 hours'), (366, '365 days, 23 hours'))
        serials = []
        for days, time in times:
            response = self.app.post(
                    self.url('controls.certs.generate_server', name=self.user.name),
                    params=[
                        ('days', days),
                        ('passphrase', u'1234'),
                        ('generate_server', u'Generate On Server'),
                        ],
                    extra_environ=self.default_environ,
                    )
            assert response.content_type == 'application/x-pkcs12', 'Anticipated a response MIME type of "application/x-pkcs12", got {0}'.format(response.content_type)
            pkcs12 = ssl.load_pkcs12(response.body, u'1234')
            serials.append('{0:x}'.format(pkcs12.get_certificate().get_serial_number()))
            # TODO: Test pkcs12 further... ?

        # Test viewing details
        response = self.app.get(
                self.url('controls.certs.details', serial=serials[1]),
                extra_environ=self.default_environ,
                )
        assert friendly_serial(serials[1]) in response, 'Unable to find new certificate details page serial.'
        assert 'OU=Users, CN={0}'.format(self.user.name) in response, 'Unable to find appropriate Subject field.'
        assert 'X509v3 Authority Key Identifier:' in response, 'Unable to find Authority Key Identifier X.509 extension.'
        assert 'X509v3 Subject Key Identifier:' in response, 'Unable to find Subject Key Identifier X.509 extension.'
        assert """
            X509v3 Basic Constraints: critical
                CA:FALSE
            X509v3 Key Usage: critical
                Digital Signature
            X509v3 Extended Key Usage: critical
                TLS Web Client Authentication\n""" in response, 'Unable to find anticipated X.509 extensions.'

        # Test revocation
        response = self.app.get(
                self.url('controls.certs.revoke', serial=serials[0]),
                extra_environ=self.default_environ,
                )
        assert 'Permanently Revoke Certificate <span class="monospace">{0}'.format(friendly_serial(serials[0])) in response, 'Unable to find anticipated heading in page.old'
        assert 'Permanently Revoke Certificate <span class="monospace">{0}</span>'.format(friendly_serial(serials[0])) in response, 'Unable to find anticipated heading in page.'
        response = self.app.post(
                self.url('controls.certs.revoke', serial=serials[0]),
                params=[('ok', u'Revoke Certificate')],
                extra_environ=self.default_environ,
                )
        response = self.app.get(
                self.url('controls.certs'),
                extra_environ=self.default_environ,
                )
        assert self.url('controls.certs.details', serial=serials[0]) in response, 'Revoked cert not found on certificates page at all.'
        assert self.url('controls.certs.revoke', serial=serials[0]) not in response, 'Revocation link found for supposedly revoked certificate.'


    def test_cert_auth_change(self):
        """Test changing the user certificate authentication option."""
        environ = copy.deepcopy(self.default_environ)
        environ['tests.auth_trust'] = ['cert']
        response = self.app.get(
                self.url('controls.auth'),
                extra_environ=self.default_environ,
                )
        assert 'selected="selected" value="disabled"' in response, 'Could not find evidence of anticipated default value.'

        response = self.app.post(
                self.url('controls.auth'),
                params=[
                    ('cert_auth', u'required')
                    ],
                extra_environ=self.default_environ,
                )
        response = self.app.get(
                self.url('controls.auth'),
                extra_environ=self.default_environ,
                )
        cert_auth = model.session.query(model.User).filter_by(id=self.user.id).one().cert_auth
        assert cert_auth == u'disabled', 'Allowed change to method requiring a certificate when user has no certificates.'

        environ['tests.auth_trust'] = ['openid', 'openid_recent']
        response = self.app.post(
                self.url('controls.certs.generate_server', name=self.user.name),
                params=[
                    ('days', 31),
                    ('generate_server', u'Generate On Server'),
                    ],
                extra_environ=environ,
                )
        response = self.app.post(
                self.url('controls.auth'),
                params=[
                    ('cert_auth', u'required')
                    ],
                extra_environ=environ,
                )
        response = self.app.get(
                self.url('controls.auth'),
                extra_environ=environ,
                )
        cert_auth = model.session.query(model.User).filter_by(id=self.user.id).one().cert_auth
        assert cert_auth == u'disabled', 'Allowed change to method requiring a certificate when user did not present one in request.'
        user = model.session.query(model.User).filter_by(id=self.user.id).one()
        assert len(user.valid_certificates) > 0, 'User does not appear to have any valid certificates, even though we just created one.'

        environ['tests.auth_trust'] = ['cert']
        response = self.app.post(
                self.url('controls.auth'),
                params=[
                    ('cert_auth', u'required')
                    ],
                extra_environ=environ,
                )
        response = self.app.get(
                self.url('controls.auth'),
                extra_environ=environ,
                )
        cert_auth = model.session.query(model.User).filter_by(id=self.user.id).one().cert_auth
        assert cert_auth == u'required', 'The authentication method did not appear to update.'

    def test_reauth(self):
        """Test re-authentication redirection sequence."""
        response = self.app.get(
                self.url('controls.auth'),
                extra_environ=self.default_environ,
                status=200,
                )
        assert 'selected="selected" value="disabled"' in response, 'Expected existing cert_auth value of "disabled" not found.'

        # Pretend to try to change our cert_auth options while our auth is too old
        environ = copy.deepcopy(self.default_environ)
        environ['tests.auth_trust'] = ['openid']
        response = self.app.post(
                self.url('controls.auth'),
                params=[('cert_auth', u'allowed')],
                extra_environ=environ,
                status=303,
                )
        # We should be redirected to the login/re-auth page
        try:
            return_key = parse_qs(urlparse(response.headers['location'])[4])['return_key'][0]
        except KeyError:
            raise AssertionError('Return key not in login GET request.')
        response = self.app.get(response.headers['location'], extra_environ=environ)
        assert 'need to re-authenticate' in response, 'Did not appear to give a message about the need to re-authenticate.'
        assert 'name="openid_identifier"' in response, 'Did not appear to prompt for OpenID URL.'
        assert 'value="{0}"'.format(return_key) in response, 'Could not find the return key hidden input in the login page.'

        # Spoof a successful OpenID login
        spoofer = self.spoofer
        spoofer.update(user=u'user', accept=True)
        user = model.session.query(model.User).filter_by(id=self.user.id).one()
        idurl = model.IdentityURL()
        idurl.url = spoofer.url
        user.identity_urls.append(idurl)
        model.session.flush()
        response = self.app.post(
                self.url('account.login_begin'),
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
        assert path == self.url('account.login_finish'), 'Unexpected redirect path: {0}'.format(path)
        assert 'return_key={0}'.format(return_key) in params, 'Return key did not appear in the OpenID redirect URL.'
        #TODO actually make the re-auth influence the trust status
        response = self.app.get(
                path,
                params=params,
                extra_environ=environ,
                status=303,
                )

        # We should now be redirected to the Authentication Options page,
        # with the contents of our original POST set as the
        # default/selected parameters (but the actual change should not yet
        # have taken place).

        # XXX prefer to avoid setting this explictly
        environ['tests.auth_trust'].append('openid_recent')
        pu = urlparse(response.headers['location'])
        path, params = pu[2], pu[4]
        assert path == self.url('controls.auth'), 'Unexpected redirect path: {0}'.format(path)
        assert 'return_key={0}'.format(return_key) in params, 'Return key did not appear in the post-re-auth redirect URL.'

        # Submission should have been turned into a POST, so we should get
        # another redirect
        response = self.app.get(
                path,
                params=params,
                extra_environ=environ,
                status=303,
                )
        pu = urlparse(response.headers['location'])
        path, params = pu[2], pu[4]
        assert path == self.url('controls.auth'), 'Unexpected redirect path: {0}'.format(path)

        response = self.app.get(
                path,
                params=params,
                extra_environ=environ,
                status=200,
                )
        cert_auth = model.session.query(model.User).filter_by(id=self.user.id).one().cert_auth
        assert cert_auth != u'disabled', 'Failed to automatically submit a form after an OpenID re-auth detour.'
