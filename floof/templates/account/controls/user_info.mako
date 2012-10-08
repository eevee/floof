<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">User Info</%def>
<%def name="panel_icon()">${lib.icon('user')}</%def>

<%
fields = [
    ('display_name', None),
    ('email', None),
    ('timezone', None),
    ('show_art_scores', 'View the computed rating score of your own artwork'),
]
%>

<section>
    <%lib:secure_form>
    <fieldset>
        <dl>
            % for f, hint in fields:
                <%
                    field = form[f]
                    kw = {}
                    maxlen = getattr(form, '_{0}_maxlen'.format(f), None)
                    if maxlen:
                        kw['size'] = maxlen
                        kw['maxlength'] = maxlen
                    if hint:
                        kw['hint_text'] = hint
                %>\
                ${lib.field(field, **kw)}
            % endfor
        </dl>
        <footer>
            <button>Update</button>
        </footer>
    </fieldset>
    </%lib:secure_form>
</section>
