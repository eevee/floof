"""Setup the floof application"""
import logging
import os

import pylons.test

from floof.config.environment import load_environment
from floof.model import meta
from floof import model

from datetime import datetime, timedelta
import OpenSSL.crypto as ssl

log = logging.getLogger(__name__)

def setup_app(command, conf, vars):
    """Place any commands to setup floof here"""
    # Don't reload the app if it was loaded under the testing environment
    if not pylons.test.pylonsapp:
            load_environment(conf.global_conf, conf.local_conf)

    ### DB stuff
    meta.metadata.bind = meta.engine

    _, conf_file = os.path.split(conf.filename)
    if conf_file == 'test.ini':
        # Drop all existing tables during a test
        meta.metadata.drop_all(checkfirst=True)

    # Create the tables if they don't already exist
    meta.metadata.create_all(checkfirst=True)

    # Add canonical privileges and roles
    privileges = dict(
        (name, model.Privilege(name=name, description=description))
        for name, description in [
            (u'admin.view',         u'Can view administrative tools/panel'),
            (u'art.upload',         u'Can upload art'),
            (u'art.rate',           u'Can rate art'),
            (u'comments.add',       u'Can post comments'),
            (u'tags.add',           u'Can add tags with no restrictions'),
            (u'tags.remove',        u'Can remove tags with no restrictions'),
        ]
    )
    upload_art = model.Privilege(name=u'upload_art', description=u'Can upload art')
    write_comment = model.Privilege(name=u'write_comment', description=u'Can post comments')
    admin_priv = model.Privilege(name=u'admin', description=u'Can administrate')

    base_user = model.Role(
        name=u'user',
        description=u'Basic user',
        privileges=[privileges[priv] for priv in [
            u'art.upload', u'art.rate', u'comments.add', u'tags.add', u'tags.remove',
        ]],
    )
    admin_user = model.Role(
        name=u'admin',
        description=u'Administrator',
        privileges=privileges.values()
    )

    meta.Session.add_all([base_user, admin_user])
    meta.Session.commit()

    ### Client SSL/TLS certificate stuff

    # Generate the CA.  Only bother if we have a directory in which to put it.
    # And skip if we already appear to have a CA.
    build_ca = True
    cert_dir = conf.local_conf.get('client_cert_dir', None)
    if cert_dir is None:
        build_ca = False
    else:
        for filename in ['ca.key', 'ca.pem']:
            filepath = os.path.join(cert_dir, filename)
            if os.path.isfile(filepath):
                build_ca = False
                print "  Encountered existing file {0}".format(filepath)
                print "  Will not generate an SSL Client Certificate CA."
                break

    if build_ca:
        if not os.path.isdir(cert_dir):
            os.makedirs(cert_dir)

        now = datetime.utcnow()
        expire = now + timedelta(days=3654)

        ca_key = ssl.PKey()
        ca_key.generate_key(ssl.TYPE_RSA, 2048)

        ca = ssl.X509()
        ca.set_version(2)  # Value 2 means v3
        ca.set_serial_number(1)
        ca.get_subject().organizationName = 'Floof'
        ca.get_subject().commonName = 'Floof Client Certificate CA'
        ca.set_issuer(ca.get_subject())
        ca.set_notBefore(now.strftime('%Y%m%d%H%M%SZ'))
        ca.set_notAfter(expire.strftime('%Y%m%d%H%M%SZ'))
        ca.set_pubkey(ca_key)

        ca.add_extensions([
                ssl.X509Extension('subjectKeyIdentifier', False, 'hash', ca),
                ssl.X509Extension('basicConstraints', True, 'CA:TRUE'),
                ssl.X509Extension('keyUsage', True, 'cRLSign, keyCertSign'),
                ])

        ca.sign(ca_key, 'sha1')

        with open(os.path.join(cert_dir, 'ca.key'), 'w') as f:
            f.write(ssl.dump_privatekey(ssl.FILETYPE_PEM, ca_key))
        with open(os.path.join(cert_dir, 'ca.pem'), 'w') as f:
            f.write(ssl.dump_certificate(ssl.FILETYPE_PEM, ca))

        print "  SSL Client Certificate CA generated at {0}" \
                .format(os.path.join(cert_dir, 'ca.pem'))

