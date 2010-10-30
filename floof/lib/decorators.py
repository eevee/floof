from pylons import tmpl_context as c
from pylons.controllers.util import abort
from decorator import decorator

def user_must(priv):
    """Decorator to automatically abort if a user isn't permissed enough."""
    @decorator
    def deco(f, *a, **kw):
        if not c.user.can(priv):
            abort(403)
        return f(*a, **kw)
    return deco
