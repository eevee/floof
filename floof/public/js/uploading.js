$(function() {
    var $form = $('#upload-form');

    // Play with the upload button.
    // 1. Replace it with a more friendly button.  Upload control is ugly.
    // XXX DON'T DO THIS ON OLD BROWSERS; IT WON'T WORK
    var $file_ctl = $form.find('input[type="file"]');
    var $file_container = $file_ctl.closest('p');
    var $thumbnail_container = $('<div class="-upload-thumbnail"/>');
    var $file_button = $('<button type="button">Choose a file</button>');
    var $dnd_protip = $('<p>or drag and drop from your computer</p>');
    var $upload_button = $form.find('button[type="submit"]').closest('p');
    $file_container.after(
        $('<p/>').append($file_button),
        $dnd_protip,
        $thumbnail_container);
    $file_container.hide();
    $thumbnail_container.hide();
    $upload_button.hide();

    // TODO indicate that these will each become separate artworks...
    $file_button.click(function() { $file_ctl.click(); });

    // 2. Handle getting some files.
    $file_ctl.change(function(evt) {
        $.each(this.files, function(idx, file) {
            // TODO needs webkit prefix
            var data_url = window.URL.createObjectURL(file);
            var img = new Image();
            img.onload = function() {
                // XXX comment all this about replicating logic from elsewhere
                // XXX unhardcode the 160
                // XXX show a loading throbber while the image resizes
                window.URL.revokeObjectURL(data_url);

                var $canvas = $('<canvas/>').attr({
                    width: '160', height: '160'
                });
                var ctx = $canvas[0].getContext('2d');

                var height = img.height;
                var width = img.width;
                var ratio = Math.max(height, width) / 160;
                if (ratio > 1) {
                    height = Math.floor(height / ratio);
                    width = Math.floor(width / ratio);
                }

                // TODO this looks like 
                ctx.drawImage(img,
                    Math.floor((160 - width) / 2),
                    Math.floor((160 - height) / 2),
                    width, height);

                $thumbnail_container.empty();
                $thumbnail_container.append($canvas);
            };
            img.src = data_url;
        });

        // TODO only do this on success
        $file_button.text("I changed my mind...");
        $dnd_protip.hide();
        $thumbnail_container.show();
        $upload_button.show();
    });
});
