<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">Change Avatar</%def>
<%def name="panel_icon()">${lib.icon('user')}</%def>

<% import hashlib %>

<%def name="avatar_box(avatar)">\
<div class="avatar-info-box clearfix">
    <%
    GRAVATAR_URL = "https://secure.gravatar.com/avatar/{hash}?r=r&s={size}&d=mm"
    if avatar:
        av_type = 'derived' if avatar.derived_image else 'uploaded'
        src=request.route_url('filestore', class_=u'avatar', key=avatar.hash)
    else:
        av_type = 'gravatar'
        email = request.user.email or ''
        hash = hashlib.md5(email.lower()).hexdigest()
        src = GRAVATAR_URL.format(hash=hash, size=120)
    %>\

    <% alt = 'gravatar' if av_type == 'gravatar' else 'avatar #{0}'.format(avatar.id) %>\
    <img class="avatar" alt="${alt}" src="${src}" />\

    <div class="info-box">
        <dl class="standard-deflist">
            <dt>Type</dt>
            <dd>${av_type.capitalize()}</dd>
            % if av_type == 'derived':
                <dt>Derived From</dt>
                <dd><a href="${request.route_url('art.view', artwork=avatar.derived_image)}">
                    ${avatar.derived_image.title or 'Untitled'}
                </a></dd>
            % endif
            % if av_type == 'gravatar':
                <dt>Gravatar Email</dt>
                <dd>${request.user.email or '<None>'} <span class="aside">(Your email address as
                specified in your <a href="${request.route_url('controls.info')}">
                User Info</a> page)</span></dd>
            % endif
            <%
                if av_type == 'gravatar':
                    active = not request.user.avatar
                else:
                    active = avatar == request.user.avatar
            %>
            % if avatar != request.user.avatar:
                <% route = 'controls.avatar.use_gravatar' if av_type == 'gravatar' else 'controls.avatar.use' %>
                ${lib.secure_form(request.route_url(route, avatar=avatar))}
                    <button>${lib.icon('tick')} Use as my avatar</button>
                </form>
            % endif
            % if not av_type == 'gravatar' and request.user.can('avatar.delete', avatar):
                ${lib.secure_form(request.route_url('controls.avatar.delete', avatar=avatar))}
                    <button>${lib.icon('minus')} Delete</button>
                </form>
            % endif
        </dl>
    </div>
</div>
</%def>\


<h1>Active Avatar</h1>

${avatar_box(request.user.avatar)}


<h1>Upload New Avatar</h1>

<p>New avatars may be uploaded directly using the form below</p>
<p>Alternatively, you may use the &quot;Make this my avatar&quot; link present
on the pages of image artworks.  This will let you crop already uploaded images
into avatars.</p>
<p>Note that uploaded avatars will be cropped to a square and resized to 120px.
</p>

${lib.secure_form(request.route_url('controls.avatar'), multipart=True)}
    <dl class="standard-form">
        ${lib.field(form.file)}
        ${lib.field(form.make_active)}
        <dd class="standard-form-footer">
            <button>Upload</button>
        </dd>
    </dl>
</form>


<h1>Available Avatars</h1>

% if not request.user.avatars:
    <p>None.</p>
    <p>To change your avatar, upload a new avatar above or derive an avatar
    from an existing artwork.</p>
% endif

% for avatar in reversed(request.user.avatars):
    <% if avatar == request.user.avatar: continue %>
    ${avatar_box(avatar)}
% endfor

% if request.user.avatar:
    ## Gravatar
    ${avatar_box(None)}
% endif
