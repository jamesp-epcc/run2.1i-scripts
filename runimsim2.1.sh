#!/bin/bash

# extract the instance catalogue
tar xzf ${1}.tar.gz
cd $1

# set up LSST and ImSim software
source /cvmfs/gridpp.egi.eu/lsst/sims_w_2019_10_1/setup.sh

# actually run ImSim
echo Running ImSim command imsim.py --processes $4 --sensors "$3" $2
imsim.py --processes $4 --sensors "$3" $2

# package up output
if [ -d fits ] ; then
    tar cf fits.tar fits/
else
    echo "Job produced no output!"
    mkdir fits # create dummy data so job doesn't fail
    echo "Dummy data" > fits/file.txt
    tar cf fits.tar fits/
fi

