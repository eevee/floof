<%inherit file="/base.mako" />
<%namespace name="artlib" file="/art/lib.mako" />

<%def name="title()">${target_user.name}'s labels</%def>

<section>
    <h1>${title()}</h1>

    <ul class="standard-list">
        % for label in request.user.permitted('label.view', target_user.labels):
        <li>${artlib.label(label)}</li>
        % endfor
    </ul>
</section>
