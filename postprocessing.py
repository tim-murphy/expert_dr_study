# any post-processing analysis that we want to do is done here. That way we
# keep the raw data files untouched and can process them differently later if
# we want to do a different analysis.

# example line:
# <REC CNT="2220575" TIME="38686.52734" TIME_TICK="4727430607263" FPOGX="0.552604" FPOGY="0.950926" FPOGS="38685.64062" FPOGD="0.88672" FPOGID="19518" FPOGV="1" BPOGX="0.522917" BPOGY="0.929630" BPOGV="1" LPCX="0.24446" LPCY="0.64614" LPD="28.07100" LPS="0.27720" LPV="1" RPCX="0.63893" RPCY="0.63643" RPD="24.67844" RPS="0.27720" RPV="1" CX="0.625521" CY="0.352778" CS="0" BKID="0" BKDUR="0.00000" BKPMIN="6" LPMM="6.09139" LPMMV="1" RPMM="5.39146" RPMMV="1" DIAL="0.77700" DIALV="1" GSR="0" GSRV="0" HR="0" HRV="0" HRP="0" TTL0="-1" TTL1="-1" TTLV="0" USER="1,0,0,1920,1080" />

import csv
import os
import re
import sys

# amount of time after a zoom change to ignore gaze data
ZOOM_CHANGE_INVALID_TIME_SEC=0.2

def process_data_file(infile, outdir, actual_grades_csv="image_grades.csv"):
    # error checking
    if not os.path.exists(actual_grades_csv):
        print("ERROR: grades file does not exist:", actual_grades_csv, file=sys.stderr)
        sys.exit(1)

    # all output files will use this prefix
    outfile_root = os.path.splitext(os.path.split(infile)[1])[0]

    # extract the data from the file
    raw_data = []
    with open(infile, 'r') as indata:
        for line in indata:
            raw_data.append(line)

    #############################################
    # ignore data within X sec from zoom change #
    #############################################

    last_zoom_time = -1.
    last_zoom_percent = -1.
    regex_extract = re.compile(r'^<REC.*TIME="(\d+\.\d+)".*USER="([\d\.]+),\d+,\d+,\d+,\d+".*>$')
    for index, line in enumerate(raw_data):
        tick_data = regex_extract.match(line)
        if tick_data is None:
            # no match
            continue

        tick_time = float(tick_data[1])
        tick_zoom = float(tick_data[2])
        tick_valid = True

        if index == 0:
            # first tick - accept and use as current values
            last_zoom_percent = tick_zoom
        elif tick_zoom != last_zoom_percent:
            # zoom change - reset the counter
            last_zoom_time = tick_time
            last_zoom_percent = tick_zoom
            tick_valid = False
        elif tick_time < (last_zoom_time + ZOOM_CHANGE_INVALID_TIME_SEC):
            # data too close to last zoom
            tick_valid = False

        if not tick_valid:
            # mark the gaze position and fixation data as invalid
            line = re.sub(r'FPOGV="1"', 'FPOGV="0"', line)
            line = re.sub(r'BPOGV="1"', 'BPOGV="0"', line)
            raw_data[index] = line

    # write the new data to disk
    with open(os.path.join(outdir, outfile_root + ".processed.txt"), 'w') as ofile:
        for line in raw_data:
            print(line, file=ofile, end="")

    ##########################################
    # extract zoom data for processing later #
    ##########################################

    regex_extract = re.compile(r'^<REC.*USER="([\d\.]+),\d+,\d+,\d+,\d+".*>$')
    tick_zooms = []
    for index, line in enumerate(raw_data):
        tick_data = regex_extract.match(line)
        if tick_data is None:
            # no match
            continue

        tick_zooms.append(float(tick_data[1]))

    with open(os.path.join(outdir, outfile_root + ".zooms.csv"), 'w') as ofile:
        for line in tick_zooms:
            print(line, file=ofile)

    #####################
    # extract the grade #
    #####################

    regex_grades = re.compile(r'^<ACK ID="USER_DATA" VALUE="dr:(-?\d+),dmo:(-?\d+)".*/>$')
    grades = None
    for line in reversed(raw_data):
        grades_data = regex_grades.match(line)
        if grades_data is None:
            continue

        grades = (int(grades_data[1]), int(grades_data[2]))
        break

    if grades is None:
        print("ERROR: no grading data found in file")
    else:
        # all grading info goes into a single CSV file
        grades_csv = os.path.join(outdir, "grades.csv")
        if not os.path.exists(grades_csv):
            with open(grades_csv, 'w') as ofile:
                print("file,dr_graded,dmo_graded,dr_actual,dmo_actual", file=ofile)

        # extract the actual grades for this image
        actual_grades = None
        with open(actual_grades_csv, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                if row[0] == outfile_root:
                    actual_grades = [int(row[1]), int(row[2])]
                    break

        if actual_grades is None:
            print("ERROR: grades not found for image:", outfile_root, file=sys.stderr)
            sys.exit(1)

        with open(grades_csv, 'a') as ofile:
            print(outfile_root, *grades, *actual_grades, sep=",", file=ofile)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage:", __file__, "<data_file> <output_dir>", file=sys.stderr)
        sys.exit(1)

    infile = sys.argv[1]
    if not os.path.exists(infile):
        print("ERROR: data_file does not exist:", infile)
        sys.exit(1)

    outdir = sys.argv[2]
    if not os.path.exists(outdir):
        os.makedirs(outdir, exist_ok=True)

    process_data_file(infile, outdir)

    print("done!")

# EOF
