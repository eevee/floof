<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="title()">Log in or register</%def>

% if request.user:
<section>
    <h1>Hmm, you look kinda familiar.</h1>
    <p>Hey, you're already logged in as <code>${request.user.name}</code>.</p>
    <p>
        Feel free to log into another BrowserID or OpenID, though.
        You can then add it to this account, make a new account, or switch accounts.  Up to you.
    </p>
</section>
% endif

<section>
    <h1>Log in or register</h1>

    <div id="big-ol-browserid-box">
        <button class="browserid">
            <img src="https://browserid.org/i/sign_in_blue.png" height="22" width="79" alt="Sign in">
            with BrowserID
        </button>
    </div>

    <p>
        This works like any other email/password login, but thanks to the power
        of technology, we don't ever see or store your password.  Take
        <em>that</em>, hackers!
    </p>
    <p>
        Mozilla is the brain behind this system, called BrowserID;
        it's intended to be built into browsers someday.
        <a href="https://browserid.org/">Read the spiel, or manage your BrowserID, at browserid.org.</a>
    </p>
    <p>
        Be sure to use a good password, of course.
        Consider picking <a href="http://xkcd.com/936/">several English words at random</a> and
        stringing them together—as long as you <em>actually</em> pick at random, not off the
        top of your head.  Maybe grab your favorite book and use <a href="http://random.org">random.org</a>
        to pick random pages, then take the fifth word on each of those pages.  Be creative.
    </p>
</section>

<section>
    <h1>Alternatives</h1>

    <p>
        At the moment, BrowserID requires JavaScript.  That sucks.  If you
        prefer to leave JavaScript off, you can use OpenID instead.
    </p>

    <%lib:secure_form url="${request.route_url('account.login_begin')}">
        <div id="big-ol-openid-box">
            ${form.return_key() | n}
            <span class="text-plus-button">
                ${form.openid_identifier(id="big-ol-openid-box--field", placeholder='you@gmail.com')}<!--
                --><button>Log in</button>
            </span>
        </div>
    </%lib:secure_form>

    <p>
        We assume that, if you know enough to disable JavaScript, you probably
        know what <a href="http://openid.net/">OpenID</a> is.  If not, it works
        with a limited set of email-ish addresses, too; try entering a GMail
        address and hope for the best!
    </p>

    <p>
        Lastly, we do support SSL client certificates, but they're both finicky
        and extremely advanced.  If you really want to use them, register with
        one of the above options first, and look through the controls page;
        beyond that, you're on your own.
    </p>
</section>
