<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="title()">3rd Party Access Code for ${client.name}</%def>

<section>

<h1>Third Party Access Code for ${client.name}</h1>

<p>Provide the below code to the application (${client.name}) that requested
this access authorization.</p>

<p id="oauth-code" class="keybox">${code}</p>

</section>
