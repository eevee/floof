"""Setup the floof application"""

import logging
import os
import pytz
import OpenSSL.crypto as ssl

from datetime import datetime, timedelta

from floof import model

log = logging.getLogger(__name__)

def populate_db(metadata, session, is_test=False):
    """Place any commands to setup floof here"""
    if is_test:
        # Drop all existing tables during a test
        metadata.drop_all(checkfirst=True)

    # Create the tables if they don't already exist
    metadata.create_all(checkfirst=True)

    # Add canonical roles
    roles = [
        (u'admin', u'Administrator'),
        (u'user', u'Basic user'),
    ]
    role_objs = [model.Role(name=n, description=d) for n, d in roles]
    session.add_all(role_objs)
    session.flush()

def generate_ca(conf):

    ### Client SSL/TLS certificate stuff
    # Generate the CA.  Attempt to load it from file first.
    generate_ca = True
    cert_dir = conf.local_conf['auth.certs.directory']
    for filename in ['ca.pem', 'ca.key']:
        filepath = os.path.join(cert_dir, filename)
        if os.path.isfile(filepath):
            generate_ca = False
            break

    if generate_ca:
        # Found no existing CA key or cert; generate new ones
        now = datetime.now(pytz.utc)
        expire = now + timedelta(days=3653)
        site_title = conf.local_conf['site_title']

        # Generate a new private key
        ca_key = ssl.PKey()
        ca_key.generate_key(ssl.TYPE_RSA, 2048)

        # Generate a new (public) CA certificate from the key
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

        # Save the new key and certificate out to files
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
        # Found existing CA files; briefly test them
        print "  Encountered existing CA certificate file {0}".format(filepath)
        with open(os.path.join(cert_dir, 'ca.key'), 'rU') as f:
            ca_key = ssl.load_privatekey(ssl.FILETYPE_PEM, f.read())
        with open(os.path.join(cert_dir, 'ca.pem'), 'rU') as f:
            ca_cert = ssl.load_certificate(ssl.FILETYPE_PEM, f.read())
        print "  Will use this file as the SSL Client Certificate CA."
