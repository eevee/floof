<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />

<h1>${lib.user_link(c.this_user)}</h1>

% if c.this_user.profile is None:
    <p>${c.this_user.display_name} has no profile.</p>
% else:
    ${c.this_user.profile}
% endif
