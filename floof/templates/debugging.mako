<%namespace name="lib" file="/lib.mako" />
<%! import os.path, pprint %>
<%! from pyramid.security import effective_principals %>

<ul id="x-debugging">
<li>
    <h5>Query log</h5>
    <h6>×${request.timer.sql_query_count} in ${lib.timedelta(request.timer.timers['sql'])}</h6>

    <div class="x-debugging-panel">
        <table id="x-debugging-query-log">
        <%! import datetime %>\
        % for query, data in request.timer.sql_query_log.iteritems():
        <tbody>
            <tr>
                <td>×${len(data)}</td>
                <td>${lib.timedelta( sum((datum['time'] for datum in data), datetime.timedelta()) )}</td>
                <th>${query}</th>
            </tr>
            % for instance in data:
            <tr>
                <td></td> <td></td>
                <td>
                    ${lib.timedelta(instance['time'])}: ${instance['caller']}<br>
                    ${instance['parameters']}
                </td>
            </tr>
            % endfor
        </tbody>
        % endfor
        </table>
    </div>
</li>
<li>
    <h5>Config</h5>
    <h6>${os.path.split(request.registry.settings['paste_config']['__file__'])[-1]}</h6>

    <pre class="x-debugging-panel">${pprint.pformat(request.registry.settings)}</pre>
</li>
<li>
    <h5>Session</h5>
    <h6>
        % if request.user:
        User ${request.user.name}
        % else:
        Anonymous user
        % endif
    </h6>

    <pre class="x-debugging-panel">
Session:
${pprint.pformat(request.session)}

Authn:
${pprint.pformat(request.auth)}

Principals:
${pprint.pformat(effective_principals(request))}

Current request context ACLs:
<% from floof.lib.auth import permissions_in_context %>\
<% ctx = request.context or request.root %>\
% while ctx is not None:
    ${getattr(ctx, '__name__', 'Unnamed Context') or 'Root'}:
<% perms = permissions_in_context(ctx, request) %>\
% if perms:
% for perm, allowed, upgradeable in perms:
        <% status = 'Upgradeable' if upgradeable else 'Denied' %>\
        ${perm}: ${'Allowed' if allowed else status}
% endfor
% else:
        None
% endif
<% ctx = getattr(ctx, '__parent__', None) %>\
% endwhile
    </pre>
</li>
<li>
    <h5>Time</h5>
    <h6>${lib.timedelta(request.timer.total_time)}</h6>

    <div class="x-debugging-panel">
        <table>
        <tbody>
            <tr>
                <th>SQL</th>
                <td>${lib.timedelta(request.timer.timers['sql'])}</td>
            </tr>
            <tr>
                <th>Mako</th>
                <td>${lib.timedelta(request.timer.timers['mako'])}</td>
            </tr>
            <tr>
                <th>Python</th>
                <td>${lib.timedelta(request.timer.timers['python'])}</td>
            </tr>
        </tbody>
        <tbody>
            <tr>
                <th>Total</th>
                <td>${lib.timedelta(request.timer.total_time)}</td>
            </tr>
        </tbody>
        </table>
    </div>
</li>
</ul>
<div id="x-debugging-toggler"><img src="${request.static_url('floof:public/icons/system-monitor.png')}" alt="dbg"></div>
