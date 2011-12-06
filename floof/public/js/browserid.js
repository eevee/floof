function redirect(response) {
    alert(response.next_url);
    location.href = response.next_url;
}

function gotVerifiedEmail(assertion) {
    // got an assertion, now send it up to the server for verification
    if (assertion !== null) {
        $.ajax({
            type: 'POST',
            url: '/account/browserid/login',
            data: { assertion: assertion, csrf_token: csrf_token },
            success: function(res, status, xhr) {
                if (res === null) {}//loggedOut();
                else redirect(res);
            },
            error: function(res, status, xhr) {
                redirect(res);
            }
        });
    }
    else {
        // not sure what this implies yet
    }
}

$(function() {
    $('#browserid').click(function() {
        navigator.id.getVerifiedEmail(gotVerifiedEmail);
        return false;
    });
});
