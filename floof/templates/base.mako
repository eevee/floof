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
    <header>
        <div id="banner">
            <a id="site-title" href="${request.route_url('root')}">${request.registry.settings['site_title']}</a>
        </div>
        <nav>
        <!--
            <div id="user">
                ## XXX merge these
                ## XXX add and style logout
                ## XXX the column+section stuff is kinda grody
                ## XXX thereis a bunch of -moz- crap all over
                <span><a href="/users/eevee">eevee<img src="https://secure.gravatar.com/avatar/2c87a0857f4e3910154bc17a8f807b60"></a></span>
                <span><a href="/account/login">log in / register</a></span>
            </div>
            -->
            <menu id="user">
            % if request.user:
                <li>
                    <a href="${request.route_url('users.view', user=request.user)}">
                        ${request.user.name} ${lib.avatar(request.user)}
                    </a>
                    <menu>
                        <li>
                            ${lib.secure_form(request.route_url('account.logout'))}
                                <div><button>Log out</button></div>
                            ${h.end_form()}
                        </li>
                    </menu>
                </li>
            % else:
                <li><a href="${request.route_url('account.login')}">Log in or register</a></li>
            % endif
            </menu>
            <menu>
                ## XXX resurrect this with a mini-logo once there's some branding
                ##<li id="mini-site-title"><a id="site-title" href="${request.route_url('root')}">${request.registry.settings['site_title']}</a></li>
                ## XXX it would be cool if these links could just introspect
                ## the view, rather than duplicating the permission here
                <li><a href="${request.route_url('art.browse')}">Art</a></li>
                % if h.could_have_permission('art.upload', request.context, request):
                <li><a href="${request.route_url('art.upload')}">Upload</a></li>
                % endif
                <li><a href="${request.route_url('tags.list')}">Tags</a></li>
                ## XXX decorate these?
                % if request.user:
                    <li><a href="${request.route_url('controls.index')}">Controls</a></li>
                % endif
                % if h.could_have_permission('admin.view', request.context, request):
                    <li><a href="${request.route_url('admin.dashboard')}">Admin</a></li>
                % endif
            </menu>
        </nav>
    </header>

    <% flash_queue = request.session.pop_flash() %>
    % if flash_queue:
    <ul id="flash">
        % for flash in flash_queue:
        <li class="flash-level-${flash['level']}">
            ${lib.icon(flash['icon'])} ${flash['message']}
        </li>
        % endfor
    </ul>
    % endif

    ${next.body()}

    <footer>
        % if request.registry.settings.get('super_debug', False):
        <p id="footer-stats">
            built in ${lib.timedelta(request.timer.total_time)} <br>
            ${request.timer.sql_query_count} quer${ 'y' if request.timer.sql_query_count == 1 else 'ies' }
                in ${lib.timedelta(request.timer.timers['sql'])}
        </p>
        % endif
        <p>Icons from the <a href="http://p.yusukekamiyamane.com/">Fugue set</a></p>
        <p><a href="${request.route_url('log')}">Admin log</a></p>
    </footer>

    % if request.registry.settings['super_debug']:
    <%include file="/debugging.mako" />
    % endif
</body>
</html>

<%def name="title()">Untitled</%def>
<%def name="script_dependencies()"></%def>
