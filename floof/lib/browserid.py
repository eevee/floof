import logging

from functools import partial
from ssl import SSLError

import vep

log = logging.getLogger(__name__)


class BrowserIDRemoteVerifier(vep.RemoteVerifier):
    """Add a timeout to :class:`vep.RemoteVerifier`"""
    def __init__(self, *args, **kwargs):
        urlopen = partial(vep.utils.secure_urlopen, timeout=5)
        vep.RemoteVerifier.__init__(self, *args, urlopen=urlopen, **kwargs)


class BrowserIDError(Exception): pass
class BrowserIDSSLError(BrowserIDError, SSLError): pass
class BrowserIDConnectionError(BrowserIDError, vep.errors.ConnectionError): pass
class BrowserIDTrustError(BrowserIDError, vep.errors.TrustError): pass
class BrowserIDExpiredSignatureError(BrowserIDTrustError, vep.errors.ExpiredSignatureError): pass
class BrowserIDInvalidSignatureError(BrowserIDTrustError, vep.errors.InvalidSignatureError): pass
class BrowserIDInvalidIssuerError(BrowserIDTrustError, vep.errors.InvalidIssuerError): pass
class BrowserIDAudienceMismatchError(BrowserIDTrustError, vep.errors.AudienceMismatchError): pass
class BrowserIDUnspecifiedError(BrowserIDError, vep.errors.Error): pass


EXC_MAP = {
    SSLError: BrowserIDSSLError,
    ValueError: BrowserIDUnspecifiedError,
    vep.errors.ConnectionError: BrowserIDConnectionError,
    vep.errors.InvalidSignatureError: BrowserIDTrustError,
    vep.errors.ExpiredSignatureError: BrowserIDExpiredSignatureError,
    vep.errors.InvalidSignatureError: BrowserIDInvalidSignatureError,
    vep.errors.InvalidIssuerError: BrowserIDInvalidIssuerError,
    vep.errors.AudienceMismatchError: BrowserIDAudienceMismatchError,
    vep.errors.Error: BrowserIDUnspecifiedError,
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
    verifier = BrowserIDRemoteVerifier()
    audience = request.registry.settings.get('auth.browserid.audience')

    if not audience:
        log.warning("Config key 'auth.browserid.audience' is missing or "
                    "blank; BrowserID authentication will fail.")

    if 'paste.testing' in request.environ:
        alternative = request.environ.get('tests.auth.browserid.verifier')
        verifier = alternative or verifier

    try:
        data = verifier.verify(assertion, audience)
    except Exception as e:
        if e.__class__ in EXC_MAP:
            raise EXC_MAP[e.__class__](*e.args)
        raise

    print "BrowserID response:", data

    # XXX Possibly superfluous -- I think PyVEP does this.
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
