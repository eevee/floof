"""Routes configuration

The more specific and detailed routes should be defined first so they
may take precedent over the more generic routes. For more information
refer to the routes manual at http://routes.groovie.org/docs/
"""
from routes import Mapper
from pylons import config

def filestore_filter(kw):
    kw['url'] = config['filestore'].url(kw.pop('key'))
    return kw

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

    map.connect('/account/{action}', controller='account',
        requirements=dict(action='login|login_finish|profile'))
    map.connect('/account/{action}', controller='account',
        requirements=dict(action='login_begin|register|logout|profile'),
        **require_POST)

    map.connect('/art', controller='art', action='gallery')
    map.connect('/art/{id:\d+};{title}', controller='art', action='view')
    map.connect('/art/{id:\d+}', controller='art', action='view')
    map.connect('/art/upload', controller='art', action='upload')

    map.connect('/user/{name}', controller='user', action='view')
    map.connect('/user/{name}/{action}', controller='user')

    map.connect('/', controller='main', action='index')

    # Static routes
    map.connect('icon', '/icons/{which}.png', _static=True)
    map.connect('css', '/css/{which}.css', _static=True)
    map.connect('filestore', '{url}', _static=True, _filter=filestore_filter)

    return map
