from pyramid.security import Allow, Deny
from pyramid.security import Authenticated, Everyone

# NB: As Floof uses URL Dispatch, the resource tree provides only authorization
# information

def contextualize(ormobj, name=None):
    """Attaches an ORM object to a resource tree by adding attributes.

    Currently just shoves everything immediately under FloofRoot.

    """
    if name is None:
        name = ormobj.__class__.__name__ + ':' + str(ormobj.id)

    parent = FloofRoot()
    parent[name] = ormobj
    ormobj.__name__ = name
    ormobj.__parent__ = parent

    return ormobj

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

    def __init__(self, request=None):
        pass
