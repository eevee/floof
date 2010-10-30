from pylons import tmpl_context as c
from pylons.controllers.util import abort
from decorator import decorator

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
        if not c.user.can(priv):
            abort(403)
        return f(*a, **kw)
    return deco
