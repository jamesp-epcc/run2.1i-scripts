#!/bin/bash
#
# Script to upload input data from Cori to GridPP, via GridFTP.
# This script should be run on Cori. It will upload everything in the current
# directory, but if an argument is given it will start from that file and ignore
# everything before it!
#

desturl=gsiftp://gfe02.grid.hep.ph.ic.ac.uk/pnfs/hep.ph.ic.ac.uk/data/lsst/lsst/user/j/james.perry/instcats/2.1i
resultsfile=~/grid_uploads.txt

startfrom=
uploading=1
if [ $# -eq 1 ] ; then
    startfrom=$1
    uploading=0
fi

# loop over files in this directory
for i in * ; do
    # check if it's time to start uploading
    if [ $uploading -eq 0 ] ; then
	if [ $i == $startfrom ] ; then
	    uploading=1
	fi
    fi

    # if we're uploading...
    if [ $uploading -eq 1 ] ; then
	src=file://`pwd`/${i}
	dest=${desturl}/${i}
	globus-url-copy -vb ${src} ${dest}
	if [ $? -eq 0 ] ; then
	    # success. record file name and size
	    set -- `ls -l ${i}`
	    size=$5
	    echo "${i} ${size}" >> $resultsfile
	else
	    # error
	    echo "${i} ERROR!" >> $resultsfile
	fi
    fi
done

