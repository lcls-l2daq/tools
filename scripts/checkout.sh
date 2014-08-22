#!/bin/bash

# $Id$

function show_help()
{
    echo    "Usage: $0 [-h] [-u <URL>] [-d <release_dir>]"
    echo    "       The default release_dir is 'release'"
    echo -n "       The default URL is \$DAQREPO "
    if [ -n "$DAQREPO" ]; then
        echo "($DAQREPO)"
    else
        echo "(Undefined variable)"
    fi
}

# default release_dir
release_dir="release"

# default URL
url=${DAQREPO:-undefined}

OPTIND=1
while getopts ":hu:d:" opt; do
    case "$opt" in
    h)
        show_help
        exit 0
        ;;
    \?)
        show_help
        exit 1
        ;;
    u)  url=$OPTARG
        ;;
    d)  release_dir=$OPTARG
        ;;
    esac
done

shift $((OPTIND-1))

[ "$1" = "--" ] && shift

if test "$#" -ne 0; then 
    show_help
    exit 1
fi

if [ "$url" == "undefined" ]; then
    echo "$0: cannot access repository: URL not defined"
    show_help
    exit 1
fi

if [ -a "$release_dir" ]; then
    echo "$0: cannot create directory \`$release_dir': File exists"
    exit 1
fi

set -e
/usr/bin/svn co $url/release/trunk  $release_dir
/usr/bin/svn co $url/pds/trunk      $release_dir/pds
/usr/bin/svn co $url/pdsapp/trunk   $release_dir/pdsapp
/usr/bin/svn co $url/ami/trunk      $release_dir/ami
/usr/bin/svn co $url/timetool/trunk $release_dir/timetool
/usr/bin/svn co $url/tools/trunk    $release_dir/tools
exit 0
