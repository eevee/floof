<%inherit file="/base.mako" />

<%def name="title()">${http_status}</%def>

<section>
    <h1>${http_status}</h1>

    <p>${message}</p>

% if outstanding_principals:

    % if len(outstanding_principals) == 1:
        <p>You may gain authorization by following the following steps:</p>
    % else:
        <p>You may gain authorization by following any of the following groups
        of steps:</p>
    % endif

    % for i, principal_group in enumerate(outstanding_principals):

        % if len(outstanding_principals) > 1:
            <h2>Alternative ${i + 1}</h2>
        % endif
        <ol>
        % for principal in principal_group:
            <li>${auth_actions[principal](request)}</li>
        % endfor
        </ol>

    % endfor

% endif
