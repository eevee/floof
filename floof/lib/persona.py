from __future__ import absolute_import

import logging

from ssl import SSLError

import browserid

log = logging.getLogger(__name__)


class PersonaError(Exception):
    msg = 'Unspecified error attempting to verify your Persona login.'
class PersonaSSLError(PersonaError, SSLError):
    msg = 'Connection to authentication server failed or timed out.'
class PersonaConnectionError(PersonaError, browserid.errors.ConnectionError):
    msg = 'Unable to connect to verifying server to verify your Persona '\
          'assertion.'
class PersonaTrustError(PersonaError, browserid.errors.TrustError):
    msg = 'Your Persona assertion was not valid.'
class PersonaExpiredSignatureError(PersonaTrustError, browserid.errors.ExpiredSignatureError):
    msg = 'Your Persona assertion expired.  Please try again.'
class PersonaInvalidSignatureError(PersonaTrustError, browserid.errors.InvalidSignatureError):
    msg = 'Your Persona signature was invalid'
class PersonaInvalidIssuerError(PersonaTrustError, browserid.errors.InvalidIssuerError):
    msg = 'Your Persona issuer is not trusted by this website.'
class PersonaAudienceMismatchError(PersonaTrustError, browserid.errors.AudienceMismatchError):
    msg = 'Your Persona assertion does not appear to have been made for this '\
          'site.'
class PersonaUnspecifiedError(PersonaError, browserid.errors.Error):
    msg = 'Encountered an unspecified error while attempting to verify your '\
          'Persona assertion.'


EXC_MAP = {
    SSLError: PersonaSSLError,
    KeyError: PersonaUnspecifiedError,
    ValueError: PersonaUnspecifiedError,
    browserid.errors.ConnectionError: PersonaConnectionError,
    browserid.errors.InvalidSignatureError: PersonaTrustError,
    browserid.errors.ExpiredSignatureError: PersonaExpiredSignatureError,
    browserid.errors.InvalidSignatureError: PersonaInvalidSignatureError,
    browserid.errors.InvalidIssuerError: PersonaInvalidIssuerError,
    browserid.errors.AudienceMismatchError: PersonaAudienceMismatchError,
    browserid.errors.Error: PersonaUnspecifiedError,
}


def verify_persona(assertion, request, flash_errors=False):
    verifier = browserid.verifiers.remote.RemoteVerifier()
    audience = request.registry.settings.get('auth.persona.audience')

    if not audience:
        log.warning("Config key 'auth.persona.audience' is missing or "
                    "blank; Persona authentication will fail.")

    if 'paste.testing' in request.environ:
        alternative = request.environ.get('tests.auth.persona.verifier')
        verifier = alternative or verifier
        alternative = request.environ.get('tests.auth.persona.audience')
        audience = alternative or audience

    try:
        if assertion is None:
            raise ValueError
        data = verifier.verify(assertion, audience)
    except Exception as e:
        if e.__class__ in EXC_MAP:
            raise EXC_MAP[e.__class__](*e.args)
        raise

    # XXX Possibly superfluous -- I think PyPersona does this.
    if data.get('status') != 'okay':
        raise PersonaTrustError("Persona authentication failed.")

    return data


def flash_persona_error(exc, request):
    if exc.__class__ == PersonaUnspecifiedError:
        log.warning('Unspecified Persona failure: {0}'.format(exc.args))

    if hasattr(exc, 'msg'):
        request.session.flash(exc.msg, level=u'error', icon='key--exclamation')
    else:
        raise exc
