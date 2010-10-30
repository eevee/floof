<%! import wtforms.widgets %>

<%def name="icon(which, alt='')">
<img src="${url('icon', which=which)}" alt="${alt}">
</%def>

<%def name="time(t)">
${c.user.localtime(t).strftime('%A, %d %B %Y at %H:%M %Z')}
</%def>

<%def name="field(form_field, **kwargs)">
% if isinstance(form_field.widget, wtforms.widgets.CheckboxInput):
<dd>
    ${form_field(**kwargs) | n} ${form_field.label() | n}
    ${field_errors(form_field)}
</dd>
% else:
<dt>${form_field.label() | n}</dt>
<dd>
    ${form_field(**kwargs) | n}
    ${field_errors(form_field)}
</dd>
% endif
</%def>

<%def name="field_errors(form_field)">
% for error in form_field.errors:
<p class="form-error">${error | n}</p>
% endfor
</%def>
