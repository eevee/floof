"""
Provides functions for manipulating the session stash.

The stash is a way of holding arbitrary values in the session that are
automatically retrieved when certain conditions are met.  Retrieval involves
the automatic attachment of the specific stash to the request (as
request.stash) when:

 1) The current path equals a stash's set path; and
 2) Either:
    a) The stash's key equals the return_key parameter in the request; or
    b) The stash's value for '__immediate__' evaluates True.

If stash is attached to the request, then it is automatically dropped from the
session; that is, stashes may only be automatically activated once.

Generally, a stash with a True '__immediate__' flag would be used to save POST
data for a form prior to a redirect, say after a validation error, where the
page redirected to would immediately use the stashed data.

A stash with a False '__immediate__' flag would be used to save POST data
before redirecting to a re-authentication attempt.

Forms that subclass floof.forms.FloofForm will automatically set their default
values to any held in the post attribute of the active stash (i.e. attached to
request.stash)

"""
import logging
import random

log = logging.getLogger(__name__)

def manage_stashes(event):
    """Performs automatic stash management; run on ContextFound."""
    request = event.request
    current_stash = fetch_stash(request)

    if current_stash and (current_stash['path'] == request.path or
                          current_stash['__immediate__']):
        # Stick a copy of the stash in the request then drop the stash
        request.stash = current_stash
        drop_stash(request)
    else:
        request.stash = None

def stash_request(request, _route_name=None, _immediate=False, **kwargs):
    """Stash the request's path and any POST data in request's session.
    Returns a key that may be used to retrieve the stash later.

    The request's path must be unique among all stashes within a single
    session.  A new stash request with a conflicting path will silently
    clobber the existing stash with that path.

    """
    stashes = request.session.setdefault('request_stashes', dict())

    if _route_name is not None:
        path = request.route_path(_route_name)
        url = request.route_url(_route_name)
    else:
        path = request.path
        url = request.url

    # Clear any old pending stashes against this path
    duplicates = [k for k in stashes if stashes[k]['path'] == path]
    for key in duplicates:
        del stashes[key]

    key = str(random.getrandbits(80))

    stashes[key] = dict(
        path=path,
        post=request.POST,
        url=url,
    )
    stashes[key].update(**kwargs)
    stashes[key]['__immediate__'] = _immediate

    request.session.changed()
    return key

def get_stash_keys(request):
    return request.session.get('request_stashes', dict()).keys()

def key_from_request(request):
    """Returns request.params['return_key'] if it exists and is a valid key.

    Otherwise returns None.
    Additionally, if the parameter exists but is invalid, a warning is logged.

    """
    key = request.params.get('return_key')
    stashes = request.session.get('request_stashes', dict())

    if key in (None, ''):
        return None

    if key in stashes:
        return key

    log.warning("Unknown return_key value: {0!r}".format(key))

def _fetch_stash(request, key=None):
    key = key or key_from_request(request)
    stashes = request.session.get('request_stashes', dict())

    if key in stashes:
        return key, stashes[key]

    # Try to locate a stash with an appropriate path, but only match if it is
    # flagged as __immediate__.
    for key, stash in stashes.items():
        if stash['path'] == request.path and stash['__immediate__']:
            return key, stash

    return None, None

def fetch_stash(request, key=None):
    key, stash = _fetch_stash(request, key)
    return stash

def drop_stash(request, key=None):
    key, stash = _fetch_stash(request, key)
    stashes = request.session.get('request_stashes', dict())
    if key in stashes:
        del stashes[key]
