import os

from setuptools import setup, find_packages, Command

HERE = os.path.abspath(os.path.dirname(__file__))


class PyTest(Command):
    user_options = [('config=', 'c', 'floof paster configuration ini-spec')]

    def initialize_options(self):
        self.config = ''

    def finalize_options(self):
        if self.config:
            self.config = os.path.abspath(self.config)

    def run(self):
        from subprocess import call

        testdir = os.path.join(HERE, 'floof', 'tests')
        unit = os.path.join(testdir, 'unit')
        functional = os.path.join(testdir, 'functional')
        cmd = ['py.test', unit, functional]
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


README = open(os.path.join(HERE, 'README')).read()

requires = [
    'pyramid>=1.3',
    'pyramid_beaker',
    'pyramid_debugtoolbar',
    'SQLAlchemy>=0.7',
    'sqlalchemy-migrate>=0.6',
    'zope.sqlalchemy',
    'wtforms',
    'WebHelpers>=1.0',
    'python-magic>=0.4.1',
    'PIL',
    'pytz',
    'iso8601',
    'python-openid',
    'PyBrowserID>=0.8.0',
    'pyOpenSSL>=0.11',
    'oauthlib>=0.3',
    'repoze.tm2>=1.0b1',  # default_commit_veto
    'lxml>=2.3.1',  # strip data: urls
    'markdown',
    'pytest',
    'WebTest',
],


setup(
    name='floof',
    version='0.1',
    description='',
    long_description=README,
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    author='',
    author_email='',
    url='',
    keywords='web pyramid pylons',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    tests_require=requires,
    cmdclass={'test': PyTest},
    entry_points="""\
    [paste.app_factory]
    main = floof.app:main
    api = floof.api:main
    """,
)
