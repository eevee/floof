$(function() {
    // When a panel item is clicked, show that panel
    $('ul#x-debugging li').click(function(e) {
        var $this = $(this);
        if ($(e.target).closest('.x-debugging-panel').length) {
            // Ignore clicks on the panel itself
            return;
        }

        var is_selected = $this.hasClass('selected');
        $this.closest('ul#x-debugging').find('li.selected').removeClass('selected');
        if (! is_selected) {
            $this.addClass('selected');
        }
    });

    // Toggler for the entire panel
    $('#x-debugging-toggler').click(function() {
        $.cookie(
            'debug-panel',
            $('#x-debugging').is(':visible') ? null : 'on'
        );
        $('#x-debugging').fadeToggle('fast');
    });

    // Preserve visibility across page loads
    if ($.cookie('debug-panel')) {
        $('#x-debugging').show();
    }
});
