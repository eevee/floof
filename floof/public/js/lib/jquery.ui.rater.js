(function($) {
    $.widget("ui.rater", {
        options: {
            rate_url: null,
            auth_token: null,
            auth_token_field: 'auth_token',
            num_ratings: 0,
            rating_sum: 0,
            up_str: String.fromCharCode(0x2b06),
            down_str: String.fromCharCode(0x2b07),
            ambi_str: String.fromCharCode(0x2022),
            value: 0
        },

        _create: function() {
            var self = this,
                rate_span = $("<span></span>")
                            .addClass("ui-widget ui-voter");

            self.options.rate_span = rate_span;
            self.element.prepend(rate_span);

            // The rating sum/num rating indicator
            self.element.prepend($("<div></div>")
                        .addClass('rater-info')
                        .html("<span class='rater-num-ratings'>" + self.options.num_ratings + "</span> (<span class='rater-rating-sum'>" + self._display_rating(self.options.rating_sum) + "</span>)")); // Text interspersed with elements makes doing this 'right' hard :p

            rate_span.append($("<a>" + self.options.up_str + "</a>")
                      .addClass('ui-rater-button-up')
                      .data({'value': 1}));

            rate_span.append($("<a>" + self.options.ambi_str + "</a>")
                      .addClass('ui-rater-button-ambi')
                      .data({'value': 0}));

            rate_span.append($("<a>" + self.options.down_str + "</a>")
                        .addClass('ui-rater-button-down')
                        .data({'value': -1}));

            // Store the rating value (-1,0,1) in data associated with the element
            rate_span.children("a")
                .click(function() {
                  self._rate($(this).data('value'));
                })
                .hover(function() { $(this).addClass('ui-rater-button-active'); },
                       function() {
                            if ($(this).data('value') != self.options.value)
                                $(this).removeClass('ui-rater-button-active');
                        });

            self._update_classes();
        },
        _rate: function(rating)
        {
            var self = this, post_data = {};

            if (self.options.value == rating) return;

            self.options.value = rating;

            post_data['rating'] = "" + rating;
            post_data[self.options.auth_token_field] = self.options.auth_token;
            post_data['asynchronous'] = 1;

            $.post(self.options.rate_url, post_data,
                function (data) {
                    // When we get the ajax response back, update the rating info text if necessary
                    if (self.options.num_ratings != data.ratings || self.options.rating_sum != data.rating_sum)
                    {
                        self.options.num_ratings = data.ratings;
                        self.options.rating_sum = data.rating_sum;
                        $('.rater-info').hide('fade', 100, function() {
                            $('.rater-num-ratings').text(self.options.num_ratings);
                            $('.rater-rating-sum').text(self._display_rating(self.options.rating_sum));
                            $('.rater-info').show('fade', 100);
                        });
                    }
                });

            self._update_classes();
        },
        // Uses the current rating value to determine the active button (i.e. the highlighted one)
        _update_classes: function() {
            var self = this;
            self.options.rate_span.children().each(function () {
                if ($(this).data('value') == self.options.value)
                    $(this).addClass('ui-rater-button-active');
                else
                    $(this).removeClass('ui-rater-button-active');
            });
        },
        // Converts null to an em dash for display
        _display_rating: function(rating) {
            if (rating == null) {
                return '—'
            }
            else {
                return rating
            }
        }
    });
})(jQuery);
