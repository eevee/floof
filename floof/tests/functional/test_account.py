from floof import model
from floof.model import meta
from floof.tests import *
import floof.tests.sim as sim

class TestAccountController(TestController):
    
    @classmethod
    def setup_class(cls):
        """Creates a user to be used as a fake login."""
        cls.user = sim.sim_user()
        meta.Session.commit()

        # Force a refresh of the user, to get id populated
        # XXX surely there's a better way!
        meta.Session.refresh(cls.user)

    def test_login(self):
        """Test display of login page."""
        response = self.app.get(
                url(controller='account', action='login'),
                )
        assert 'Log in or register' in response, 'Anticipated heading not found in login page.'

    def test_logins(self):
        """Test logging in with various ``cert_auth` values, using mechanism overrides."""
        runsheet = dict(
                disabled=[
                    ('logged_out', []),
                    ('pending', ['cert']),
                    ('logged_in', ['openid']),
                    ('logged_in', ['cert', 'openid']),
                    ],
                allowed=[
                    ('logged_out', []),
                    ('logged_in', ['cert']),
                    ('logged_in', ['openid']),
                    ('logged_in', ['cert', 'openid']),
                    ],
                sensitive_required=[
                    ('logged_out', []),
                    ('logged_in', ['cert']),
                    ('logged_in', ['openid']),
                    ('logged_in', ['cert', 'openid']),
                    ],
                required=[
                    ('logged_out', []),
                    ('logged_in', ['cert']),
                    ('pending', ['openid']),
                    ('logged_in', ['cert', 'openid']),
                    ],
               )
        response = self.app.get(url('/'))
        assert 'Log in or register' in response, 'Page does not appear logged out even when no auth data should be present.'
        response = self.app.post(
                url(controller='controls', action='certificates_server', name=self.user.name),
                params=[
                    ('days', 31),
                    ('generate_server', u'Generate On Server'),
                    ],
                extra_environ={'tests.user_id': self.user.id},
                )
        user = meta.Session.query(model.User).filter_by(id=self.user.id).one()
        assert len(user.certificates) == 1, 'Expected user to have exactly one certificate, found {0}'.format(len(user.certificates))
        serial = user.certificates[0].serial
        for cert_auth in runsheet:
            user.cert_auth = cert_auth
            meta.Session.commit()
            for test in runsheet[cert_auth]:
                result, mechs = test
                extra = dict()
                if 'cert' in mechs:
                    extra['tests.auth_cert_serial'] = serial
                if 'openid' in mechs:
                    extra['tests.auth_openid_uid'] = user.id
                response = self.app.post(url(controller='account', action='logout'))
                response = self.app.get(url('/'), extra_environ=extra)
                if 'Hello, <a href=' in response:
                    assert result == 'logged_in', 'Wound up in state "logged_in", wanted "{0}", for cert_auth "{1}" with authed mechanisms: {2}'.format(result, cert_auth, mechs)
                if 'Complete log in for {0}'.format(user.name) in response:
                    assert result == 'pending', 'Wound up in state "pending", wanted "{0}", for cert_auth "{1}" with authed mechanisms: {2}'.format(result, cert_auth, mechs)
                if 'Log in or register' in response:
                    assert result == 'logged_out', 'Wound up in state "logged_out", wanted "{0}", for cert_auth "{1}" with authed mechanisms: {2}'.format(result, cert_auth, mechs)

    def test_login_cert_invalid(self):
        """Test automatic fallback to "allowed" if the user has no valid certs."""
        user = meta.Session.query(model.User).filter_by(id=self.user.id).one()
        user.cert_auth = u'required'
        meta.Session.commit()
        response = self.app.post(
                url(controller='account', action='logout'),
                expect_errors=True,
                )
        response = self.app.get(
                url('/'),
                extra_environ={'tests.auth_openid_uid': self.user.id},
                )
        assert 'Hello, <a href=' in response, 'Expected to be logged in, but do not appear to be.'
