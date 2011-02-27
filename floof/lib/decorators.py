import functools
from inspect import getargspec

from pylons import tmpl_context as c
from pylons.controllers.util import abort
from decorator import decorator

from floof.lib.helpers import flash
from floof.model import meta
from floof import model

@decorator
def logged_in(f, *a, **kw):
    """Decorator to automatically abort if a user isn't logged in."""
    if not c.user:
        abort(403)
    return f(*a, **kw)

@decorator
def logged_out(f, *a, **kw):
    """Decorator to automatically abort if a user is logged in."""
    if c.user:
        abort(403)
    return f(*a, **kw)

def user_must(priv):
    """Decorator to automatically abort if a user isn't permissed enough."""
    @decorator
    def deco(f, *a, **kw):
        if not c.user.can(priv, log=True):
            abort(403, detail="User does not have permission to perform this action")
        sensitive_privs = ('auth.', 'money.')
        print priv, c.auth.confidence_level
        if (priv.startswith('admin.') and c.auth.confidence_level < 2) or \
                (priv.startswith(sensitive_privs) and c.auth.confidence_level < 1):
            flash('You would have been denied as your assurance level '
                    'is only {0}'.format(c.auth.confidence_level),
                    level='error'
                    )
        return f(*a, **kw)
    return deco

def user_action(f):
    """Decorator to transform a username into a user object."""
    @functools.wraps(f)
    def wrap(self, name, **kwargs):
        q = meta.Session.query(model.User)
        user = q.filter_by(name=name).first()
        if user is None:
            abort(404)
        c.this_user = user
        kw = dict((k, kwargs[k]) for k in getargspec(f).args if k not in ('self', 'user'))
        return f(self, user, **kw)
    return wrap
