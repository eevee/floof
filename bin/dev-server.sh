#!/usr/bin/env zsh

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
if [[ -e $DIR/../bin/paster ]]; then
    PASTER=$DIR/../bin/paster
fi


### OK, run stuff

sass --scss --quiet --watch ${DIR}/floof/sass:${DIR}/floof/public/css &

# Catch the incoming SIGINT that will kill paster and have it kill sass too
trap 'kill %1' 2

$PASTER serve --reload $*
