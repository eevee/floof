<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />

<section>
    <h1>${lib.user_link(target_user)}</h1>

    % if target_user.profile is None:
        <p>${target_user.display_name} has no profile.</p>
    % else:
        ${target_user.profile}
    % endif
</section>
