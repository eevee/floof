import logging

from openid.consumer import consumer
from openid.extensions.sreg import SRegRequest, SRegResponse
from openid.extensions.draft.pape5 import Request as PAPERequest, Response as PAPEResponse
from openid.store.filestore import FileOpenIDStore
from openid.yadis.discover import DiscoveryFailure
from urllib2 import HTTPError, URLError

from floof.lib.webfinger import finger

log = logging.getLogger(__name__)

openid_store = FileOpenIDStore('/var/tmp')

class OpenIDError(RuntimeError):
    pass

FAKE_WEBFINGER_DOMAINS = {
    #'gmail.com': 'https://www.google.com/accounts/o8/id',
    #'yahoo.com': 'http://me.yahoo.com/',
    'aol.com': 'http://openid.aol.com/%s',
    'steamcommunity.com': 'http://steamcommunity.com/openid/',
    'livejournal.com': 'http://%s.livejournal.com',
    'wordpress.com': 'http://%s.wordpress.com/',
    'blogger.com': 'http://%s.blogger.com/',
    'blogspot.com': 'http://%s.blogspot.com/',
    'myspace.com': 'http://myspace.com/%s',
}

def resolve_webfinger(address):
    """Attempt to extract an OpenID, given a webfinger address."""
    if u'@' not in address:
        return

    user, domain = address.rsplit(u'@', 1)
    if domain in FAKE_WEBFINGER_DOMAINS:
        # XXX possibly phishable or something since this goes into domain name
        return FAKE_WEBFINGER_DOMAINS[domain] % (user,)

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
    print session

    cons = consumer.Consumer(session=session, store=openid_store)

    print 1
    try:
        auth_request = cons.begin(openid_url)
    except DiscoveryFailure:
        # XXX this error blows
        raise OpenIDError(
            "Can't connect to '{0}'.  It might not support OpenID.".format(openid_url))
    print 2

    if sreg:
        sreg_req = SRegRequest(optional=['nickname', 'email', 'dob', 'gender',
                                         'country', 'language', 'timezone'])
        auth_request.addExtension(sreg_req)
    if max_auth_age is not False and max_auth_age >= 0:
        auth_age_req = PAPERequest(max_auth_age=max_auth_age)
        auth_request.addExtension(auth_age_req)

    print 3
    # XXX is this realm stuff correct
    new_url = auth_request.redirectURL(
            return_to=return_url,
            realm=request.host_url,
            )
    print new_url
    return new_url

def openid_end(return_url, request):
    """Step two of logging in; the OpenID provider redirects back here."""

    cons = consumer.Consumer(session=request.session, store=openid_store)
    host = request.headers['host']
    res = cons.complete(request.params, return_url)

    if res.status == consumer.FAILURE:
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

    if res.status == consumer.CANCEL:
        raise OpenIDError("Looks like you canceled the login.")


    identity_url = unicode(res.identity_url)
    identity_webfinger = request.session.pop('pending_identity_webfinger', None)

    sreg_res = SRegResponse.fromSuccessResponse(res) or dict()
    pape_res = PAPEResponse.fromSuccessResponse(res)
    auth_time = pape_res.auth_time

    return identity_url, identity_webfinger, auth_time, sreg_res
