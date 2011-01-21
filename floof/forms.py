from wtforms import fields, widgets
import re

class PassthroughListWidget(widgets.ListWidget):
    """Just like a ListWidget, but passes rendering kwargs to its children."""
    def __call__(self, field, **kwargs):
        html = [u'<%s>' % (self.html_tag)]
        for subfield in field:
            if self.prefix_label:
                html.append(u'<li>%s: %s</li>' % (subfield.label, subfield(**kwargs)))
            else:
                html.append(u'<li>%s %s</li>' % (subfield(**kwargs), subfield.label))
        html.append(u'</%s>' % self.html_tag)
        return widgets.HTMLString(u''.join(html))

# borrowed from spline
class MultiCheckboxField(fields.SelectMultipleField):
    """ A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """
    widget = PassthroughListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class MultiTagField(fields.TextField):

    def _value(self):
        if self.raw_data:
            return self.raw_data[0]
        elif self.data:
            return u' '.join(sorted(self.data))
        return u''

    _tag_re = re.compile(r'^[a-z0-9\s]*$')
    def process_formdata(self, valuelist):
        if not valuelist:
            self.data = []
            return

        value = valuelist[0]
        if not self._tag_re.match(value):
            raise ValueError("Tags must be lowercase and alphanumeric")

        if value:
            self.data = [x for x in value.strip().split()]
