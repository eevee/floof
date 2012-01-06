import logging
import urllib

from openid.consumer.consumer import Consumer
from openid.consumer.consumer import CANCEL, FAILURE, SUCCESS
from openid.extensions.sreg import SRegRequest, SRegResponse
from openid.extensions.draft.pape5 import Request as PAPERequest, Response as PAPEResponse
from openid.store.filestore import FileOpenIDStore
from openid.yadis.discover import DiscoveryFailure
from urllib2 import HTTPError, URLError

from floof.lib.webfinger import finger
from floof.lib.stash import key_from_request

log = logging.getLogger(__name__)

openid_store = FileOpenIDStore('/var/tmp')

class OpenIDError(RuntimeError):
    pass

FAKE_WEBFINGER_DOMAINS = {
    # Google does support webfinger, but only if you have a vanity Google
    # Profile URL, which doesn't seem to exist for Google+ users, and is
    # totally different from the thing below anyway.  ???????
    'gmail.com': 'https://www.google.com/accounts/o8/id',
    #'yahoo.com': 'http://me.yahoo.com/',
    'aol.com': 'http://openid.aol.com/{0}',
    'steamcommunity.com': 'http://steamcommunity.com/openid/',
    'livejournal.com': 'http://{0}.livejournal.com',
    'wordpress.com': 'http://{0}.wordpress.com/',
    'blogger.com': 'http://{0}.blogger.com/',
    'blogspot.com': 'http://{0}.blogspot.com/',
    'myspace.com': 'http://myspace.com/{0}',
}

def resolve_webfinger(address):
    """Attempt to extract an OpenID, given a webfinger address."""
    if u'@' not in address:
        return

    user, domain = address.rsplit(u'@', 1)
    if domain in FAKE_WEBFINGER_DOMAINS:
        # XXX possibly phishable or something since this goes into domain name
        # Do our best to mitigate this: a) strip RFC-3986 "gen-delims" and
        # b) URL encode.  Need to strip "gen-delims" since Python seemed to be
        # re-constituting the '/' when it was merely encoded, and presumably
        # may do so for other reserved characters.
        user = urllib.quote(user.encode('utf-8').strip(':/?#[]@'), safe='~')
        return FAKE_WEBFINGER_DOMAINS[domain].format(user)

    try:
        result = finger(address)
    except URLError:
        raise OpenIDError(
            "I can't connect to '{0}'.  Is it down?  Do you have another service you can try?".format(domain))
    except HTTPError:
        raise OpenIDError(
            "It doesn't look like '{0}' supports webfinger.".format(domain))
    except Exception as exc:
        raise OpenIDError(
            "Something hilariously broken happened and I don't know what.  Sorry.  :(")

    if not result.open_id:
        raise OpenIDError(
            "The address '{0}' doesn't have an OpenID associated with it.".format(address))

    return result.open_id

def openid_begin(identifier, return_url, request, max_auth_age=False, sreg=False):
    """Step one of logging in with OpenID; we resolve a webfinger,
    if present, then redirect to the provider.

    Set sreg to True to attempt to retrieve Simple Registration
    information.

    Set max_auth_age to a number of seconds to request the OP to
    ensure that the user authenticated within that many seconds prior
    to the request, or else force immediate re-authentication."""

    session = request.session
    openid_url = identifier

    # Does it look like an email address?
    # If so, try finding an OpenID URL via Webfinger.
    webfinger_openid = resolve_webfinger(identifier)
    if webfinger_openid:
        openid_url = webfinger_openid
        session['pending_identity_webfinger'] = identifier
        session.save()

    cons = Consumer(session=session, store=openid_store)

    print 1
    try:
        auth_request = cons.begin(openid_url)
    except DiscoveryFailure:
        # XXX this error blows
        raise OpenIDError(
            "Can't connect to '{0}'.  It might not support OpenID.".format(openid_url))
    print 2

    if sreg:
        sreg_req = SRegRequest(optional=['nickname', 'email', 'timezone'])
        auth_request.addExtension(sreg_req)

    if max_auth_age is not False and max_auth_age >= 0:
        auth_age_req = PAPERequest(max_auth_age=max_auth_age)
        auth_request.addExtension(auth_age_req)

    print 3
    # XXX is this realm stuff correct
    # ^^^ AFAICT, yes, as long as we don't need the assertion to be valid for
    # sub-domains
    new_url = auth_request.redirectURL(
            return_to=return_url,
            realm=request.host_url,
            )
    print new_url
    return new_url

def openid_end(return_url, request):
    """Step two of logging in; the OpenID provider redirects back here."""

    cons = Consumer(session=request.session, store=openid_store)
    host = request.headers['host']
    params = request.params

    if 'return_key' in params and not key_from_request(request):
        # We've followed a return_key that has terminated at the OpenID request
        # i.e. this is a stashed OpenID request; the OpenID request will
        # therefore NOT have the return_key in its return_to URL, so strip it
        log.debug("OpenID check stripping stale return_key(s) '{0}'"
                  .format(params.getall('return_key')))
        # Janrain OpenID treats params as a normal dict, so it's safe to lose
        # the MultiDict here (AFAICT).
        params = dict((k, v) for k, v in params.iteritems() if k != 'return_key')

    res = cons.complete(params, return_url)

    if res.status == SUCCESS:
        pass

    elif res.status == FAILURE:
        # The errors are, very helpfully, plain strings.  Nevermind that
        # there's a little hierarchy of exception classes inside the openid
        # library; they all get squashed into homogenous goo in the return
        # value.  Fucking awesome.  Check for a few common things here and
        # assume the rest are wacky internal errors
        log.error('openid failure: ' + res.message)

        if res.message == 'Nonce already used or out of range':
            # You tend to get this if you hit refresh on login_finish
            raise OpenIDError("Sorry!  Your login attempt expired; please start over.")
        else:
            raise OpenIDError("Something has gone hilariously wrong.")

    elif res.status == CANCEL:
        raise OpenIDError("Looks like you canceled the login.")

    else:
        log.error("Unexpected OpenID return status '{0}' with message '{1}'"
                  .format(res.status, res.message))
        raise OpenIDError("Something has gone hilariously wrong.")

    identity_url = unicode(res.identity_url)
    identity_webfinger = request.session.pop('pending_identity_webfinger', None)

    sreg_res = SRegResponse.fromSuccessResponse(res) or dict()
    pape_res = PAPEResponse.fromSuccessResponse(res)
    auth_time = pape_res.auth_time

    return identity_url, identity_webfinger, auth_time, sreg_res
