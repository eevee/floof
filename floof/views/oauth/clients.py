import logging

from urlparse import urlparse

import wtforms

from pyramid.view import view_config, view_defaults

from floof import model
from floof.forms import FloofForm, ManyToOneTextField
from floof.forms import NewlineDelimitedListField
from floof.lib.pager import DiscretePager
from floof.views._workflow import CreateWorkflow, DeleteWorkflow
from floof.views._workflow import UpdateWorkflow

log = logging.getLogger(__name__)


# XXX: Should these fall under trusted_for:auth protection?


@view_config(
    route_name='controls.oauth',
    permission='__authenticated__',
    request_method='GET',
    renderer='account/controls/oauth/index.mako')
def user_oauth_list(context, request):
    """All-in-one summary for single users."""
    return dict()


@view_config(
    route_name='admin.oauth.clients',
    permission='admin.oauth',
    request_method='GET',
    renderer='admin/oauth/clients.mako')
def oauth_clients_list(context, request):
    """All-clients list; currently just for admins."""
    q = model.session.query(model.OAuth2Client)
    # For as long as this is admin-only, a countable DiscretePager should be OK
    pager = DiscretePager(
        query=q,
        page_size=100,
        formdata=request.GET,
        countable=True,
    )
    return dict(clients=pager)


def validate_redirect_uris(form, field):
    uris = field.data

    if hasattr(form.request.context, 'type'):
        client_type = form.request.context.type
    else:
        client_type = form.type.data

    if client_type == u'native':
        if uris:
            raise wtforms.validators.ValidationError(
                'Native/Mobile clients cannot specify redirection URIs')
        return

    if not uris:
        raise wtforms.validators.ValidationError(
            'Must include at least one URI')

    for uri in uris:
        # XXX: does this have any input for which it will raise an exc?
        u = urlparse(uri)
        if not u.scheme or not u.netloc:
            raise wtforms.validators.ValidationError(
                'All redirection URIs must be absolute and include at '
                'least a scheme (must be HTTPS) and authority')
        if u.scheme != 'https':
            raise wtforms.validators.ValidationError(
                'For now, all redirection URIs must be HTTPS URLs')
        if u.fragment:
            raise wtforms.validators.ValidationError(
                'Redirection URIs must not contain fragments')


def validate_site_uri(form, field):
    uri = field.data
    if not uri:
        return

    u = urlparse(uri)
    if not u.scheme or not u.netloc:
        raise wtforms.validators.ValidationError(
            'The site URIs must be absolute and include at least a scheme '
            '(must be HTTP or HTTPS) and authority')
    if u.scheme != 'https':
        raise wtforms.validators.ValidationError(
            'For now, all site URIs must be HTTP or HTTPS URLs')


class OAuthClientBaseForm(FloofForm):
    name = wtforms.fields.TextField(
        u'Friendly Name', [
            wtforms.validators.Required(),
            wtforms.validators.Length(max=127),
        ])
    site_uri = wtforms.fields.TextField(u'Website URL')
    redirect_uris = NewlineDelimitedListField(u'Redirection URIs')

    validate_site_uri = validate_site_uri
    validate_redirect_uris = validate_redirect_uris


get_oauth_client_name = lambda workflow, obj: "Client '{0}'".format(obj.name)


@view_defaults(
    route_name='controls.oauth.clients.add',
    permission='oauth.clients.add',
    renderer='account/controls/oauth/clients_add.mako')
@view_config(attr='handle_get', request_method='GET', xhr=False)
@view_config(attr='handle_post', request_method='POST')
class OAuthClientCreatePage(CreateWorkflow):
    """Edits an OAuth2 client object."""

    orm_cls = model.OAuth2Client
    redirect_location = lambda self: self.request.route_url(
        'controls.oauth.clients.edit', client=self.newobj)
    flash_name = get_oauth_client_name

    class form_class(OAuthClientBaseForm):
        type = wtforms.fields.SelectField(u'Application Type', choices=[
            ('web', 'Web Server'),
            ('native', 'Native or Mobile')
        ])

    def make_form(self):
        return self.form_class(self.request, self.request.POST)

    def extra_attrs(self):
        return dict(user=self.request.user)


@view_defaults(
    route_name='admin.oauth.clients.add',
    permission='admin.oauth',
    renderer='admin/oauth/clients_add.mako')
@view_config(attr='handle_get', request_method='GET', xhr=False)
@view_config(attr='handle_post', request_method='POST')
class AdminOAuthClientCreatePage(OAuthClientCreatePage):
    redirect_location = lambda self: self.request.route_url(
        'admin.oauth.clients.edit', client=self.newobj)

    class form_class(OAuthClientCreatePage.form_class):
        user = ManyToOneTextField(u'Owning User', sqla_column=model.User.name)


@view_defaults(
    route_name='controls.oauth.clients.edit',
    permission='oauth.client.control',
    renderer='account/controls/oauth/clients_edit.mako')
@view_config(attr='handle_get', request_method='GET', xhr=False)
@view_config(attr='handle_post', request_method='POST')
class OAuthClientEditPage(UpdateWorkflow):
    """Edits an OAuth2 client object."""

    context_name = 'client'
    redirect_route = 'controls.oauth'
    flash_name = get_oauth_client_name

    form_class = OAuthClientBaseForm

    def make_form(self):
        return self.form_class(
            self.request, self.request.POST, obj=self.request.context)


@view_defaults(
    route_name='admin.oauth.clients.edit',
    permission='admin.oauth',
    renderer='admin/oauth/clients_edit.mako')
@view_config(attr='handle_get', request_method='GET', xhr=False)
@view_config(attr='handle_post', request_method='POST')
class AdminOAuthClientEditPage(OAuthClientEditPage):
    redirect_route = 'admin.oauth.clients'

    class form_class(OAuthClientEditPage.form_class):
        user = ManyToOneTextField(u'Owning User', sqla_column=model.User.name)


@view_defaults(
    route_name='controls.oauth.clients.delete',
    permission='oauth.client.control',
    renderer='account/controls/oauth/clients_delete.mako')
@view_config(attr='handle_get', request_method='GET', xhr=False)
@view_config(attr='handle_post', request_method='POST')
class OAuthClientRemovePage(DeleteWorkflow):
    """Edits an OAuth2 client object."""

    context_name = 'client'
    redirect_route = 'controls.oauth'
    flash_name = get_oauth_client_name


@view_defaults(
    route_name='admin.oauth.clients.delete',
    permission='admin.oauth',
    renderer='admin/oauth/clients_delete.mako')
@view_config(attr='handle_get', request_method='GET', xhr=False)
@view_config(attr='handle_post', request_method='POST')
class AdminOAuthClientRemovePage(OAuthClientRemovePage):
    redirect_route = 'admin.oauth.clients'
