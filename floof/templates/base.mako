<!DOCTYPE html>
<%namespace name="lib" file="/lib.mako" />
<html>
<head>
    <title>${self.title()} - ${config['site_title']}</title>
    <meta charset="utf-8" />
    <link rel="stylesheet" type="text/css" href="${request.static_url('floof:public/css/all.css')}">
    ${h.javascript_link(url('/js/lib/jquery-1.4.4.min.js'))}
    ${h.javascript_link(url('/js/lib/jquery.cookie.js'))}
    % if config.get('super_debug', False):
        ${h.javascript_link(url('/js/debugging.js'))}
    % endif

## Allow templates to define their script dependencies to include in head
    % if hasattr(self, "script_dependencies") and hasattr(self.script_dependencies, "__call__"):
        ${self.script_dependencies()}
    %endif
</head>
<body>
    <div id="header">
        <div id="logo"><a href="${request.route_url('root')}">floof</a></div>
        <div id="user">
            % if user:
            ${h.secure_form(request.route_url('account.logout'), class_='compact')}
            <p>Hello, ${lib.user_link(user)}!</p>
                % if auth.can_purge:
                <p><input type="submit" value="Log out" /></p>
                % else:
                <p>To log out, you'll need to instruct your browser to stop
                sending your SSL certificate.</p>
                % endif
            ${h.end_form()}
            % elif auth.pending_user:
            <p><a href="${request.route_url('account.login')}">Complete log in for ${auth.pending_user.name}</a></p>
            ${h.secure_form(request.route_url('account.logout'), class_='compact')}
                % if auth.can_purge:
                <p><input type="submit" value="Purge Authentication" /></p>
                % else:
                <p>To log in as someone else, you'll need to instruct
                your browser to stop sending your SSL certificate.</p>
                % endif
            ${h.end_form()}
            % else:
            <a href="${request.route_url('account.login')}">Log in or register</a>
            % endif
        </div>
        <ul id="navigation">
            <li><a href="${url(controller='art', action='gallery')}">Art</a></li>
            <li><a href="${url(controller='art', action='upload')}">Upload</a></li>
            <li><a href="${url(controller='tags', action='index')}">Tags</a></li>
            % if user:
                <li><a href="${url(controller='controls', action='index')}">Controls</a></li>
            % endif
            % if user.can('admin.view'):
                <li><a href="${url(controller='admin', action='dashboard')}">Admin</a></li>
            % endif
        </ul>
    </div>

    <% flash = request.session.pop_flash() %>
    % if flash:
    ## XXX yeah this won't actually work yet.
    <ul id="flash">
        % for messages in flash:
        <li class="flash-level-${'' and messages.message[1]['level']}">
            ##${lib.icon(messages.message[1]['icon'])}
            ${messages}
        </li>
        % endfor
    </ul>
    % endif

    <div id="content">
        ${next.body()}
    </div>

    <div id="footer-spacer"></div>
    <div id="footer">
        <%doc>
        <p id="footer-stats">
            built in ${lib.timedelta(timer.total_time)} <br>
            ${timer.sql_queries} quer${ 'y' if timer.sql_queries == 1 else 'ies' }
                in ${lib.timedelta(timer.sql_time)}
        </p>
        </%doc>
        <p>Icons from the <a href="http://p.yusukekamiyamane.com/">Fugue set</a></p>
        <p><a href="${url(controller='main', action='log')}">Admin log</a></p>
    </div>

    % if config.get('super_debug', False):
    <%include file="/debugging.mako" />
    % endif
</body>
</html>

<%def name="title()">Untitled</%def>
