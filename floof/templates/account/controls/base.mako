<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="title()">${self.panel_title()} - Control panel</%def>

<h1>${self.panel_icon()} Control panel » ${self.panel_title()}</h1>

<ul id="control-panel-navigation">
    <li><a href="/">${lib.icon('fruit')} Apple</a></li>
    <li><a href="/">${lib.icon('fruit-grape')} Grape</a></li>
    <li><a href="/">${lib.icon('fruit-lime')} Lime</a></li>
    <li><a href="/">${lib.icon('fruit-orange')} Orange</a></li>
    <li class="selected">${lib.icon('question')} Current page</li>
    <li><a href="/">${lib.icon('fruit-orange')} Orange 2</a></li>
    <li><a href="/">${lib.icon('fruit-orange')} Orange 3</a></li>
</ul>

<div id="control-panel-content">
${next.body()}
