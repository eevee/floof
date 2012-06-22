from __future__ import absolute_import

import logging

from ssl import SSLError

import browserid

log = logging.getLogger(__name__)


class BrowserIDError(Exception): pass
class BrowserIDSSLError(BrowserIDError, SSLError): pass
class BrowserIDConnectionError(BrowserIDError, browserid.errors.ConnectionError): pass
class BrowserIDTrustError(BrowserIDError, browserid.errors.TrustError): pass
class BrowserIDExpiredSignatureError(BrowserIDTrustError, browserid.errors.ExpiredSignatureError): pass
class BrowserIDInvalidSignatureError(BrowserIDTrustError, browserid.errors.InvalidSignatureError): pass
class BrowserIDInvalidIssuerError(BrowserIDTrustError, browserid.errors.InvalidIssuerError): pass
class BrowserIDAudienceMismatchError(BrowserIDTrustError, browserid.errors.AudienceMismatchError): pass
class BrowserIDUnspecifiedError(BrowserIDError, browserid.errors.Error): pass


EXC_MAP = {
    SSLError: BrowserIDSSLError,
    KeyError: BrowserIDUnspecifiedError,
    ValueError: BrowserIDUnspecifiedError,
    browserid.errors.ConnectionError: BrowserIDConnectionError,
    browserid.errors.InvalidSignatureError: BrowserIDTrustError,
    browserid.errors.ExpiredSignatureError: BrowserIDExpiredSignatureError,
    browserid.errors.InvalidSignatureError: BrowserIDInvalidSignatureError,
    browserid.errors.InvalidIssuerError: BrowserIDInvalidIssuerError,
    browserid.errors.AudienceMismatchError: BrowserIDAudienceMismatchError,
    browserid.errors.Error: BrowserIDUnspecifiedError,
}


EXC_MSG = {
    BrowserIDSSLError:
        'Connection to authentication server failed or timed out.',
    BrowserIDConnectionError:
        'Unable to connect to verifying server to verify your BrowserID '
        'assertion.',
    BrowserIDTrustError:
        'Your BrowserID assertion was not valid.',
    BrowserIDExpiredSignatureError:
        'Your BrowserID assertion expired.  Please try again.',
    BrowserIDInvalidSignatureError:
        'Your BrowserID signature was invalid',
    BrowserIDInvalidIssuerError:
        'Your BrowserID issuer is not trusted by this website.',
    BrowserIDAudienceMismatchError:
        'Your BrowserID assertion does not appear to have been made for this '
        'site.',
    BrowserIDUnspecifiedError:
        'Encountered an unspecified error while attempting to verify your '
        'BrowserID assertion.',
}


def verify_browserid(assertion, request, flash_errors=False):
    print assertion
    verifier = browserid.verifiers.remote.RemoteVerifier()
    audience = request.registry.settings.get('auth.browserid.audience')

    if not audience:
        log.warning("Config key 'auth.browserid.audience' is missing or "
                    "blank; BrowserID authentication will fail.")

    if 'paste.testing' in request.environ:
        alternative = request.environ.get('tests.auth.browserid.verifier')
        verifier = alternative or verifier
        alternative = request.environ.get('tests.auth.browserid.audience')
        audience = alternative or audience

    try:
        if assertion is None:
            raise ValueError
        data = verifier.verify(assertion, audience)
    except Exception as e:
        if e.__class__ in EXC_MAP:
            raise EXC_MAP[e.__class__](*e.args)
        raise

    print "BrowserID response:", data

    # XXX Possibly superfluous -- I think PyBrowserID does this.
    if data.get('status') != 'okay':
        raise BrowserIDTrustError("BrowserID authentication failed.")

    return data


def flash_browserid_error(exc, request):
    if exc.__class__ == BrowserIDUnspecifiedError:
        log.warning('Unspecified BrowserID failure: {0}'.format(exc.args))

    if exc.__class__ in EXC_MSG:
        request.session.flash(EXC_MSG[exc.__class__], level=u'error',
                              icon='key--exclamation')
    else:
        raise exc
