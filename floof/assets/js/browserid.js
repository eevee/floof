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
        url: window.floofdata.browserid_url,
        data: { assertion: assertion, csrf_token: window.floofdata.csrf_token },
        success: function(data, status, xhr) {
            // XXX this is kinda generic ajax response handling
            // XXX even moreso now that it's copy-pasted from uploading.js
            if (data['status'] == 'redirect') {
                window.location = data['redirect-to'];
            }
            else {
                // TODO handle errors in some more useful manner
                alert("Whoops, something fucked up with Persona login.  And this error sucks, too!");
            }
        },
        error: function(xhr, status, error) {
            alert("Whoops, something fucked up with Persona login.  And this error sucks, too!");
        }
    });
}

$(function() {
    $('.browserid').click(function(evt) {
        evt.preventDefault();
        navigator.id.get(gotVerifiedEmail);
    });
});


// TODO: handle persistent login correctly, oops!
// see: https://developer.mozilla.org/en/BrowserID/Advanced_Features

// TODO stop copy/pasting code around  :)
