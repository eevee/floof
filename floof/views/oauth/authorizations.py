import logging

from pyramid.view import view_config, view_defaults

from floof import model
from floof.lib.pager import DiscretePager
from floof.views._workflow import DeleteWorkflow

log = logging.getLogger(__name__)


@view_config(
    route_name='admin.oauth.authorizations',
    permission='admin.oauth',
    request_method='GET',
    renderer='admin/oauth/authorizations.mako')
def oauth_authorizations_list(context, request):
    """All-authorizations list; currently just for admins."""
    q = model.session.query(model.OAuth2RefreshToken)
    # For as long as this is admin-only, a countable DiscretePager should be OK
    pager = DiscretePager(
        query=q,
        page_size=100,
        formdata=request.GET,
        countable=True,
    )
    return dict(authorizations=pager)


@view_defaults(
    route_name='controls.oauth.authorizations.revoke',
    permission='oauth.authorization.revoke',
    renderer='account/controls/oauth/authorizations_delete.mako')
@view_config(attr='handle_get', request_method='GET', xhr=False)
@view_config(attr='handle_post', request_method='POST')
class OAuthAuthzRemovePage(DeleteWorkflow):
    """Edits an OAuth2 client object."""

    context_name = 'authz'
    redirect_route = 'controls.oauth'

    def flash_name(workflow, authz_obj):
        return "Authorization for '{0}'".format(authz_obj.client.name)


@view_defaults(
    route_name='admin.oauth.authorizations.revoke',
    permission='admin.oauth',
    renderer='admin/oauth/authorizations_delete.mako')
@view_config(attr='handle_get', request_method='GET', xhr=False)
@view_config(attr='handle_post', request_method='POST')
class AdminOAuthAuthzRemovePage(OAuthAuthzRemovePage):
    redirect_route = 'admin.oauth.authorizations'
