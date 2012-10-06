"use strict";

function gotVerifiedEmail(assertion) {
    if (assertion === null) {
        // user canceled; whatever man
        return;
    }

    // got an assertion, now send it up to the server for verification
    // TODO use that cutesy fake browser throbber thing
    $.ajax({
        type: 'POST',
        url: window.floofdata.persona_url,
        data: { assertion: assertion, csrf_token: window.floofdata.csrf_token },
        success: floofHandleAJAX(),
        error: floofHandleAJAXError
    });
}

$(function() {
    $('.persona').click(function(evt) {
        evt.preventDefault();
        navigator.id.get(gotVerifiedEmail);
    });
});


// TODO: handle persistent login correctly, oops!
// see: https://developer.mozilla.org/en/BrowserID/Advanced_Features
