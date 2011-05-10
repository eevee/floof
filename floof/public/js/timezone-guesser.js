// On page load, set the timezone to our best guess
$(document).ready(function() {
    var tzs = document.getElementById("timezone");
    // Only change it if it's at its default of UTC
    if (tzs.options[tzs.selectedIndex].value == "UTC") {
        var tz = determine_timezone().timezone.olson_tz;
        // tz's Olson name may not be in our list, so this may silently fail
        // under some circumstances, but that should be okay.
        for (var i = 0; i < tzs.options.length; i++) {
            if (tzs.options[i].value == tz) {
                tzs.options.selectedIndex = i;
                break;
            }
        }
    }
});
