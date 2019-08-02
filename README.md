These are the scripts used to run ImSim for DC2 Run 2.1i on the UK grid.

runimsim2.1.sh is the script actually launched on the worker node when an ImSim job starts up. It unpacks the input instance catalogue file (which will have been automatically fetched from a storage element by this point) and runs ImSim with the correct arguments, then at the end of the job it packs up the generated FITS files into an archive named fits_<visit>_<index>.tar ready for upload to a storage element. It is also responsible for fetching, unpacking and setting up ImSim from a tar archive on a storage element, for compute nodes that do not have the required CVMFS repository mounted.

This script takes 5 arguments:

 1. The visit number. This is an 8 digit number and can be used to derive the name of the instance catalogue archive file.

 2. The name of the top level text file inside the instance catalogue archive.

 3. The zero-based index of the first sensor to run (0-188).

 4. The number of processes that ImSim should use, which is also the number of sensors that should be simulated. This is usually set to 4 for these jobs, except for the last job of a visit, for which it is set to 1.

 5. The index of this job within the visit (in the range 0-47).

Sometimes, if the instance catalogue does not contain any objects to be drawn onto any of the sensors, a job will produce no output. In this case the script creates a dummy output file. This is necessary because the grid middleware will generate an error if the output file does not exist, and this is not an error condition.


run_imsim_nersc.py is a copy of the same ImSim driver script used for DC2 runs at NERSC. It is invoked by runimsim2.1.sh after the input has been prepared. The line which sets the GalSim share directory has been commented out as it is incompatible with the grid runs, but everything else remains exactly the same as at NERSC.


jobmanager.py is the top level Python script that manages the submission of ImSim jobs via the Dirac API. It monitors the currently running jobs and automatically submits more if the number in the system falls below a certain threshold. It also automatically resubmits jobs that fail, and keeps a record of the grid sites at which the jobs run. Each visit requires 48 jobs in order to fully process it, and within each visit the jobs are tracked by an index number (0-47).

jobmanager.py maintains its state in a set of text files. The paths to these files are set near the top of the script. The function of these files is as follows:

 joblist.txt - contains a list of all the jobs currently in the system. Each line represents one job and contains the visit number (always 8 digits), the index number within the visit, and the Dirac job ID, separated by spaces. Before starting a new run, this should be created as an empty file.
 
 jobscompleted.txt - contains a list in exactly the same format as joblist.txt, but this time for completed jobs rather than active jobs. Again this should be created as an empty file before starting a new run.
 
 visitlist.txt - contains a list of visit IDs to process. Each line contains one 8 digit visit number. This is only read by the script, never written to. Before starting a new run, the visit IDs to be simulated should be put in here.
 
 visitposition.txt - contains a single number which keeps track of how many visits have already been submitted. Before starting a new run, this file should be initialised with "0".
 
 jobsites.txt - contains a list of Dirac job IDs and the name of the site where each one ran. Should be created as an empty file before starting a new run.

When the script is interrupted by CTRL-C, it will catch the signal and ensure that its current state is written to disk before terminating.

This script does not need to be running all the time. The jobs already submitted will progress fine without it, but no new jobs will be submitted until the script is run again.


To get up and running with this script, you need to:

 1. Edit the file paths within to point to the right directories.
 2. Create joblist.txt, jobscompleted.txt and jobsites.txt as empty files.
 3. Create visitlist.txt containing a list of all visit numbers to be processed.
 4. Create visitposition.txt containing the number 0.
 5. Run the script!


submit_visit.py can be used to submit a single visit, or a subset of a visit, to the grid for processing. Its first argument is the 8 digit visit number to submit. If any further arguments are present, they represent indices in the range 0-47, for jobs within the visit that should be submitted. If no further arguments are given, all 48 jobs are submitted. The job IDs are recorded in a file named 'visit_jobs_<visit>.txt'. This script does not integrate with the infrastructure used by jobmanager.py; instead, jobs submitted this way must be checked on manually.
