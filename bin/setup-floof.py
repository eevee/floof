"""Setup the floof application"""
from datetime import datetime, timedelta
import logging
import os
import pytz
import sys

from floof.model import meta
from floof import model

import OpenSSL.crypto as ssl
from paste.deploy import appconfig
from sqlalchemy import engine_from_config
import transaction
from zope.sqlalchemy import ZopeTransactionExtension

log = logging.getLogger(__name__)

def setup_floof(conf, model, meta, is_test=False):
    """Place any commands to setup floof here"""
    if is_test:
        # Drop all existing tables during a test
        meta.metadata.drop_all(checkfirst=True)

    # Create the tables if they don't already exist
    meta.metadata.create_all(checkfirst=True)

    # Add canonical privileges and roles
    privileges = dict(
        (name, model.Privilege(name=name, description=description))
        for name, description in [
            (u'admin.view',         u'Can view administrative tools/panel'),
            (u'auth.certificates',  u'Can manage own client certificates'),
            (u'auth.method',        u'Can manage own authentication method'),
            (u'auth.openid',        u'Can manage own OpenID URLs'),
            (u'art.upload',         u'Can upload art'),
            (u'art.rate',           u'Can rate art'),
            (u'comments.add',       u'Can post comments'),
            (u'tags.add',           u'Can add tags with no restrictions'),
            (u'tags.remove',        u'Can remove tags with no restrictions'),
        ]
    )

    base_user = model.Role(
        name=u'user',
        description=u'Basic user',
        privileges=[privileges[priv] for priv in [
            u'auth.certificates', u'auth.method', u'auth.openid',
            u'art.upload', u'art.rate', u'comments.add', u'tags.add',
            u'tags.remove',
        ]],
    )
    admin_user = model.Role(
        name=u'admin',
        description=u'Administrator',
        privileges=privileges.values()
    )

    meta.Session.add_all([base_user, admin_user])

    ### Client SSL/TLS certificate stuff
    # Generate the CA.  Attempt to load it from file first.
    generate_ca = True
    cert_dir = conf.local_conf['client_cert_dir']
    for filename in ['ca.pem', 'ca.key']:
        filepath = os.path.join(cert_dir, filename)
        if os.path.isfile(filepath):
            generate_ca = False
            break
    if generate_ca:
        now = datetime.now(pytz.utc)
        expire = now + timedelta(days=3653)
        site_title = conf.local_conf['site_title']

        ca_key = ssl.PKey()
        ca_key.generate_key(ssl.TYPE_RSA, 2048)

        ca = ssl.X509()
        ca.set_version(2)  # Value 2 means v3
        ca.set_serial_number(1)
        ca.get_subject().organizationName = site_title
        ca.get_subject().commonName = 'Client Certificate CA'
        ca.set_notBefore(now.strftime('%Y%m%d%H%M%SZ'))
        ca.set_notAfter(expire.strftime('%Y%m%d%H%M%SZ'))
        ca.set_issuer(ca.get_subject())
        ca.set_pubkey(ca_key)
        ca.add_extensions([
                ssl.X509Extension('subjectKeyIdentifier', False, 'hash', ca),
                ssl.X509Extension('basicConstraints', True, 'CA:TRUE'),
                ssl.X509Extension('keyUsage', True, 'cRLSign, keyCertSign'),
                ])
        ca.sign(ca_key, 'sha256')

        if not os.path.isdir(cert_dir):
            os.makedirs(cert_dir)
        with open(os.path.join(cert_dir, 'ca.key'), 'w') as f:
            f.write(ssl.dump_privatekey(ssl.FILETYPE_PEM, ca_key))
        with open(os.path.join(cert_dir, 'ca.pem'), 'w') as f:
            f.write(ssl.dump_certificate(ssl.FILETYPE_PEM, ca))
        print """  New SSL Client Certificate CA generated at {0}
  ENSURE that {1} has appropriately restrictive access permissions!""".format(
                os.path.join(cert_dir, 'ca.pem'),
                os.path.join(cert_dir, 'ca.key'),
                )
    else:
        print "  Encountered existing CA certificate file {0}".format(filepath)
        # Breifly test the found files
        with open(os.path.join(cert_dir, 'ca.key'), 'rU') as f:
            ca_key = ssl.load_privatekey(ssl.FILETYPE_PEM, f.read())
        with open(os.path.join(cert_dir, 'ca.pem'), 'rU') as f:
            ca_cert = ssl.load_certificate(ssl.FILETYPE_PEM, f.read())
        print "  Will use this file as the SSL Client Certificate CA."

if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print 'usage: python {0} config-file.ini#app-name'.format(sys.argv[0])
        sys.exit(0)

    ini_spec = os.path.abspath(sys.argv[1])
    conf = appconfig('config:' + ini_spec)
    engine = engine_from_config(conf, 'sqlalchemy.')
    model.meta.Session.configure(bind=engine, extension=ZopeTransactionExtension())
    model.TableBase.metadata.bind = engine

    setup_floof(conf, model, meta)

    # XXX: This may be bad juju
    transaction.commit()
