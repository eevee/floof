"""Helper classes for implementing common workflows."""
from pyramid.renderers import render_to_response
from pyramid.httpexceptions import HTTPSeeOther


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
        

