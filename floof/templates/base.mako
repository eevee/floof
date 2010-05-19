<!DOCTYPE html>
<html>
<head>
    <title>${self.title()}</title>
</head>
<body>
    <div id="header">
        <div id="user">
            % if c.user:
                ${h.form(url(controller='account', action='logout'), class_='compact')}
                <p>
                    Logged in as ${c.user.display_name}.
                    <button type="submit">Log out</button>
                </p>
                ${h.end_form()}
            % else:
            <a href="${url(controller='account', action='login')}">Log in or register</a>
            % endif
        </div>
    </div>
    <div id="content">
        ${next.body()}
    </div>
</body>
</html>

<%def name="title()">Untitled</%def>
