#!/bin/bash
# Arguments:
#  - visit number (always full 8 digits)
#  - name of actual top level catalogue file within archive
#  - list of sensor names to run (quoted, and separated by ^)
#  - number of processes to run
#  - index number of job within visit

# extract the instance catalogue
tar xzf ${1}.tar.gz

# set up LSST and ImSim software
# use gridpp.egi.eu if it's there, otherwise use sw.lsst.eu and ImSim tarball
if [ -d /cvmfs/gridpp.egi.eu ] ; then
    source /cvmfs/gridpp.egi.eu/lsst/sims_w_2019_10_1/setup.sh
else
    source /cvmfs/sw.lsst.eu/linux-x86_64/lsst_sims/sims_w_2019_10/loadLSST.bash
    setup lsst_sims

    # extract and set up ImSim
    globus-url-copy gsiftp://lapp-se01.in2p3.fr/dpm/in2p3.fr/home/lsst/lsst/user/j/james.perry/imsim.tar.gz file://`pwd`/imsim.tar.gz
    tar xzf imsim.tar.gz
    cd imSim
    setup -r . -j
    cd ..
fi

cd $1

# actually run ImSim
echo Running ImSim command imsim.py --processes $4 --sensors "$3" $2
python run_imsim.py --processes $4 --sensors "$3" $2
result=$?
if [ $result -ne 0 ] ; then
    exit $result
else
# package up output
outputname=fits_${1}_${5}.tar.gz
if [ -d fits ] ; then
    tar cf $outputname fits/
else
    echo "Job produced no output!"
    mkdir fits # create dummy data so job doesn't fail
    echo "Dummy data" > fits/file.txt
    tar cf $outputname fits/
fi
fi
