<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />
<%namespace name="artlib" file="/art/lib.mako" />

<%def name="title()">${target_user.display_name}</%def>

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
            <div class="user-activity-date">${lib.time(artwork.uploaded_time)}</div>
            <a href="${request.route_url('art.view', artwork=artwork)}">${artwork.resource_title}</a><br>
            new art <strong>${action.relationship_type}</strong> ${target_user.display_name}<br>
        </li>
        % endfor
    </ul>
</section>
