<%inherit file="/base.mako" />

<section>
<p>Hello, world!</p>

<p>Front page is blank for now, sorry!</p>
</section>

<section>
<h1>Oh hey wait a sec</h1>

<p>Yo, we have a new and less-awkward login doohicky now.</p>

<p>If you already registered with OpenID, no worries; that still works too.  You can switch pretty easily: log in with OpenID again, then go <em>back</em> to <a href="${request.route_url('account.login')}">the login page</a> and log in with BrowserID, and you can add that id to your account.</p>

</section>
