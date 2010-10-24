"""Routes configuration

The more specific and detailed routes should be defined first so they
may take precedent over the more generic routes. For more information
refer to the routes manual at http://routes.groovie.org/docs/
"""
from routes import Mapper

def make_map(config):
    """Create, configure and return the routes Mapper"""
    map = Mapper(directory=config['pylons.paths']['controllers'],
                 always_scan=config['debug'])
    map.minimization = False

    require_POST = dict(conditions=dict(method=['POST']))

    # The ErrorController route (handles 404/500 error pages); it should
    # likely stay at the top, ensuring it can always be resolved
    map.connect('/error/{action}', controller='error')
    map.connect('/error/{action}/{id}', controller='error')

    map.connect('/account/login', controller='account', action='login')
    map.connect('/account/login_begin', controller='account', action='login_begin',
        **require_POST)
    map.connect('/account/login_finish', controller='account', action='login_finish')
    map.connect('/account/register', controller='account', action='register',
        **require_POST)
    map.connect('/account/logout', controller='account', action='logout',
        **require_POST)

    map.connect('/art', controller='art', action='gallery')
    map.connect('/art/{id:\d+};{title}', controller='art', action='view')
    map.connect('/art/{id:\d+}', controller='art', action='view')
    map.connect('/art/upload', controller='art', action='upload')

    map.connect('/', controller='main', action='index')

    return map
