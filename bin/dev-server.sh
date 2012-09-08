#!/usr/bin/env bash

if [[ $# != 1 ]]; then
    echo "usage: $0 config-file.ini"
    exit
fi

# Absolute path to the floof checkout directory
DIR=$(dirname $(readlink -f $0))/..

# Tell pserve not to use the production-mode CSS compilation
FLOOF_SKIP_SASS_COMPILATION=1

# Is this a virtualenv...?
PSERVE=pserve
if [[ -n "$VIRTUAL_ENV" && -e "$VIRTUAL_ENV" ]]; then
    PSERVE="$VIRTUAL_ENV/bin/pserve"
elif [[ -e $DIR/../bin/pserve ]]; then
    PSERVE=$DIR/../bin/pserve
fi

### OK, run stuff

$PSERVE --reload -n dev $*
