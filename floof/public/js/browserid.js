function gotVerifiedEmailFactory(path) {
    return function gotVerifiedEmail(assertion) {
        // got an assertion, now send it up to the server for verification
        if (assertion !== null) {
            $.ajax({
                type: 'POST',
                url: path,
                data: { assertion: assertion, csrf_token: csrf_token },
                success: function(res, status, xhr) {
                    // TODO: handle a bum return value `res` (undefined or
                    // missing attributes, etc)
                    if (res === null) {}//loggedOut();
                    else if (res.post_id) {
                        form = $('#' + res.post_id)
                        form.action = res.next_url;
                        form.submit();
                    }
                    else location.href = res.next_url;
                },
                error: function(res, status, xhr) {
                    location.href = res.next_url;
                }
            });
        }
        else {
            // user aborted BrowserID authn
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
