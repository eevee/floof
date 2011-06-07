from pyramid.view import view_config

@view_config(route_name='root',
    renderer='index.mako')
def dummy_index(context, request):
    return {}
