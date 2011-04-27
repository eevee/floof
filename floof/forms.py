from datetime import datetime
from wtforms import fields, widgets
from wtforms.widgets import HTMLString, html_params
import pytz
import random
import re

class KeygenWidget(widgets.Input):
    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        return HTMLString(u'<keygen {0} />'.format(html_params(
                name=field.name,
                challenge=field.challenge,
                keytype=field.keytype,
                **kwargs
                )))

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
        return HTMLString(u''.join(html))

class KeygenField(fields.TextField):
    widget = KeygenWidget()

    def __init__(self, label='', validators=None, keytype='rsa', **kwargs):
        super(KeygenField, self).__init__(label, validators, **kwargs)
        self.keytype = keytype
        # For SPKAC certificate generation.  AFAIK it does not need to be
        # a cryptographically strong radom string, just unique.
        self.challenge = random.getrandbits(128)

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

def timezone_choices():
    """Helper that generates a list of timezones sorted by ascending UTC
    offset.

    The timezones are represented as tuple pairs of timezone name and a
    string representation of the current UTC offset.
    """
    #TODO: Perfect for caching; the list is unlikely to change more than hourly.
    tzs = []
    now = datetime.now()
    for tz_name in pytz.common_timezones:
        offset = pytz.timezone(tz_name).utcoffset(now)
        offset_real_secs = offset.seconds + offset.days * 24 * 60**2
        offset_hours, remainder = divmod(offset_real_secs, 3600)
        offset_minutes, _ = divmod(remainder, 60)
        offset_txt = '(UTC {0:0=+3d}:{1:0>2d}) {2}'.format(
                offset_hours, offset_minutes, tz_name)
        tzs.append((offset_real_secs, tz_name, offset_txt))
    tzs.sort()
    return [tz[1:] for tz in tzs]

def coerce_timezone(value):
    if value is None:
        return None
    if isinstance(value, (pytz.tzfile.DstTzInfo, pytz.tzfile.StaticTzInfo)):
        return value
    else:
        try:
            return pytz.timezone(value)
        except (ValueError, pytz.UnknownTimeZoneError):
            # ValueError is recognised by SelectField.process_formdata()
            raise ValueError(u'Not a timezone')

class TimezoneField(fields.SelectField):
    """A simple select field that handles pytz to Olson TZ name conversions.
    """
    def __init__(self, label=None, validators=None, **kwargs):
        super(TimezoneField, self).__init__(label, validators,
                coerce=coerce_timezone, choices=timezone_choices(), **kwargs)

    def pre_validate(self, form):
        for v, _ in self.choices:
            if self.data.zone == v:
                break
        else:
            raise ValueError(self.gettext(u'Not a valid choice'))
