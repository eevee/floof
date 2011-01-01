<%namespace name="lib" file="/lib.mako" />
<%! import os.path, pprint %>

<ul id="x-debugging">
<li>
    <h5>Query log</h5>
    <h6>×${c.timer.sql_queries} in ${lib.timedelta(c.timer.sql_time)}</h6>

    <div class="x-debugging-panel">
        <table id="x-debugging-query-log">
        <%! import datetime %>\
        % for query, data in c.timer.sql_query_log.iteritems():
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
    <h6>${os.path.split(config['__file__'])[-1]}</h6>

    <pre class="x-debugging-panel">${pprint.pformat(config)}</pre>
</li>
<li>
    <h5>Session</h5>
    <h6>
        % if c.user:
        User ${c.user.name}
        % else:
        Anonymous user
        % endif
    </h6>

    <pre class="x-debugging-panel">${pprint.pformat(session)}</pre>
</li>
<li>
    <h5>Time</h5>
    <h6>${lib.timedelta(c.timer.total_time)}</h6>

    <div class="x-debugging-panel">
        <table>
        <tbody>
            <tr>
                <th>SQL</th>
                <td>${lib.timedelta(c.timer.sql_time)}</td>
            </tr>
            <tr>
                <th>Mako</th>
                <td>${lib.timedelta(c.timer.template_time)}</td>
            </tr>
            <tr>
                <th>Python</th>
                <td>${lib.timedelta(c.timer.total_time - c.timer.sql_time - c.timer.template_time)}</td>
            </tr>
        </tbody>
        <tbody>
            <tr>
                <th>Total</th>
                <td>${lib.timedelta(c.timer.total_time)}</td>
            </tr>
        </tbody>
        </table>
    </div>
</li>
</ul>
<div id="x-debugging-toggler">debug</div>
