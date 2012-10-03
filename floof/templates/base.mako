<!DOCTYPE html>
<%namespace name="lib" file="/lib.mako" />
<html>
<head>
    <title>${self.title()} - ${request.registry.settings['site_title']}</title>
    <meta charset="utf-8" />
    <link rel="stylesheet" type="text/css" href="${request.route_url('pyscss', css_path='all')}">
    ${h.javascript_link('https://login.persona.org/include.js', async=True)}
    ${h.javascript_link(request.static_url('floof:assets/js/vendor/jquery-1.7.2.min.js'))}
    ${h.javascript_link(request.static_url('floof:assets/js/vendor/jquery.cookie.js'))}
    ${h.javascript_link(request.static_url('floof:assets/js/persona.js'))}

    ## Allow templates to define their script dependencies to include in head
    ${self.script_dependencies()}

    ## Super-duper JS globals -- important stuff only please
    <script type="text/javascript">
        <%! import json %>
        window.floofdata = ${json.dumps(dict(
            csrf_token=request.session.get_csrf_token(),
            persona_url=h.update_params(
                request.route_path("account.persona.login"),
                return_key=request.params.get('return_key')),
        )) | n};
    </script>
</head>
<body>
    <header>
        <div id="banner">
            <a id="site-title" href="${request.route_url('root')}">${request.registry.settings['site_title']}</a>
        </div>
        <nav>
            <menu id="user">
            % if request.user:
                <li>
                    <a href="${request.route_url('users.view', user=request.user)}">
                        ${request.user.name} ${lib.avatar(request.user)}
                    </a>
                    <menu>
                        <li>
                            <%lib:secure_form url="${request.route_url('account.logout')}">
                                <div><button>Log out</button></div>
                            </%lib:secure_form>
                        </li>
                    </menu>
                </li>
            % else:
                <li>
                    <a href="${request.route_url('account.login')}" class="persona">
                        <img src="${request.static_url('floof:assets/images/persona-signin.png')}" height="22" width="79" alt="Sign in with Persona" title="Sign in with Persona">
                        or register
                    </a>
                    <menu>
                        <li><a href="${request.route_url('account.login')}">More details</a></li>
                    </menu>
                </li>
            % endif
            </menu>
            <menu>
                ## XXX resurrect this with a mini-logo once there's some branding
                ##<li id="mini-site-title"><a id="site-title" href="${request.route_url('root')}">${request.registry.settings['site_title']}</a></li>
                ## XXX it would be cool if these links could just introspect
                ## the view, rather than duplicating the permission here
                <li><a href="${request.route_url('art.browse')}">Art</a></li>
                % if request.user.can('art.upload'):
                <li><a href="${request.route_url('art.upload')}">Upload</a></li>
                % endif
                <li><a href="${request.route_url('tags.list')}">Tags</a></li>
                ## XXX decorate these?
                % if request.user:
                    <li><a href="${request.route_url('controls.index')}">Controls</a></li>
                % endif
                % if request.user.can('admin.view'):
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
            ${lib.icon(flash['icon'])}
            % if flash['html_escape']:
                ${flash['message']}
            % else:
                ${flash['message'] | n}
            % endif
        </li>
        % endfor
    </ul>
    % endif

    ${next.body()}

    <footer>
        <p>Icons from the <a href="http://p.yusukekamiyamane.com/">Fugue set</a></p>
        <p><a href="${request.route_url('log')}">Admin log</a></p>
    </footer>
</body>
</html>

<%def name="title()">Untitled</%def>
<%def name="script_dependencies()"></%def>
