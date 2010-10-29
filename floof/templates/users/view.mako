<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />
<%namespace name="artlib" file="/art/lib.mako" />

<h1>${lib.icon('user-nude')} <a href="${url.current(action='profile')}">${c.this_user.name}</a></h1>
% for rel in ['by', 'for', 'of']:
<%
    arts = c.related_art.get(rel)
    if not arts:
        continue
%>
<h3>Art ${rel} ${c.this_user.name}</h3>
<ul class="thumbnail-grid">
  % for art in arts:
  ${artlib.thumbnail(art)}
  % endfor
</ul>
% endfor
