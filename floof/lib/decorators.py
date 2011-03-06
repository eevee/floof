import functools
from inspect import getargspec
import logging

from pylons import request, session, tmpl_context as c, url
from pylons.controllers.util import abort
from decorator import decorator

from floof.lib.auth import stash_request
from floof.lib.helpers import flash, redirect
from floof.model import meta
from floof import model

log = logging.getLogger(__name__)

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
        success, reason = c.auth.can(priv, log=True)
        if not success:
            if reason == 'no_privilege':
                log.debug('User attempted to perform an action for which they '
                        'lacked the privilege ({0})'.format(priv))
                abort(403, detail='User does not have permission to perform this action')
            if reason == 'cert_auth_required':
                log.debug('Action requiring cert auth attempted without cert.')
                flash('For security, you need to authenticate with a '
                        'certificate to perform this action.',
                        level='error'
                        )
                abort(403, detail='Cert error')
            elif reason == 'cert_auth_option_too_weak':
                log.debug('Action requiring cert auth enforcement on '
                        'sensitive operations attempted without such '
                        'enforcement enabled.')
                flash('For security, you need to configure your authentication '
                        'options to require certificates for sensitive '
                        'operations (or for all logins) to perform this action.',
                        level='error'
                        )
                abort(403, detail='Cert auth option too weak')
            elif reason == 'openid_reauth_required':
                log.debug('OpenID auth refresh required for attempted action.')
                flash('For security, you need to re-authenticate to perform this action.',
                        level='notice'
                        )
            elif reason == 'no_user':
                log.debug('Login required for attempted action.')
                flash('You must log in to perform this action.',
                        level='notice'
                        )
            # Redirect for OpenID re-auth, stashing the current URL and
            # POST (if any) for later retrieval with fetch_stash(session, key)
            post_data = request.POST if request.method == 'POST' else None
            key = stash_request(session, url.current(), post_data)
            redirect(url(controller='account', action='login', return_key=key))
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
