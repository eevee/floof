try:
    from setuptools import setup, find_packages, Command
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

import os.path

HERE = os.path.abspath(os.path.dirname(__file__))


class PyTest(Command):
    user_options = [('config=', 'c', 'floof paster configuration ini-spec')]

    def initialize_options(self):
        self.config = ''

    def finalize_options(self):
        if self.config:
            self.config = os.path.abspath(self.config)

    def run(self):
        import sys
        from subprocess import call

        testdir = os.path.join(HERE, 'floof', 'tests')
        cmd = ['py.test', testdir]
        if self.config:
            cmd.append('--config={0}'.format(self.config))

        try:
            ret_val = call(cmd, cwd=HERE)
        except OSError as exc:
            from traceback import print_exc
            from errno import ENOENT

            print_exc(exc)
            errno, strerror = exc
            if errno == ENOENT:
                print "Probably could not find py.test in path; have you run " \
                      "'python setup.py <develop|install>' ?"
            else:
                print ("Unexpected error calling py.test: errno {0}: {1}"
                       .format(errno, strerror))

            ret_val = errno or 1

        raise SystemExit(ret_val)


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
        'python-magic>=0.4.1',
        'PIL',
        'sqlalchemy-migrate>=0.6',
        'pytz',
        'iso8601',
        'pyOpenSSL>=0.11',
        'pyramid>=1.2',
        'pyramid_beaker',
        'repoze.tm2>=1.0b1',  # default_commit_veto
        'WebError',
        'WebTest',
        'zope.sqlalchemy',
        'pytest',
        'lxml>=2.3.1',  # strip data: urls
        'markdown',
    ],
    setup_requires=["PasteScript>=1.6.3"],
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    cmdclass={'test': PyTest},
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
