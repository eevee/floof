<%namespace name="lib" file="/lib.mako" />

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
</ul>
<div id="x-debugging-toggler">debug</div>
