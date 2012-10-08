(function($) {
    $.widget("ui.rater", {
        options: {
            rate_url: null,
            num_ratings: 0,
            rating_score: null,
            up_str: String.fromCharCode(0x2b06),
            down_str: String.fromCharCode(0x2b07),
            ambi_str: String.fromCharCode(0x2022),
            value: 0
        },

        _create: function() {
            var self = this,
                rate_span = $("<p></p>")
                            .addClass("ui-widget ui-voter");

            self.options.rate_span = rate_span;
            self.element.prepend(rate_span);

            // The rating num/score indicator
            var display = "<p class='rater-num-ratings'>" + self.options.num_ratings + "</p>";
            if (self.options.rating_score !== null)
                display += "<p class='rater-rating-score'>(" + self.options.rating_score + ")</p>";
            self.element.prepend($("<div></div>")
                        .addClass('rater-info')
                        .html(display));  // Text interspersed with elements makes doing this 'right' hard :p

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
                .click(function () { self._rate($(this).data('value')); });

            self._update_classes();
        },

        _rate: function(rating)
        {
            var self = this, post_data = {};

            if (self.options.value === rating) return;

            var oldrating = self.options.value;
            self.options.value = rating;

            post_data['rating'] = "" + rating;
            post_data['csrf_token'] = window.floofdata.csrf_token;
            post_data['asynchronous'] = 1;

            $.post(self.options.rate_url, post_data,
                function (data) {
                    // When we get the ajax response back, update the rating info text if necessary
                    if (self.options.num_ratings != data.num_ratings || self.options.rating_score != data.rating_score)
                    {
                        self.options.num_ratings = data.num_ratings;
                        self.options.rating_score = data.rating_score;
                        $('.rater-info').hide('fade', 100, function() {
                            $('.rater-num-ratings').text(self.options.num_ratings);
                            $('.rater-rating-score').text('(' + self.options.rating_score + ')');
                            $('.rater-info').show('fade', 100);
                        });
                    }
                })
                .error(floofHandleAJAXError)
                .error(function () {
                    self.options.value = oldrating;
                    self._update_classes();
                });

            self._update_classes();
        },

        // Uses the current rating value to determine the active button (i.e. the highlighted one)
        _update_classes: function() {
            var self = this;
            self.options.rate_span.children().each(function () {
                if ($(this).data('value') === self.options.value)
                    $(this).addClass('ui-rater-button-active');
                else
                    $(this).removeClass('ui-rater-button-active');
            });
        }
    });
})(jQuery);
