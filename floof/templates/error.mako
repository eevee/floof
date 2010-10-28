<%inherit file="/base.mako" />

<%def name="title()">${c.code}</%def>

<h1>${c.code}!</h1>

% if c.code == '404':
<p><tt>${c.req.path_info}</tt> could not be found.</p>
% else:
<p>${c.message}</p>
% endif
