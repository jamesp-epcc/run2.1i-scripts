#!/usr/bin/env python
#
# Automatic ImSim manager script using Dirac

from DIRAC.Core.Base import Script
Script.parseCommandLine()
from DIRAC.Interfaces.API.Job import Job
from DIRAC.Interfaces.API.Dirac import Dirac

import signal, os, time

# constants
# data file paths
joblistfile = "/home/james/joblist.txt"
completedlistfile = "/home/james/jobscompleted.txt"
visitlist = "/home/james/visitlist.txt"
visitposition = "/home/james/visitposition.txt"
sensorfile = "/home/james/lsst_sensor_list.txt"
sitelistfile = "/home/james/jobsites.txt"

# how many jobs we should aim to have in the system at once
DESIRED_JOB_COUNT = 7500


# returns a list of tuples. each one contains:
#  - visit (8 digit string)
#  - index (int)
#  - Dirac job ID (int)
def readJobList(filename):
    listfile = open(filename, 'r')
    lines = listfile.readlines()
    listfile.close()
    result = []
    for line in lines:
        line = line.strip()
        bits = line.split(' ')
        result.append( (bits[0], int(bits[1]), int(bits[2])) )
    return result

def writeJobList(filename, joblist):
    listfile = open(filename, 'w')
    for job in joblist:
        listfile.write(job[0] + " " + str(job[1]) + " " + str(job[2]) + "\n")
    listfile.close()

def removeJobFromList(l, jobId):
    for i in range(0, len(l)):
        if l[i][2] == jobId:
            del l[i]
            return

def submitImsimJob(dirac, joblist, sensorblocks, visit, idx):
    j = Job()
    j.setName("ImSim_" + visit + "_" + str(idx));
    j.setCPUTime(1209600)

    instcatname = visit + ".tar.gz"
    
    insidename = 'phosim_cat_' + str(int(visit)) + '.txt'
        
    args = visit + ' ' + insidename + ' "' + ('^'.join(sensorblocks[idx])) + '" 4'

    print "Submitting ImSim job with arguments", args
    
    j.setExecutable('runimsim2.1.sh', arguments=args)
    j.stderr="std.err"
    j.stdout="std.out"
    j.setInputSandbox(["runimsim2.1.sh","LFN:/lsst/user/j/james.perry/instcats/2.1i/" + instcatname])
    j.setOutputSandbox(["std.out","std.err"])
    j.setTag(["4Processors"])
    j.setOutputData([visit + "/fits.tar"], outputPath="", outputSE=["UKI-NORTHGRID-LANCS-HEP-disk"])
    j.setPlatform("AnyPlatform")

    jobID = dirac.submitJob(j)

    # add to the list
    ok = jobID['OK']
    jobID = jobID['JobID']
    joblist.append( ( visit, idx, jobID ) )
    print "Adding job ID", jobID, "to list"
    return ok

# submit a whole batch of jobs for a complete visit
def submitBatch(dirac, joblist, sensorblocks, visit):
    print "*** Submitting jobs for", visit, "***"
    for i in range(0, len(sensorblocks)):
        submitImsimJob(dirac, joblist, sensorblocks, visit, i)


exitnow = False

def signalhandler(signum, frame):
    global exitnow
    print "Caught SIGINT, exiting after this iteration"
    exitnow = True
    

# start up Dirac first and create an instance
dirac = Dirac()

# read master job list
joblist = readJobList(joblistfile)
print "Read", len(joblist), "jobs from job list"

# read sensor name list
sensorfile = open(sensorfile, 'r')
sensorlines = sensorfile.readlines()
sensorfile.close()
print "Read", len(sensorlines), "sensors from sensor list"

# turn it into blocks
sensorblocks = []
i = 0
while i < len(sensorlines):
    block = []
    n = len(sensorlines) - i
    if n > 4:
        n = 4
    for j in range(0, n):
        line = sensorlines[i + j].strip()
        block.append(line)
    sensorblocks.append(block)
    i = i + n
print "Read sensorblocks:", sensorblocks

# read visits file
visitsfile = open(visitlist, 'r')
visitslines = visitsfile.readlines()
visitsfile.close()
visits = []
for line in visitslines:
    visits.append(line.strip())

# read input visit position and work out where we are
visitposfile = open(visitposition, 'r')
visitpos = int(visitposfile.read().strip())
visitposfile.close()

# install signal handler so we don't lose data when closing
signal.signal(signal.SIGINT, signalhandler)
signal.signal(signal.SIGTERM, signalhandler)

# enter main loop
while not exitnow:
    print "Running main loop"

    # check job statuses
    failedlist = []
    completedlist = []
    sitelist = []
    submittedjobs = 0
    runningjobs = 0
    otherjobs = 0

    # make a list of job IDs so we can request all the statuses at once from Dirac
    jobidlist = []
    for i in joblist:
        jobidlist.append(i[2])

    statuslist = dirac.status(jobidlist)

    for i in joblist:
        # get status from Dirac
        status = statuslist['Value'][i[2]]['Status']
        # if it failed, add it to the failed list
        if status == "Failed":
            failedlist.append(i);
        # if it completed, add it to the completed list
        elif status == "Done":
            completedlist.append(i)
            sitelist.append(statuslist['Value'][i[2]]['Site'])
        elif status == "Waiting":
            submittedjobs = submittedjobs + 1
        elif status == "Running":
            runningjobs = runningjobs + 1
        else:
            print "Job", i[2], "has status", status
            otherjobs = otherjobs + 1

    # print out status stats
    print "Current job distribution:"
    print "  ", submittedjobs, "submitted"
    print "  ", runningjobs, "running"
    print "  ", len(failedlist), "failed"
    print "  ", len(completedlist), "completed"
    print "  ", otherjobs, "other"

    # process failed list
    for i in failedlist:
        print "Job", i, "failed, resubmitting..."
        # remove this job from the main list now
        removeJobFromList(joblist, i[2])

        # resubmit it
        submitImsimJob(dirac, joblist, sensorblocks, i[0], i[1])


    # process completed list
    for j in range(0, len(completedlist)):
        i = completedlist[j]
        site = sitelist[j]
        print "Job", i, "completed at site", site, ", adding to completed list..."
        # remove this job from the main list now
        removeJobFromList(joblist, i[2])

        # append it to the completed list file
        compfile = open(completedlistfile, 'a')
        compfile.write(i[0] + " " + str(i[1]) + " " + str(i[2]) + "\n")
        compfile.close()

        # append site to the site list file
        compfile = open(sitelistfile, 'a')
        compfile.write(str(i[2]) + " " + site + "\n")
        compfile.close()

    time.sleep(5)

    # start new jobs if desired
    if len(joblist) < DESIRED_JOB_COUNT and visitpos < len(visits):
        # start next batch
        submitBatch(dirac, joblist, sensorblocks, visits[visitpos]);
        visitpos = visitpos + 1

        # save visit position
        visitposfile = open(visitposition, 'w')
        visitposfile.write(str(visitpos) + "\n")
        visitposfile.close()

    # write job list back to file at end of loop
    writeJobList(joblistfile, joblist)

print "Exited main loop"

