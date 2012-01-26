function attachJcropWithPreview(target, preview, targetWidth, targetHeight,
                                previewDimension, formCoords) {
    return function() {

        // Attach Jcrop to the target (source) image
        target.Jcrop({
            onChange: onChangeCropBox,
            onSelect: onChangeCropBox,
            onRelease: releasePreview,
            aspectRatio: 1
        });

        // Set change event handlers on the HTML form inputs holding the
        // current cropping coordinated
        for (var c in formCoords) {
            formCoords[c].change(onChangeCoords);
        }

        // Update the preview display to reflect the given left, top, width
        // & height cropping co-ordinates
        function updatePreview(x, y, w, h) {

            var rx = previewDimension / w;
            var ry = previewDimension / h;

            preview.css({
                width: Math.round(rx * targetWidth) + 'px',
                height: Math.round(ry * targetHeight) + 'px',
                marginLeft: '-' + Math.round(rx * x) + 'px',
                marginTop: '-' + Math.round(ry * y) + 'px'
            }).show();
        }

        // Called on crop box manipulation.  Updates the preview image and
        // ensures that the HTML form co-ordinate input fields are read-only
        // and up to date
        function onChangeCropBox(coords)
        {
            if (parseInt(coords.w) > 0)
                updatePreview(coords.x, coords.y, coords.w, coords.h);

            for (var c in formCoords) {
                formCoords[c].attr('readonly', true);
            }
            formCoords['left'].val(coords.x);
            formCoords['top'].val(coords.y);
            formCoords['size'].val(coords.y2 - coords.y);
        }

        // Called on HTML form co-ordinate input field change.  Updates the
        // preview image if sane to do so, else hides it
        function onChangeCoords(eventObj) {
            var size = parseInt(formCoords['size'].val())
            if (size > 0)
                updatePreview(
                    parseInt(formCoords['left'].val()),
                    parseInt(formCoords['top'].val()),
                    size,
                    size
                );
            else
                preview.stop().fadeOut('fast');
        }

        // Called when the Jcrop crop box is dismissed.  Releases the read-only
        // property from the HTML form co-ordinate input fields
        function releasePreview()
        {
            onChangeCoords(null)
            for (var c in formCoords) {
                formCoords[c].removeAttr('readonly');
            }
        }

    }
}
