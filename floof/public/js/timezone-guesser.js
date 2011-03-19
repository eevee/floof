$(document).ready(function() {
    var tzs = document.getElementById("timezone");
    if (tzs.options[tzs.selectedIndex].value == "UTC") {
        var tz = determine_timezone().timezone.olson_tz;
        if (tz != "UTC") {
            for (var i = 0; i < tzs.options.length; i++) {
                if (tzs.options[i].value == tz) {
                    tzs.options.selectedIndex = i;
                    break;
                }
            }
        }
    }
});
