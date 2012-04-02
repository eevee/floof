<%def name="stack2()">
    <% raise Exception %>
</%def>

<%def name="stack1()">
    ${stack2()}
</%def>

${stack1()}
