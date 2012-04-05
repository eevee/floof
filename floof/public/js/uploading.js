"use strict";

var UploadController = function() {
    if (! (window.FileReader && window.File && window.FormData && window.FileReader)) {
        // Old browser; none of this will work
        return null;
    }

    var this_controller = this;

    var $form = $('#upload-form');
    this.$form = $form;

    this.files = [];

    this.$upload_block = $form.find('.upload-block');

    // Play with the upload button.

    // XXX this is pretty specific and impl-specific stuff, break me out
    this.$thumbnail_container = this.$upload_block.find('.-part-thumbnail');
    this.$file_button = this.$upload_block.find('.-part-file-button button');
    this.$file_control = this.$upload_block.find('input[type="file"]');
    this.$upload_button = this.$upload_block.find('button[type="submit"]');

    this.set_state('init');

    this.attach_body_drag_handlers();

    // Turn a button click into a file upload click
    this.$file_button.click(function() {
        this_controller.$file_control.click();
    });

    // 2. Handle getting some files.
    this.$file_control.change(function(evt) {
        this_controller.accept_files(this.files);
    });

    // Intercept the actual upload
    // TODO put all these in a separate function come on
    this.$upload_button.click(function(evt) {
        evt.preventDefault();
        this_controller.ajax_submit();
    });
};
$.extend(UploadController.prototype, {
    set_state: function(state) {
        this.$upload_block.each(function() {
            this.className = this.className.replace(/\bstate-\S+/, '');
        });
        this.$upload_block.addClass('state-' + state);
    },

    // Make the whole page a drop zone for uploading.
    attach_body_drag_handlers: function() {
        var this_controller = this;

        // XXX split this stuff up between the actual form and the drag/drop bits,
        // so it can go on every page someday

        var $drop_target = $(document.body);
        var within_enter = false;

        $drop_target.bind('dragenter', function(evt) {
            // Default behavior is to deny a drop, so this will allow it
            evt.preventDefault();

            within_enter = true;
            setTimeout(function() { within_enter = false; }, 0);

            $(this).addClass('js-dropzone');

            console.log(evt.originalEvent.dataTransfer);  // .types
        });
        $drop_target.bind('dragover', function(evt) {
            // Same as above
            evt.preventDefault();

            // Show a cool 'copy' cursor
            evt.originalEvent.dataTransfer.dropEffect = 'copy';
        });
        $drop_target.bind('dragleave', function(evt) {
            console.log('leaving');
            // same as above?  necessary??
            // evt.preventDefault();

            if (! within_enter) {
                $(this).removeClass('js-dropzone');
            }
            within_enter = false;
        });

        // Handle the actual drop effect
        $drop_target.bind('drop', function(evt) {
            $(this).removeClass('js-dropzone');
            within_enter = false;

            evt.preventDefault();

            this_controller.accept_files(evt.originalEvent.dataTransfer.files);
        });
    },

    // Accept some files from either the upload control or drag/drop.
    // `files` is a FileList, not a regular Array
    accept_files: function(files) {
        var this_controller = this;
        console.log('got files', files);

        var SIZE = 160;

        // Remove any existing thumbnail first.
        // TODO multi-image concerns
        this_controller.$thumbnail_container.find('canvas').remove();

        $.each(files, function(idx, file) {
            // Skip non-images.
            // TODO this needs some kinda feedback message, and it will need to
            // be better when multi-image works
            if (! file.type.match(/^image/)) {
                return;
            }

            // Show a loading thing in the thumbnail box
            // TODO multi-image concern here
            this_controller.set_state('loading');
            this_controller.$thumbnail_container.append($('<div class="throbber"/>'));

            // Create an anon Image object; this will decode the image, then
            // copy itself to a canvas
            // TODO what if it's not a /valid/ image?
            var img = new Image();
            img.addEventListener('load', function(evt) {
                var img = evt.target;  // avoid circular ref

                // NOTE: this replicates the thumbnailing logic in the upload
                // controller; please keep in sync
                var $canvas = $('<canvas/>').attr({
                    width: String(SIZE),
                    height: String(SIZE)
                });
                var ctx = $canvas[0].getContext('2d');

                var height = img.height;
                var width = img.width;
                var ratio = Math.max(height, width) / SIZE;
                if (ratio > 1) {
                    height = Math.floor(height / ratio);
                    width = Math.floor(width / ratio);
                }

                ctx.drawImage(img,
                    Math.floor((SIZE - width) / 2),
                    Math.floor((SIZE - height) / 2),
                    width, height);

                // Indicate image properties
                var metadata_parts = [
                    String(img.width) + " × " + String(img.height)
                ];

                // TODO split me out too
                var filetype_parts = file.type.split('/');
                metadata_parts.push(filetype_parts[1].toUpperCase());
                metadata_parts.push(filetype_parts[0] + ",");

                // TODO and me...
                // TODO 900 bytes should be shown as kb
                if (file.size < 1024) {
                    metadata_parts.push(String(file.size));
                    metadata_parts.push("B");
                }
                else if (file.size < 1024 * 1024) {
                    metadata_parts.push(String(Math.round(file.size / 1024 * 10) / 10));
                    metadata_parts.push("KiB");
                }
                else {
                    metadata_parts.push(String(Math.round(file.size / 1024 / 1024 * 10) / 10));
                    metadata_parts.push("MiB");
                }

                // XXX this selector chain is stupid
                this_controller.$thumbnail_container.parent().find('.-part-metadata').html(file.name + "<br>" + metadata_parts.join(' '));


                // Success goes here!  All needs to sit together to avoid race
                // conditions and make bogus file handling work right
                // TODO multi-image concerns; this stuff should append, not
                // clobber
                this_controller.files = [];
                this_controller.files.push(file);

                this_controller.$thumbnail_container.find('.throbber').remove();
                this_controller.$thumbnail_container.append($canvas);

                this_controller.set_state('ready');
            });

            // Read the file as a data: URL and attach it to the Image
            var reader = new FileReader();
            // NOTE: as of this writing (apr '12), webkit doesn't support
            // addEventListener on FileReader objects
            reader.onload = function(evt) {
                img.src = evt.target.result;
            };

            reader.readAsDataURL(file);

            // Bail after the first valid image for now
            // TODO multi-image concerns
            return false;
        });
    },

    ajax_submit: function() {
        // Construct a FormData from the form's, er, data.
        // Disable the file upload control first, so its contents don't get
        // sent along
        this.$file_control.attr('disabled', true);
        var formdata = new FormData(this.$form[0]);
        this.$file_control.attr('disabled', false);

        // Then add in our collected files
        var field_name = this.$file_control.attr('name');
        $.each(this.files, function(idx, file) {
            formdata.append(field_name, file);
        });

        // And send it!

        // TODO this iframe should maybe be a global shared thing; this is pretty adhoc
        var $iframe = $('<iframe>').appendTo(document.body);
        $iframe[0].contentDocument.open();

        $.ajax({
            url: this.$form.attr('action'),
            type: 'POST',
            data: formdata,
            dataType: 'json',  // that is, the response type

            // Ask jQuery not to fuck with the formdata
            processData: false,
            contentType: false,

            success: function(data, status, xhr) {
                // XXX this is kinda generic ajax response handling
                if (data['status'] == 'redirect') {
                    window.location = data['redirect-to'];
                }
                else {
                    // TODO handle errors in some more useful manner
                    alert("Whoops, something fucked up.  And this error sucks, too!");
                }
            },
            complete: function() {
                $iframe.remove();
            }
        });
        // TODO error handling, where does a progress indicator go...
    },

    null:null
});

// XXX yeah uh this makes me hard to include anywhere but the upload page
$(function() {
    new UploadController();
});
