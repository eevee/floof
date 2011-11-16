import itertools
import time

from pyramid.security import Authenticated, Everyone
from pyramid.testing import DummyRequest

from floof.model import meta
from floof.tests import UnitTests
from floof.tests import sim

from floof.lib.auth import Authenticizer, FloofAuthnPolicy

def create_authn_request(config, params=None, environ=None):
    request = DummyRequest(
            registry=config.registry, params=params, environ=environ)
    request.auth = Authenticizer(request)
    return request

class TestFloofAuthnPolicy(UnitTests):

    def setUp(self):
        """Creates a user to be used as a fake login."""
        super(TestFloofAuthnPolicy, self).setUp()

        self.user = sim.sim_user()
        meta.Session.flush()

        self.policy = FloofAuthnPolicy()

        self.env_openid_old = {
                'tests.user_id': self.user.id,
                'tests.auth_trust': ['openid'],
                }

        self.env_openid_recent = {
                'tests.user_id': self.user.id,
                'tests.auth_trust': ['openid', 'openid_recent'],
                }

    def test_principals_unauthenticated(self):
        request = create_authn_request(self.config)
        principals = self.policy.effective_principals(request)

        assert Everyone in principals
        assert len(principals) == 1

    def test_principals_role(self):
        env = {
                'tests.user_id': self.user.id,
                'tests.auth_trust': ['cert'],
                }
        request = create_authn_request(self.config, environ=env)
        principals = self.policy.effective_principals(request)
        assert 'role:user' in principals

    def test_principals_secure(self):
        env = {
                'tests.user_id': self.user.id,
                'tests.auth_trust': ['cert'],
                }
        request = create_authn_request(self.config, environ=env)

        methods = {
                u'disabled': 'insecure',
                u'allowed': 'insecure',
                u'sensitive_required': 'secure',
                u'required': 'secure',
                }

        for method, nature in methods.iteritems():
            self.user.cert_auth = method
            principals = self.policy.effective_principals(request)
            assert 'auth:{0}'.format(nature) in principals

    def test_principals_trusted(self):
        def makeone(auth_trust):
            env = {
                'tests.user_id': self.user.id,
                'tests.auth_trust': auth_trust,
                }
            request = create_authn_request(self.config, environ=env)
            return self.policy.effective_principals(request)

        trust_flags = ['cert', 'openid', 'openid_recent']

        for i in xrange(len(trust_flags)):
            for auth_trust in itertools.combinations(trust_flags, i + 1):
                principals = makeone(auth_trust)

                assert Everyone in principals
                assert Authenticated in principals
                assert 'user:{0}'.format(self.user.id) in principals

                for mech in auth_trust:
                    assert 'trusted:{0}'.format(mech) in principals

    def test_principal_derivation_trustedfor_auth(self):
        pass

    def test_principal_derivation_trustedfor_admin(self):
        pass
