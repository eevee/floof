"""Helper classes for implementing common workflows."""

import wtforms

from pyramid.renderers import render_to_response
from pyramid.httpexceptions import HTTPSeeOther

from floof import model


class FormWorkflow(object):
    form_class = None

    # TODO: Some ideas for expanding on our ajax powers:
    # - Let ajax requests get something more useful than errors or redirects
    # back, for e.g. partial page updates.  Perhaps ratings are a good
    # candidate here.  Consider later things like uploading directly to a
    # gallery page and having it reflow automatically.
    # - Make ORM objects understand how to JSON-serialize themselves, for use
    # as return values.  Possibly this belongs in the app layer where we can
    # add URLs as well.

    def __init__(self, request):
        self.request = request
        self.form = self.make_form()

    def make_form(self):
        return self.form_class(self.request.POST)

    def show_form(self):
        return dict(form=self.form)

    def _new_json_response(self):
        ret = {
            'status': 'unknown',
            'flash': [],
        }

        flash_queue = self.request.session.pop_flash()
        for flash in flash_queue:
            ret['flash'].append({
                'icon': flash['icon'],
                'message': flash['message'],
                # XXX we shouldn't need this at all; should always go through markupsafe
                'html': not flash['html_escape'],
            })

        return ret

    def respond_json(self, data):
        return render_to_response('json', data, self.request)

    def respond_form_error(self):
        if self.request.is_xhr:
            ret = self._new_json_response()
            ret['status'] = 'invalid-form'
            ret['form-errors'] = self.form.errors
            return self.respond_json(ret)
        else:
            return self.show_form()

    def respond_general_error(self):
        if self.request.is_xhr:
            ret = self._new_json_response()
            ret['status'] = 'failure'
            return self.respond_json(ret)
        else:
            return self.show_form()

    def respond_redirect(self, url):
        if self.request.is_xhr:
            # NOTE: do NOT use _new_json_response here; it eats the flash!
            ret = {}
            ret['status'] = 'redirect'
            ret['redirect-to'] = url
            return self.respond_json(ret)
        else:
            return HTTPSeeOther(location=url)


class CRUDWorkflow(FormWorkflow):
    """Workflows for manipulating (single) ORM objects.

    GETs just display the form defined as :attr:`form_class`.

    POSTs perform the creation, updation, deletion, etc and then redirect (303)
    the user to the :attr:`redirect_location` or :attr:`redirect_route`.

    """
    # TODO: Make this work meaningfully with FormWorkflow AJAXisms
    # TODO: Properly abstract the business logic for easy integration into both
    # web view and a future (imminent?) API.

    # CHANGEME: Where to redirect after success.  redirect_location may be a
    # string that will be passed directly as the Location HTTP header or a
    # callable accepting the workflow object and returning such a string;
    # alternatively, redirect_route may be used as a shortcut to specify a
    # plain route name to be passed to request.route_url
    redirect_location = None
    redirect_route = 'root'

    # CHANGEME: Name to use to reference the ORM obj in the "successfully
    # created" flash message; may be a callable that accepts the workflow obj
    # Omit to suppress the flash message
    flash_name = None

    def _get_redirect(self):
        if self.redirect_location is not None:
            if hasattr(self.redirect_location, '__call__'):
                location = self.redirect_location()
            else:
                location = self.redirect_location
        else:
            location = self.request.route_url(self.redirect_route)

        return HTTPSeeOther(location=location)

    def handle_get(self):
        return self.show_form()

    def add_flash(self, obj, msg, **kwargs):
        callable_ = hasattr(self.flash_name, '__call__')
        name = self.flash_name(obj) if callable_ else self.flash_name

        if name:
            msg = msg.format(name=name)
            self.request.session.flash(msg, **kwargs)


class CreateWorkflow(CRUDWorkflow):
    """Workflow for creating a single ORM object."""

    # CHANGEME: ORM class of which an instance shall be created
    orm_cls = None

    def extra_attrs(self):
        return dict()

    def handle_post(self):
        if not self.form.validate():
            return self.respond_form_error()

        # Prepare to populate a new object with appropriate form fields
        orm_attrs = {}
        for field in self.form:
            if hasattr(self.orm_cls, field.short_name):
                orm_attrs[field.short_name] = field.data

        orm_attrs.update(self.extra_attrs())

        self.newobj = self.orm_cls(**orm_attrs)
        model.session.add(self.newobj)
        model.session.flush()  # Ensure the new obj exists before rdr

        self.add_flash(
            self.newobj, u'{name} successfully created.', level=u'success',
            icon='plus')

        return self._get_redirect()


class UpdateWorkflow(CRUDWorkflow):
    """Workflow for editing a single ORM object.

    The ORM object must be supplied as the request's context.

    """
    # CHANGEME: Name under which to make the ORM obj available in the template
    context_name = 'changeme'

    def make_form(self):
        return self.form_class(self.request.POST, obj=self.request.context)

    def show_form(self):
        return {'form': self.form, self.context_name: self.request.context}

    def tweak_form(self):
        pass

    def handle_post(self):
        if not self.form.validate():
            return self.respond_form_error()

        self.tweak_form()

        self.form.populate_obj(self.request.context)

        self.add_flash(
            self.request.context, u'{name} successfully updated.',
            level=u'success', icon='pencil')

        return self._get_redirect()


class DeleteWorkflow(CRUDWorkflow):
    """Workflow for editing a single ORM object.

    The ORM object must be supplied as the request's context.

    """
    # CHANGEME: Name under which to make the ORM obj available in the template
    context_name = 'changeme'

    class form_class(wtforms.form.Form):
        delete = wtforms.fields.SubmitField(u'Delete')

    def show_form(self):
        return {'form': self.form, self.context_name: self.request.context}

    def handle_post(self):
        if not self.form.validate():
            return self.respond_form_error()

        model.session.delete(self.request.context)
        model.session.flush()

        self.add_flash(
            self.request.context, u'{name} successfully deleted.',
            level=u'success', icon='minus')

        return self._get_redirect()
