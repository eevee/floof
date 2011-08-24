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
        "WebHelpers>=1.0",
        "SQLAlchemy>=0.7",
        'python-openid',
        'wtforms',
        'python-magic',
        'PIL',
        'sqlalchemy-migrate>=0.6',
        'pytz',
        'iso8601',
        'pyOpenSSL>=0.11',
        'pyramid>=1.1',
        'pyramid_beaker',
        'repoze.tm2>=1.0b1',  # default_commit_veto
        'WebError',
        'zope.sqlalchemy',
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
    paster_plugins=['PasteScript', 'pyramid'],
    entry_points="""
    [paste.app_factory]
    main = floof.config.middleware:make_app
    pyramid = floof.app:main

    [paste.app_install]
    main = pylons.util:PylonsInstaller
    """,
)
