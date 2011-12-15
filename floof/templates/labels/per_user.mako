<%inherit file="/base.mako" />
<%namespace name="artlib" file="/art/lib.mako" />

<%def name="title()">${target_user.name}'s labels</%def>

<section>
    <h1>${title()}</h1>

    <ul class="standard-list">
        % for label in target_user.labels_visible_to(request.user):
        <li>${artlib.label(label)}</li>
        % endfor
    </ul>
</section>
