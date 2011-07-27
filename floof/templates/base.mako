<!DOCTYPE html>
<%namespace name="lib" file="/lib.mako" />
<html>
<head>
    <title>${self.title()} - ${request.registry.settings['site_title']}</title>
    <meta charset="utf-8" />
    <link rel="stylesheet" type="text/css" href="${request.static_url('floof:public/css/all.css')}">
    ${h.javascript_link(request.static_url('floof:public/js/lib/jquery-1.4.4.min.js'))}
    ${h.javascript_link(request.static_url('floof:public/js/lib/jquery.cookie.js'))}
    % if request.registry.settings['super_debug']:
        ${h.javascript_link(request.static_url('floof:public/js/debugging.js'))}
    % endif

    ## Allow templates to define their script dependencies to include in head
    ${self.script_dependencies()}
</head>
<body>
    <div id="header">
        <div id="logo"><a href="${request.route_url('root')}">floof</a></div>
        <div id="user">
            % if request.user:
            ${lib.secure_form(request.route_url('account.logout'), class_='compact')}
            <p>Hello, ${lib.user_link(request.user)}!</p>
                % if request.auth.can_purge:
                <p><input type="submit" value="Log out" /></p>
                % else:
                <p>To log out, you'll need to instruct your browser to stop
                sending your SSL certificate.</p>
                % endif
            ${h.end_form()}
            % elif request.auth.pending_user:
            <p><a href="${request.route_url('account.login')}">Complete log in for ${request.auth.pending_user.name}</a></p>
            ${lib.secure_form(request.route_url('account.logout'), class_='compact')}
                % if request.auth.can_purge:
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
            <li><a href="${request.route_url('art.browse')}">Art</a></li>
            <li><a href="${request.route_url('art.upload')}">Upload</a></li>
            <li><a href="${request.route_url('tags.list')}">Tags</a></li>
            % if request.user:
                <li><a href="${request.route_url('controls.index')}">Controls</a></li>
            % endif
            % if request.user.can('admin.view'):
                <li><a href="${request.route_url('admin.dashboard')}">Admin</a></li>
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
        ## TODO: make this only show for devs.  nobody else cares.
        ## TODO: of course, if you do that, do more logging!
        <p id="footer-stats">
            built in ${lib.timedelta(request.timer.total_time)} <br>
            ${request.timer.sql_query_count} quer${ 'y' if request.timer.sql_query_count == 1 else 'ies' }
                in ${lib.timedelta(request.timer.timers['sql'])}
        </p>
        <p>Icons from the <a href="http://p.yusukekamiyamane.com/">Fugue set</a></p>
        <p><a href="${request.route_url('log')}">Admin log</a></p>
    </div>

    % if request.registry.settings['super_debug']:
    <%include file="/debugging.mako" />
    % endif
</body>
</html>

<%def name="title()">Untitled</%def>
<%def name="script_dependencies()"></%def>
