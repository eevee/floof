<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />
<%def name="title()">Cookies Disabled</%def>

<h1>Cookies Disabled</h1>

<p>You appear to have cookies disabled.</p>

<p>Unfortunately, ${config['site_title']} requires cookies to secure
most user actions against potential CSRF attacks.</p>

<p>You will need to enable cookies to log in.  Please reference your
web-browser's documentation if you are unsure about how to do this.</p>
