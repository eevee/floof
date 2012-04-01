<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="title()">Log in or register</%def>
<%def name="script_dependencies()">
    ${h.javascript_link(request.static_url('floof:public/js/browserid.js'))}
</%def>

<section>
<% auth = object() %>
% if request.user:
    <h1>You're already logged in, but...</h1>
    <p>We already know you as <code>${request.user.name}</code>.</p>
    <p>If you'd like to link another identity to your account, feel free to enter it below.</p>
    <p>Or you can just log into a different account.</p>
% else:
    <h1>Log in or register</h1>
% endif

<noscript>
    <p style="text-align: center; color: #600;">It looks like you don't have Javascript enabled for this site.
    <br />Unfortunately, BrowserID requires Javascript to work.</p>
</noscript>
<p style="text-align: center; font-size: 2em;"><a href="#" id="browserid" title="Sign-in with BrowserID">
    <img src="https://browserid.org/i/sign_in_blue.png" alt="Sign in with BorwserID" />
</a></p>
<script src="https://browserid.org/include.js" async></script>
<%
    path = request.route_path("account.browserid.login")
    if form.return_key.data:
        path = h.update_params(path, return_key=form.return_key.data)
%>\
<script type="text/javascript">
    $(browseridOnClick('#browserid', '${path}'));
</script>

<%lib:secure_form url="${request.route_url('account.register')}" id="postform">
    ${h.tags.hidden('display_only', value='true')}
</%lib:secure_form>

<aside class="sidebar">
    <h1>How will this work?</h1>
    <p>If you haven't used BrowserID before, then you will be asked to:</p>
    <ol>
        <li>Provide an email address;</li>
        <li>Follow a link sent via email to that address to prove it's yours; and</li>
        <li>Choose a password so you don't need to follow a link in an email every time</li>
    </ol>
    <p>You can then use your BrowserID account to log in to any site that supports BrowserID without needing to memorize additional passwords.</p>
</aside>

<section>
    <h1>Wait, what?</h1>

    <ul class="standard-list">
        <li>We don't ask you for a password directly.  We use BrowserID to let you log in using just your email address.</li>
        <li>Make sure you use an email account that's reliable.  If someone hacks your email account, they can log in here too.</li>
        <li>We don't tell anyone what email addresses you're using to log in.</li>
    </ul>
</section>


<h1>Alternative: Log in with OpenID</h1>
<%lib:secure_form url="${request.route_url('account.login_begin')}">
    <div id="big-ol-openid-box">
        ${form.return_key() | n}
        <span class="text-plus-button">
            ${form.openid_identifier(id="big-ol-openid-box--field", placeholder='you@gmail.com')}<!--
            --><button>Log in</button>
        </span>
    </div>
</%lib:secure_form>


<%
    openid_webfinger_shims = [
        ('Google', 'gmail.com', 'https://www.google.com/accounts/o8/id'),
        ('Yahoo!', 'yahoo.com', 'http://me.yahoo.com/'),
        ('AOL', 'aol.com', 'http://openid.aol.com/%s'),
        ('Steam', 'steamcommunity.com', 'http://steamcommunity.com/openid/'),
        ('LiveJournal', 'livejournal.com', 'http://%s.livejournal.com'),
        ('WordPress', 'wordpress.com', 'http://%s.wordpress.com/'),
        ('Blogger', 'blogger.com', 'http://%s.blogger.com/'),
        ('Blogger', 'blogspot.com', 'http://%s.blogspot.com/'),
        ('MySpace', 'myspace.com', 'http://myspace.com/%s'),
    ]
%>
<aside class="sidebar">
    <h1>Examples</h1>
    <p>Not every service supports OpenID.  Here are some common services you might already be using:</p>
    <ul class="standard-list">
        % for provider_name, provider_domain, provider_openid in openid_webfinger_shims:
            <li>${provider_name}: <kbd><var>username</var>@${provider_domain}</kbd></li>
        % endfor
    </ul>
    <p>Don't have any of these?  Check the longer <a href="http://en.wikipedia.org/wiki/OpenID#OpenID_Providers">list on Wikipedia</a>, or just <a href="https://www.myopenid.com/">create a myOpenID account</a>.</p>
</aside>


<section>
    <h1>Wait, what?</h1>

    <ul class="standard-list">
        <li>Don't want to use BrowserID?  Don't want to enable Javascript?  No problem; use OpenID!</li>
        <li>Just tell us about an account (or "identity") you already have with another service, and we'll use that to confirm who you are.</li>
        <li>For example, if you have a gmail account, enter <kbd><var>username</var>@gmail.com</kbd>.  Google will ask you to push a button to confirm, and that's it!</li>
        <li>It doesn't have to be an actual email address.  Steam works as <kbd><var>username</var>@steamcommunity.com</kbd>.</li>
        <li>Make sure you use an account that's reliable.  In the example above, if someone hacks your Google account, they can log in here, too.  And if Google goes down, you can't log in!</li>
        <li>We don't tell anyone what account you're using to log in; it's no different from giving us your email address.</li>
    </ul>
</section>

</section>
