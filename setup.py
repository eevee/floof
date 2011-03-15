try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name='floof',
    version='0.1',
    description='',
    author='',
    author_email='',
    url='',
    install_requires=[
        "Pylons>=1.0",
        "WebHelpers>=1.0",
        "SQLAlchemy>=0.6.6",
        'python-openid',
        'wtforms',
        'python-magic',
        'PIL',
        'sqlalchemy-migrate>=0.6',
        'pytz',
        'iso8601',
        # We need pyOpenSSL to be at least 0.11 for CRL support.
        # At the time of writing, easy_install chokes on pyOpenSSL > 0.10. Try:
        # $ wget http://launchpad.net/pyopenssl/main/0.11/+download/pyOpenSSL-0.11.tar.gz
        # $ easy_install pyOpenSSL-0.11.tar.gz
        'pyOpenSSL>=0.11',
    ],
    setup_requires=["PasteScript>=1.6.3"],
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    test_suite='nose.collector',
    package_data={'floof': ['i18n/*/LC_MESSAGES/*.mo']},
    #message_extractors={'floof': [
    #        ('**.py', 'python', None),
    #        ('templates/**.mako', 'mako', {'input_encoding': 'utf-8'}),
    #        ('public/**', 'ignore', None)]},
    zip_safe=False,
    paster_plugins=['PasteScript', 'Pylons'],
    entry_points="""
    [paste.app_factory]
    main = floof.config.middleware:make_app

    [paste.app_install]
    main = pylons.util:PylonsInstaller
    """,
)
