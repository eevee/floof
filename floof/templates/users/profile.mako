<%inherit file="/base.mako" />

<h1>${c.this_user.display_name}</h1>

% if c.this_user.profile is None:
    <p>${c.this_user.display_name} has no profile.</p>
% else:
    ${c.this_user.profile}
% endif
