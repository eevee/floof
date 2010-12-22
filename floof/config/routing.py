"""Routes configuration

The more specific and detailed routes should be defined first so they
may take precedent over the more generic routes. For more information
refer to the routes manual at http://routes.groovie.org/docs/
"""
from routes import Mapper
from pylons import config

def user_filter(kw):
    if 'user' in kw:
        kw['name'] = kw.pop('user').name
    return kw

def filestore_filter(kw):
    kw['url'] = config['filestore'].url(kw.pop('key'))
    return kw

def make_map(config):
    """Create, configure and return the routes Mapper"""
    map = Mapper(directory=config['pylons.paths']['controllers'],
                 always_scan=config['debug'])
    map.minimization = False

    require_GET = dict(conditions=dict(method=['GET']))
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

    map.connect('/account/controls', controller='controls', action='index')
    map.connect('/account/controls/{action}', controller='controls', action='index',
        requirements=dict(action='relationships'))

    map.connect('user', '/users/{name}', controller='users', action='view', _filter=user_filter)
    map.connect('/users/{name}/{action}', controller='users')

    map.connect('/', controller='main', action='index')

    map.connect('/art', controller='art', action='gallery')
    map.connect('/art/upload', controller='art', action='upload')

    map.connect(r'/art/{id:\d+};{title}', controller='art', action='view')
    map.connect(r'/art/{id:\d+}', controller='art', action='view')
    map.connect(r'/art/{id:\d+}/add_tags', controller='art', action='add_tags', **require_POST)
    map.connect(r'/art/{id:\d+}/remove_tags', controller='art', action='remove_tags', **require_POST)

    map.connect('/tags', controller='tags', action='index')
    map.connect('/tags/{name}', controller='tags', action='view')
    map.connect('/tags/{name}/artwork', controller='tags', action='artwork')

    # Comments, which can be attached to various things
    comment_submappings = [
        # Art
        dict(controller='comments', subcontroller='art',
            path_prefix=r'/{subcontroller}/{id:\d+};{title}'),
        dict(controller='comments', subcontroller='art',
            path_prefix=r'/{subcontroller}/{id:\d+}'),
    ]
    for submapping in comment_submappings:
        with map.submapper(**submapping) as m:
            m.connect('/comments', action='view')
            m.connect('/comments/{comment_id:\d+}', action='view')
            m.connect('/comments/write', action='write', **require_GET)
            m.connect('/comments/write', action='write_commit', **require_POST)
            m.connect(r'/comments/{comment_id:\d+}/write', action='write', **require_GET)
            m.connect(r'/comments/{comment_id:\d+}/write', action='write_commit', **require_POST)

    # Static routes
    map.connect('icon', '/icons/{which}.png', _static=True)
    map.connect('css', '/css/{which}.css', _static=True)
    map.connect('filestore', '{url}', _static=True, _filter=filestore_filter)

    return map
