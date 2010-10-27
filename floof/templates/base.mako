<!DOCTYPE html>
<%namespace name="lib" file="/lib.mako" />
<html>
<head>
    <title>${self.title()} - ${config['site_title']}</title>
    <link rel="stylesheet" type="text/css" href="${url('css', which='reset')}">
    <link rel="stylesheet" type="text/css" href="${url('css', which='core')}">
</head>
<body>
    <div id="header">
        <div id="user">
            % if c.user:
                ${h.form(url(controller='account', action='logout'), class_='compact')}
                <p>
                    Logged in as ${c.user.display_name}.
                    <button type="submit">Log out</button>
                </p>
                ${h.end_form()}
            % else:
            <a href="${url(controller='account', action='login')}">Log in or register</a>
            % endif
        </div>
        <ul id="navigation">
            <li><a href="${url(controller='art', action='gallery')}">Art</a></li>
            <li><a href="${url(controller='art', action='upload')}">Upload</a></li>
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

    <div id="footer">
        Icons from the <a href="http://p.yusukekamiyamane.com/">Fugue set</a>
    </div>
</body>
</html>

<%def name="title()">Untitled</%def>
