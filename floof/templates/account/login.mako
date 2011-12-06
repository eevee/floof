<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="title()">Log in or register</%def>
<%def name="script_dependencies()">
    ${h.javascript_link('/js/browserid.js')}
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

${lib.secure_form(request.route_url('account.login_begin'))}
    <div id="big-ol-openid-box">
        ${form.return_key() | n}
        <span class="text-plus-button">
            ${form.openid_identifier(id="big-ol-openid-box--field", placeholder='you@gmail.com')}<!--
            --><button>Log in</button>
        </span>
    </div>
${h.end_form()}

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
        <li>We don't ask you for a password.  Just tell us about an account (or "identity") you already have with another service, and we'll use that to confirm who you are.</li>
        <li>For example, if you have a gmail account, enter <kbd><var>username</var>@gmail.com</kbd>.  Google will ask you to push a button to confirm, and that's it!</li>
        <li>It doesn't have to be an actual email address.  Steam works as <kbd><var>username</var>@steamcommunity.com</kbd>.</li>
        <li>Make sure you use an account that's reliable.  In the example above, if someone hacks your Google account, they can log in here, too.  And if Google goes down, you can't log in!</li>
        <li>We don't tell anyone what account you're using to log in; it's no different from giving us your email address.</li>
    </ul>
</section>

<section>
    <h1>How it works</h1>
    <p>You shouldn't have to care, but...</p>
    <p>This system is called OpenID, and it's designed to let you prove you own a URL.</p>
    <p>You can enter something that looks like an email address because we also support Webfinger, a system for asking a Web site about its users.  For common OpenID providers that don't also support Webfinger, we fake it.</p>
    <p>You can read a bunch of stuff on <a href="http://en.wikipedia.org/wiki/OpenID">Wikipedia</a> or at the <a href="http://openid.net/">OpenID Foundation</a>.</p>
</section>


<h1>Log in with BrowserID</h1>
<noscript>
    <p>It looks like you don't have Javascript enabled for this site.</p>
    <p>Unfortunately, BrowserID requires Javascript to work.</p>
</noscript>
<a href="#" id="browserid" title="Sign-in with BrowserID">
    <img src="https://browserid.org/i/sign_in_blue.png" alt="Sign in">
</a>
<script src="https://browserid.org/include.js" async></script>

</section>
