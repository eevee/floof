import itertools

from functools import partial

from pyramid.security import Authenticated, Everyone
from pyramid.testing import DummyRequest

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
        self.env = partial(sim.sim_user_env, self.user)

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
        env = self.env('cert')
        request = create_authn_request(self.config, environ=env)
        principals = self.policy.effective_principals(request)
        assert 'role:user' in principals

    def test_principals_secure(self):
        env = self.env('cert')
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
        authn_flags = ['cert', 'openid']
        additional_flags = ['openid_recent']
        all_flags = authn_flags + additional_flags

        for i in xrange(len(all_flags)):
            for combo in itertools.combinations(all_flags, i + 1):
                env = self.env(*combo)
                request = create_authn_request(self.config, environ=env)
                principals = self.policy.effective_principals(request)

                if not any([f for f in combo if f in authn_flags]):
                    # With no flags from authn_flags, no user should resolve
                    assert principals == set([Everyone])
                    continue

                assert Everyone in principals
                assert Authenticated in principals
                assert 'user:{0}'.format(self.user.id) in principals

                for mech in combo:
                    flag = 'trusted:{0}'.format(mech)
                    if mech.endswith('_recent') and mech[:-7] not in combo:
                        assert flag not in principals
                    else:
                        assert flag in principals

    def test_principal_derivation_trustedfor_auth(self):
        pass

    def test_principal_derivation_trustedfor_admin(self):
        pass
