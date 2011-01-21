<!DOCTYPE html>
<%namespace name="lib" file="/lib.mako" />
<html>
<head>
    <title>${self.title()} - ${config['site_title']}</title>
    <link rel="stylesheet" type="text/css" href="${url('css', which='all')}">
    <script type="text/javascript" src="${url('/js/lib/jquery-1.4.4.min.js')}"></script>
    <script type="text/javascript" src="${url('/js/lib/jquery.cookie.js')}"></script>
    % if config.get('super_debug', False):
    <script type="text/javascript" src="${url('/js/debugging.js')}"></script>
    % endif
</head>
<body>
    <div id="header">
        <div id="logo"><a href="${url('/')}">floof</a></div>
        <div id="user">
            % if c.user:
                ${h.secure_form(url(controller='account', action='logout'), class_='compact')}
                <p>Hello, ${lib.user_link(c.user)}!</p>
                <p><button type="submit">Log out</button></p>
                ${h.end_form()}
            % else:
            <a href="${url(controller='account', action='login')}">Log in or register</a>
            % endif
        </div>
        <ul id="navigation">
            <li><a href="${url(controller='art', action='gallery')}">Art</a></li>
            <li><a href="${url(controller='art', action='upload')}">Upload</a></li>
            <li><a href="${url(controller='tags', action='index')}">Tags</a></li>
            % if c.user:
                <li><a href="${url(controller='controls', action='index')}">Controls</a></li>
            % endif
        </ul>
    </div>

    <% flash = h._flash.pop_messages() %>
    % if flash:
    <ul id="flash">
        % for messages in flash:
        <li class="flash-level-${messages.message[1]['level']}">
            ${lib.icon(messages.message[1]['icon'])}
            ${messages.message[0]}
        </li>
        % endfor
    </ul>
    % endif

    <div id="content">
        ${next.body()}
    </div>

    <div id="footer-spacer"></div>
    <div id="footer">
        <p id="footer-stats">
            built in ${lib.timedelta(c.timer.total_time)} <br>
            ${c.timer.sql_queries} quer${ 'y' if c.timer.sql_queries == 1 else 'ies' }
                in ${lib.timedelta(c.timer.sql_time)}
        </p>
        <p>Icons from the <a href="http://p.yusukekamiyamane.com/">Fugue set</a></p>
    </div>

    % if config.get('super_debug', False):
    <%include file="/debugging.mako" />
    % endif
</body>
</html>

<%def name="title()">Untitled</%def>
