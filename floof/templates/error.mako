<%inherit file="/base.mako" />

<%def name="title()">${status}</%def>

<h1>${status}!</h1>

% if status.startswith('404'):
<p>Can't find what you're looking for...</p>
% else:
<p>${message}</p>
% endif
