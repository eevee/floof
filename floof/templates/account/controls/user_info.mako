<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">User Info</%def>
<%def name="panel_icon()">${lib.icon('user')}</%def>

<%
fields = [
        'display_name',
        'email',
        'timezone',
        ]
%>

<section>
    <%lib:secure_form>
    <fieldset>
        <dl>
            % for f in fields:
                <% field = form[f] %>\
                <% maxlen = getattr(form, '_{0}_maxlen'.format(f), None) %>\
                % if maxlen:
                    ${lib.field(field, size=maxlen, maxlength=maxlen)}
                % else:
                    ${lib.field(field)}
                % endif
            % endfor
        </dl>
        <footer>
            <button>Update</button>
        </footer>
    </fieldset>
    </%lib:secure_form>
</section>
