<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="title()">${self.panel_title()} - Admin panel</%def>

<section>
<h1>${self.panel_icon()} Admin panel » ${self.panel_title()}</h1>

<nav class="side-navigation">
<ul>
    % for action, icon, title in [ \
        ('dashboard',           'question',         u'Dashboard'), \
        ('oauth.clients',       'oauth-tiny',       u'OAuth Clients'), \
        ('oauth.authorizations','oauth-tiny',       u'OAuth Authorizations'), \
        ('log',                 'book-bookmark',    u'Log'), \
    ]:
    <% route_tail = request.matched_route.name.split('.', 1)[1] %>
    % if route_tail == action or route_tail.startswith(action + '.'):
    <li class="selected">${lib.icon(icon)} ${title}</li>
    % else:
    <li><a href="${request.route_url('admin.' + action)}">${lib.icon(icon)} ${title}</a></li>
    % endif
    % endfor
</ul>
</nav>

<section>
${next.body()}
</section>
</section>
