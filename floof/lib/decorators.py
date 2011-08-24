import functools
from inspect import getargspec
import logging

from decorator import decorator

from floof.lib.auth import stash_request
from floof.lib.helpers import flash, redirect
from floof.model import meta
from floof import model

log = logging.getLogger(__name__)

def user_must(priv):
    """Decorator to automatically abort if a user isn't permissed enough."""
    # This decorator uses functions from Pylons and is probably no longer
    # necessary.
    raise NotImplementedError(
            "This hasn't been updated for Pyramid yet (and may be"
            "inappropriate for Pyramid anyway).")
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
