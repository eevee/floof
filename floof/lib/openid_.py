from openid.consumer.consumer import Consumer
from openid.consumer.consumer import CANCEL, FAILURE, SUCCESS
from openid.extensions.sreg import SRegRequest, SRegResponse
from openid.extensions.draft.pape5 import Request as PAPERequest, Response as PAPEResponse
from openid.store.filestore import FileOpenIDStore
from openid.yadis.discover import DiscoveryFailure
from urllib2 import HTTPError, URLError

from floof.lib.webfinger import finger

openid_store = FileOpenIDStore('/var/tmp')

class OpenIDError(RuntimeError):
    pass

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
    if len(identifier.split('@')) == 2:
        result = None
        try:
            result = finger(identifier)
        except URLError:
            raise OpenIDError(
                    "Attemted to resolve identifier '{0}' via Webfinger, but hit a URLError.  "
                    "Is the email address invalid?"
                    .format(identifier)
                    )
        except HTTPError:
            raise OpenIDError(
                    "Attemted to resolve identifier '{0}' via Webfinger, but hit an HTTPError.  "
                    "Does the host support Webfinger?"
                    .format(identifier)
                    )
        except Exception as exc:
            raise OpenIDError(
                    "Attemted to resolve identifier '{0}' via Webfinger, but hit the following unusual error: "
                    "'{1}'  "
                    "Does the host use an old Webfinger format?"
                    .format(identifier, exc)
                    )
        if result and result.open_id is not None:
            session['pending_identity_webfinger'] = identifier
            session.save()
            openid_url = result.open_id

    cons = Consumer(session=session, store=openid_store)

    print 1
    try:
        auth_request = cons.begin(openid_url)
    except DiscoveryFailure:
        raise OpenIDError(
                "Can't connect to '{0}'.  Are you sure it's a valid OpenID URL or webfinger-enabled email address?"
                .format(openid_url)
                )
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
    res = cons.complete(request.params, return_url)

    if res.status == SUCCESS:
        pass
    elif res.status == FAILURE:
        raise OpenIDError(res.message)
    elif res.status == CANCEL:
        raise OpenIDError("OpenID transaction cancelled by user.")
    else:
        raise OpenIDError("Unanticaipated response status.")

    identity_url = unicode(res.identity_url)
    identity_webfinger = request.session.pop('pending_identity_webfinger', None)

    sreg_res = SRegResponse.fromSuccessResponse(res) or dict()
    pape_res = PAPEResponse.fromSuccessResponse(res)
    auth_time = pape_res.auth_time

    return identity_url, identity_webfinger, auth_time, sreg_res
