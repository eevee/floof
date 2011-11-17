try:
    from setuptools import setup, find_packages, Command
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

def which(program):
    """Emulates UNIX which, sort of.

    Ripped straight from StackOverflow #377017

    """
    import os
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

class PyTest(Command):
    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        import os.path, sys, subprocess
        if which('py.test') is None:
            raise EnvironmentError("Unable to find executable 'py.test'; have "
                                   "you run python setup.py <develop|install> ?")
        path = os.path.abspath(os.path.dirname(__file__))
        errno = subprocess.call(['py.test', 'floof/tests'] + sys.argv[2:],
                                cwd=path)
        raise SystemExit(errno)

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
        'pyramid>=1.2',
        'pyramid_beaker',
        'repoze.tm2>=1.0b1',  # default_commit_veto
        'WebError',
        'zope.sqlalchemy',
        'pytest',
        'lxml>=2.3.1',  # strip data: urls
        'python-markdown',
    ],
    setup_requires=["PasteScript>=1.6.3"],
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    cmdclass = {'test': PyTest},
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
