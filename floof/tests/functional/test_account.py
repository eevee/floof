import time

from itertools import chain

from floof import model
from floof.tests import FunctionalTests
from floof.tests import sim


class TestAccount(FunctionalTests):

    def setUp(self):
        """Creates a user to be used as a fake login."""
        super(TestAccount, self).setUp()

        self.user = sim.sim_user()
        model.session.flush()

        self.default_environ = {
                'tests.user_id': self.user.id,
                'tests.auth_openid_uid': self.user.id,
                'tests.auth_openid_time': time.time(),
                }

    def test_login(self):
        """Test display of login page."""
        response = self.app.get(
                self.url('account.login'),
                )
        assert 'Log in or register' in response, 'Anticipated heading not found in login page.'

    def test_logins(self):
        """Test logging in with various ``cert_auth` values, using mechanism overrides."""
        externalids = [['openid']]
        cert_with_others = [
                ['cert', 'openid'],
                ]
        runsheet = dict(
                disabled=[
                    ('logged_out', ([], ['cert'])),
                    ('logged_in', chain(externalids, cert_with_others)),
                    ],
                allowed=[
                    ('logged_out', ([],)),
                    ('logged_in', chain(['cert'], externalids, cert_with_others)),
                    ],
                sensitive_required=[
                    ('logged_out', ([],)),
                    ('logged_in', chain(['cert'], externalids, cert_with_others)),
                    ],
                required=[
                    ('logged_out', chain([], externalids)),
                    ('logged_in', chain(['cert'], cert_with_others)),
                    ],
               )

        response = self.app.get(self.url('root'))
        assert 'Log in or register' in response, 'Page does not appear logged out even when no auth data should be present.'

        user = model.session.query(model.User).filter_by(id=self.user.id).one()
        assert len(user.certificates) == 1, 'Expected user to have exactly one certificate, found {0}. (Test setup error)'.format(len(user.certificates))

        for cert_auth in runsheet:
            user.cert_auth = cert_auth
            model.session.flush()

            for result, mech_combos in runsheet[cert_auth]:
                for mech_combo in mech_combos:
                    if isinstance(mech_combo, basestring):
                        # XXX is there a more elegant way?
                        mech_combo = [mech_combo]

                    extra = sim.sim_user_env(self.user, *mech_combo)
                    response = self.app.post(self.url('account.logout'))
                    response = self.app.get(self.url('root'), extra_environ=extra)

                    if 'Log in or register' in response:
                        assert result == 'logged_out', 'Wound up in state "logged_out", wanted "{0}", for cert_auth "{1}" with authed mechanisms: {2}'.format(result, cert_auth, mech_combo)
                    else:
                        assert result == 'logged_in', 'Wound up in state "logged_in", wanted "{0}", for cert_auth "{1}" with authed mechanisms: {2}'.format(result, cert_auth, mech_combo)

    def test_login_cert_invalid(self):
        """Test automatic fallback to "allowed" if the user has no valid certs."""
        user = model.session.query(model.User).filter_by(id=self.user.id).one()
        user.cert_auth = u'required'
        model.session.flush()
        response = self.app.post(
                self.url('account.logout'),
                expect_errors=True,
                )
        response = self.app.get(
                self.url('root'),
                extra_environ={'tests.auth_openid_uid': self.user.id},
                )
        assert 'Hello, ' in response, 'Expected to be logged in, but do not appear to be.'
