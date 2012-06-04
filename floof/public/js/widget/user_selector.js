$.widget('floof.user_selector', $.ui.autocomplete, {
    options: {
    },

    _renderItem: function(ul, item) {
        return $('<li>')
            .data('item.autocomplete', item)
            .append($('<a>').html(item.label))
            .appendTo(ul);
    },
});

// Turn any elements with the right class into a user completer
$(function() {
    var make_autocomp_callback = function(url) {
        return function(req, resp) {
            // TODO use jq queues to avoid tons of firing?  or see if autocomp does this on its own
            console.log('firing callback');

            $.ajax({
                url: url,
                data: { 'name': req.term },
                success: function(data) {
                    // TODO needs the usual handling of status, sigh
                    var results = $.map(data.results, function(user) {
                        return {
                            label: user.name,
                            value: user.name
                        };
                    });
                    resp(results);
                },
                error: function() {
                    resp([]);
                }
            });
        };
    };

    $('.js-ui-user-selector').each(function() {
        var $this = $(this);
        
        var source = $this.data('autocomplete-source');
        if (! source) {
            return;
        }
        
        $this.user_selector({
            source: make_autocomp_callback(source),
            //minLength: 3,
        });
    });

});
