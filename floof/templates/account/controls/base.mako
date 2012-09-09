<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="title()">${self.panel_title()} - Control panel</%def>

<section>
    <h1>${self.panel_icon()} Control panel » ${self.panel_title()}</h1>

    <div class="columns">
    <div class="col2">
        <nav class="side-navigation col2">
        <ul>
            % for action, icon, title in [ \
                ('index',    'fruit',        u'Index??'), \
                ('info',     'user--pencil', u'User Info'), \
                ('rels',     'users',        u'Watches'), \
                ('browserid','user',         u'Persona Identities'), \
                ('openid',   'openid',       u'OpenID Identities'), \
                ('certs',    'certificate',  u'SSL Certificates'), \
                ('auth',     'key',          u'Authentication Options'), \
            ]:
            % if action == request.matched_route.name.split('.')[1]:
            <li class="selected">${lib.icon(icon)} ${title}</li>
            % else:
            <li><a href="${request.route_url('controls.' + action)}">${lib.icon(icon)} ${title}</a></li>
            % endif
            % endfor
        </ul>
        </nav>
    </div>

    <div class="col10">
        ${next.body()}
    </div>
    </div>
</section>
