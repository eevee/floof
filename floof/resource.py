from pyramid.security import Allow, Deny
from pyramid.security import Authenticated, Everyone

class FloofRoot(dict):
    __name__ = ''
    __parent__ = None

    __acl__ = [
        (Deny, 'banned:interact_with_others', (
            'art.rate',
            'comments.add',
            'tags.add',
        )),

        (Allow, Authenticated, '__authenticated__'),

        (Allow, 'role:user', (
            'art.upload', 'art.rate',
            'comments.add',
            'tags.add', 'tags.remove',
        )),

        (Allow, 'trusted_for:auth', (
            'auth.method', 'auth.certificates', 'auth.openid')),

        (Allow, 'trusted_for:admin', ('admin.view')),
    ]
