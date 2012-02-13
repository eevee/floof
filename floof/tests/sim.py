import pytz
import random
import string
import time

from datetime import datetime, timedelta

from floof import model
from floof.lib.setup import gen_ca_certs

# XXX The idea here is that we generate random junk data to use (and print the
# seed at the start of a test run), ensuring over time that the actual format
# of data doesn't break the app.  Like really slow fuzzing.
# But, for now, the constant values below were determined to be sufficiently
# random.

def sim_user(credentials=None, roles=None):
    """Create a user suitable for use in testing.

    Parameters:

        `credentials` is a sequence of (auth_mechanism, credential) tuples,
        where auth_mechanism is one of 'openid' or 'cert' and credential is the
        OpenID URL when paired with 'openid' and ignored when paired with
        'cert'.  If not specified, will default to:
        ``[('cert', None), ('openid', 'https://example.com/'), ('browserid',
        '<username>@example.org')]``

        `roles` is a sequence of user role names to which to add the user.
        Defaults to u'user'.

    """
    username = 'sim_' + ''.join(random.choice(string.letters) for n in range(10))

    if credentials is None:
        credentials = [
                ('cert', None),
                ('openid', 'https://example.com/'),
                ('browserid', '{0}@example.com'.format(username))
                ]
    if roles is None:
        roles = [u'user']

    user = model.User(
        name=username,
        resource=model.Resource(type=u'users'),
    )
    model.session.add(user)

    for role in roles:
        r = model.session.query(model.Role).filter_by(name=role).one()
        user.roles.append(r)

    for mech, credential in credentials:
        if mech == 'cert':
            title = 'Test'
            now = datetime.now(pytz.utc)
            expire = now + timedelta(days=3)

            cert = model.Certificate(user, *gen_ca_certs(title, now, expire))
            user.certificates.append(cert)
            user.cert_auth = 'allowed'

        elif mech == 'openid':
            openid = model.IdentityURL(url=credential)
            user.identity_urls.append(openid)

        elif mech == 'browserid':
            browserid = model.IdentityEmail(email=credential)
            user.identity_emails.append(browserid)

        else:
            print ("Unknown mech '{0}' specified in credentials on sim user "
                   "creation.".format(mech))

    model.session.flush()

    return user


def sim_user_env(user, *trust_flags):
    """
    Generates a set of environment variables to authenticate as the given user.

    This function uses "real" authentication credentials, so the specified user
    must have valid credentials of all the requested types, or else IndexError
    will be raised.

    To gain authentication flags without needing real backing credentials, add
    the desired cert_flags directly to the tests.auth_trust environment
    variable.  Note that this alternate method will not test large parts of
    floof's authn code.

    """
    env = {'paste.testing': True}

    if 'cert' in trust_flags:
        env['tests.auth.cert_serial'] = user.certificates[0].serial

    if 'openid' in trust_flags:
        env['tests.auth.openid_url'] = user.identity_urls[0].url
        env['tests.auth.openid_timestamp'] = 1

    if 'openid_recent' in trust_flags:
        env['tests.auth.openid_timestamp'] = time.time()

    if 'browserid' in trust_flags:
        env['tests.auth.browserid_email'] = user.identity_emails[0].email
        env['tests.auth.browserid_timestamp'] = 1

    if 'browserid_recent' in trust_flags:
        env['tests.auth.browserid_timestamp'] = time.time()

    return env


def sim_artwork(user):
    artwork = model.MediaImage(
        title = ''.join(random.choice(string.letters) for i in xrange(10)),
        hash = '123',
        uploader = user,
        original_filename = 'dummy.jpg',
        mime_type = 'image/jpeg',
        file_size = 1234,
        resource = model.Resource(type=u'artwork'),

        height = 100,
        width = 100,
        number_of_colors = 256,
    )
    model.session.add(artwork)
    return artwork

def sim_tag():
    tag = model.Tag(name=u'foo')
    model.session.add(tag)
    return tag
