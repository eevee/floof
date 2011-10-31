<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />
<%namespace name="artlib" file="/art/lib.mako" />

<%def name="title()">${target_user.display_name}</%def>

<nav class="user-nav">
    <div class="-avatar">${lib.avatar(target_user, size=50)}</div>
    <div class="-name">${target_user.name}</div>

    ## this is kinda grody until there are enough bits to flesh it out
    ## XXX check for perm here
    % if request.user != target_user:
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
</nav>

<section>
    <ul class="user-activity">
        % for action in activity:
        <li>
            <% artwork = action.artwork %>
            ##<a class="thumbnail" href="${request.route_url('art.view', artwork=artwork)}">
            <div class="user-activity-illus">
                <img src="${request.route_url('filestore', class_=u'thumbnail', key=artwork.hash)}" alt="">
            </div>
            ##</a>
            ${lib.time(artwork.uploaded_time)}<br>
            New art <strong>${action.relationship_type}</strong> ${target_user.display_name}:<br>
            ${artwork.title}
        </li>
        % endfor
    </ul>
</section>
