from pyramid.security import Authenticated

from floof.tests import UnitTests

from floof.lib.authz import FloofACLAuthorizationPolicy, PrivCheck
from floof.resource import contextualize


class Resource(object):
    pass


class Discussion(object):
    def __init__(self, resource):
        self.resource = resource


class Comment(object):
    def __init__(self, discussion, user_id):
        self.discussion = discussion
        self.author_user_id = user_id



class TestFloofACLAuthzPolicy(UnitTests):

    def setUp(self):
        super(TestFloofACLAuthzPolicy, self).setUp()
        self.policy = FloofACLAuthorizationPolicy()

    def test_comment_tree(self):
        resource = Resource()
        discussion = Discussion(resource)
        comment = Comment(discussion, 10)
        contextualize(comment)

        runsheet = (
            (True, [Authenticated, 'role:admin', 'user:1', 'auth:secure', 'cred:cert']),
            (True, [Authenticated, 'role:moderator', 'user:2', 'auth:secure', 'cred:cert']),
            (False, [Authenticated, 'role:curator', 'user:3', 'auth:secure', 'cred:cert']),
            (True, [Authenticated, 'role:user', 'user:10', 'auth:secure', 'cred:cert']),
            (True, [Authenticated, 'role:user', 'user:10', 'cred:openid']),
            (True, [Authenticated, 'role:user', 'user:10', 'cred:oauth', 'scope:roundhouse', 'scope:comment']),
            (False, [Authenticated, 'role:user', 'user:10', 'cred:oauth', 'scope:art', 'scope:roundhouse']),
            (False, [Authenticated, 'role:user', 'user:42', '-cred:oauth', 'auth:secure', 'cred:cert']),
            (False, [Authenticated, 'role:user', 'user:42', 'cred:oauth', 'scope:comment']),
        )
        for outcome, principals in runsheet:
            assert self.policy.permits(comment, principals, 'comment.edit') == outcome

    def test_root(self):
        class Boring(object): pass
        obj = Boring()
        contextualize(obj)

        runsheet = (
            (True, '__authenticated__', [Authenticated, 'role:user', 'user:10', 'cred:browserid']),
            # Admin powers
            (True, 'admin.view', [Authenticated, 'role:admin', 'user:1', 'auth:secure', 'cred:cert']),
            (False, 'admin.view', [Authenticated, 'role:admin', 'user:1', 'auth:secure', 'cred:openid']),
            (False, 'admin.view', [Authenticated, 'role:admin', 'user:1', 'auth:insecure', 'cred:cert']),
            (False, 'admin.view', [Authenticated, 'role:moderator', 'user:2', 'auth:secure', 'cred:cert']),
            (False, 'admin.view', [Authenticated, 'role:user', 'user:10', 'auth:secure', 'cred:cert']),
            # Auth mechanism changes
            (True, 'auth.method', [Authenticated, 'role:admin', 'user:1', 'auth:insecure', 'cred:cert']),
            (True, 'auth.method', [Authenticated, 'role:moderator', 'user:2', 'auth:secure', 'cred:cert']),
            (True, 'auth.method', [Authenticated, 'role:user', 'user:10', 'auth:secure', 'cred:cert']),
            (True, 'auth.method', [Authenticated, 'role:user', 'user:10', 'auth:insecure', 'cred:openid', 'cred:openid_recent']),
            (False, 'auth.method', [Authenticated, 'role:user', 'user:10', 'auth:insecure', 'cred:openid']),
            (False, 'auth.method', [Authenticated, 'role:user', 'user:10', 'auth:insecure', 'cred:oauth', 'scope:art']),
            (False, 'auth.method', [Authenticated, 'role:user', 'user:10', 'auth:secure', 'cred:openid']),
            (False, 'auth.method', [Authenticated, 'role:admin', 'user:10', 'auth:secure', 'cred:browserid']),
            # General
            (True, 'art.upload', [Authenticated, 'role:user', 'user:10', 'auth:insecure', 'cred:openid']),
        )
        for outcome, permission, principals in runsheet:
            assert self.policy.permits(obj, principals, permission) == outcome

    def test_synthetic_tree(self):
        # TODO
        pass


class TestPrivCheck(UnitTests):
    def test_principals(self):
        runsheet = (
            (
                dict(role='admin', trusted_for='admin'),
                [
                    ['role:admin', '-cred:oauth', 'auth:secure', 'cred:cert'],
                ]
            ),
            (
                dict(role='moderator', trusted_for='admin'),
                [
                    ['role:admin', '-cred:oauth', 'auth:secure', 'cred:cert'],
                    ['role:moderator', '-cred:oauth', 'auth:secure', 'cred:cert'],
                ]
            ),
            (
                dict(role='user', user_id=42, scope='art'),
                [
                    ['role:admin', 'user:42', '-cred:oauth'],
                    ['role:admin', 'user:42', 'scope:art'],
                    ['role:moderator', 'user:42', '-cred:oauth'],
                    ['role:moderator', 'user:42', 'scope:art'],
                    ['role:curator', 'user:42', '-cred:oauth'],
                    ['role:curator', 'user:42', 'scope:art'],
                    ['role:user', 'user:42', '-cred:oauth'],
                    ['role:user', 'user:42', 'scope:art'],
                ]
            ),
        )
        for kwargs, principals in runsheet:
            pc = PrivCheck(**kwargs)
            assert pc.principals == principals

    def test_delta(self):
        # TODO
        # For now, see delta's doctests:
        import doctest
        from floof.lib import authz
        failures, total = doctest.testmod(authz)
        assert not failures
        assert total > 0

    def test_call(self):
        # TODO
        pass
