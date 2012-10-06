"use strict";

function floofFlash(flashes) {
    // TODO make the transition smooth rather than "bouncy"
    // ie if there are the same number of flashes before and after, the content
    // shouldn't slide up then down again when the function fires
    var f;
    $('#flash').hide(200, function () {
        $('#flash li').remove();
        for (var i = 0; i < flashes.length; i++) {
            f = flashes[i];
            $('#flash').append(
                '<li class="flash-level-' + f.level + '">' +
                '<img src="' + f.icon_url + '">' +
                f.message + '</li>'
            );
        }
    });
    $('#flash').show(200);
}


function floofFormErrors(errors) {
    // XXX this uses the fact that each WTForm field populates its id attr with
    // its name; we may not actually want to rely on that behavior
    $('form p.form-error').remove();
    for (var field in errors) {
        for (var i = 0; i < errors[field].length; i++) {
            $('form #' + field).parent().append(
                '<p class="form-error">' + errors[field][i] + '</p>');
        }
    }
}


function floofHandleAJAX(onUpdate) {
    // Will call onUpdate with the parsed JSON response object on success
    // XXX should we be more flexible with when we allow updating?
    return function (data, status, xhr) {
        if (!data || !('status' in data)) {
            floofHandleAJAXError(xhr);
            return;
        }
        switch (data['status']) {
            case 'redirect':
                window.location = data['redirect-to'];
                break;
            case 'success':
                floofFlash(data['flash']);
                if (onUpdate)
                    onUpdate(data);
                break;
            case 'invalid-form':
                floofFormErrors(data['form-errors']);
            case 'failure':
                floofFlash(data['flash']);
                break;
            default:
                floofHandleAJAXError(xhr);
        }
    };
}


function floofHandleAJAXError(xhr) {
    // Handles error responses from AJAX requests
    var msg;
    try {
        msg = $.parseJSON(xhr.responseText).message;
    } catch (e) {
        // Leave response truthy-false
    }

    if (!msg) {
        if (xhr.status && xhr.status < 500)
            // We should always aim to yield a meaningful error message
            msg = 'Unspecified error.  Please file a bug report.';
        else
            // Not to say a status >= 500 never deserves a bug report,
            // but it should be logged automatically in production
            msg = 'Server error.  Please try again later.';
    }
    floofFlash([{
        // XXX what's the cleanest way to get an icon URL in here?
        message: 'Error:  ' + msg,
        level: 'error'
    }]);
}
