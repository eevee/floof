#!/usr/bin/env bash

if [[ $# != 1 ]]; then
    echo "usage: $0 config-file.ini"
    exit
fi

# Absolute path to the floof checkout directory
DIR=$(dirname $(readlink -f $0))/..

# Tell paster not to use the production-mode CSS compilation
FLOOF_SKIP_SASS_COMPILATION=1

# Is this a virtualenv...?
PASTER=paster
if [[ -n "$VIRTUAL_ENV" && -e "$VIRTUAL_ENV" ]]; then
    PASTER="$VIRTUAL_ENV/bin/paster"
fi

### OK, run stuff

sass --scss --quiet --watch ${DIR}/floof/sass:${DIR}/floof/public/css &

# Catch the incoming SIGINT that will kill paster and have it kill sass too
trap 'kill %1' 2

$PASTER serve --reload -n dev $*

# Kill sass again just in case; might get here if paster dies on its own
kill %1
