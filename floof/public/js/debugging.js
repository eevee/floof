$(function() {
    $('ul#x-debugging li').click(function(e) {
        var $this = $(this);
        if ($(e.target).closest('.x-debugging-panel').length) {
            // Ignore clicks on the panel itself
            return;
        }

        var is_selected = $this.is('.selected');
        $this.closest('ul#x-debugging').find('li.selected').removeClass('selected');
        if (! is_selected) {
            $this.addClass('selected');
        }
    });
    $('#x-debugging-toggler').click(function() {
        $('#x-debugging').toggleClass('visible');
    });
});
