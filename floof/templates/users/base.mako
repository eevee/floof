<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />

<nav class="user-nav">
    <div class="-avatar">${lib.avatar(target_user, size=80)}</div>
    <div class="-name">${target_user.name}</div>

    ## this is kinda grody until there are enough bits to flesh it out
    ## XXX check for perm here
    % if request.user and request.user != target_user:
    <div>
        <a href="${h.update_params(request.route_url('controls.rels.watch'), target_user=target_user.name)}">
            % if any(watch.other_user == target_user for watch in request.user.watches):
            ${lib.icon(u'user--pencil')} Modify watch
            % else:
            ${lib.icon(u'user--plus')} Watch
            % endif
        </a>
    </div>
    % endif

    <ul class="-subpages">
        <li class="-current">${lib.icon('fruit')} activity</li>
        <li>${lib.icon('information')} about me</li>
        <li><a href="${request.route_url('users.art', user=target_user)}">${lib.icon('fruit')} art</a></li>
        <li>${lib.icon('lock')} albums</li>
    </ul>
</nav>

${next.body()}
