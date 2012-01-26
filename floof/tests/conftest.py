def pytest_addoption(parser):
    # config allows importing settings, such as MogileFS tracker URLs;
    # some tests may be skipped in the absence of this option
    parser.addoption('--config', action='store', default='',
        help='floof config file & app: e.g paster.ini#floof-test or '
        'config.ini#myapp, etc.')
