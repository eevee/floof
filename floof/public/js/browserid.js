function gotVerifiedEmailFactory(path) {
    return function gotVerifiedEmail(assertion) {
        // got an assertion, now send it up to the server for verification
        if (assertion !== null) {
            $.ajax({
                type: 'POST',
                url: path,
                data: { assertion: assertion, csrf_token: csrf_token },
                success: function(res, status, xhr) {
                    if (res === null) {}//loggedOut();
                    else location.href = res.next_url;
                },
                error: function(res, status, xhr) {
                    location.href = res.next_url;
                }
            });
        }
        else {
            // not sure what this implies yet
        }
    }
}

function browseridOnClick(domspec, submissionPath) {
    return function() {
        $(domspec).click(function() {
            callback = gotVerifiedEmailFactory(submissionPath);
            navigator.id.getVerifiedEmail(callback);
            return false;
        });
    }
}
