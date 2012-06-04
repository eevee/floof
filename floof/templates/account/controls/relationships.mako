<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="script_dependencies()">
    ${h.javascript_link(request.static_url('floof:assets/js/vendor/jquery.ui-1.8.7.js'))}
    ${h.javascript_link(request.static_url('floof:assets/js/widget/user_selector.js'))}
</%def>

<%def name="panel_title()">Watches</%def>
<%def name="panel_icon()">${lib.icon('users')}</%def>

<section>
    ## Only show art watches for now; the others don't have a remote chance of
    ## working yet
    % if watches:
    <table class="user-list">
        % for watch in watches:
        <tr>
            <td>${lib.user_link(watch.other_user)}</td>
        </tr>
        % endfor
    </table>
    % else:
    <p>You're not watching anyone!  How antisocial.</p>
    % endif
</section>

<section>
    <h1>Watch someone</h1>

    <%lib:secure_form method="GET" url="${request.route_url('controls.rels.watch')}">
        <p>
            <span class="text-plus-button">
                <input type="text" name="target_user" class="js-ui-user-selector"
                    data-autocomplete-source="${request.route_url('api:users.list')}"><button>→</button>
            </span>
        </p>
    </%lib:secure_form>
</section>
