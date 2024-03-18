# take a file containing gazepoint raw output, extract the fixation data, and
# write it to a new file.

import os
import re
import sys

if __name__ == '__main__':
    def printUsage():
        print("Usage:", __file__, "<gazepoint_data_txt> <outfile_csv>")

    if len(sys.argv) < 3:
        printUsage()
        sys.exit(1)

    ### parse command line arguments ###
    gazepoint_data_txt = sys.argv[1]
    if not os.path.exists(gazepoint_data_txt):
        raise ValueError("gazepoint_data_txt does not exist: " + gazepoint_data_txt)

    outfile_csv = sys.argv[2]

    ### extract the data ###
    fixation_offset = None # alter the fixation IDs to start at 1
    time_offset = None # alter each timestamp to be relative to the first data point
    fixations = {}
    regex_string = r'FPOGX="([0-9\.]+)" FPOGY="([0-9\.]+)" FPOGS="([0-9\.]+)" FPOGD="([0-9\.]+)" FPOGID="([0-9]+)" FPOGV="1"'
    with open(gazepoint_data_txt, 'r') as rawfile:
        for line in rawfile:
            matches = re.search(regex_string, line)

            if matches is None:
                continue

            fpogx = float(matches.group(1))
            fpogy = float(matches.group(2))
            fpogs = float(matches.group(3))
            fpogd = float(matches.group(4))
            fpogid = int(matches.group(5))

            # set the time offset
            if time_offset is None:
                time_offset = fpogs
            fpogs -= time_offset

            # change the IDs to start from 1
            if fixation_offset is None:
                fixation_offset = fpogid - 1
            fpogid -= fixation_offset

            fixations[fpogid] = [fpogx, fpogy, fpogs, fpogd]

    ### write to a CSV file ###
    with open(outfile_csv, 'w') as outfile:
        print("fixation_id,x_frac,y_frac,fixation_start,fixation_duration", file=outfile)

        for fix_id, fix_data in fixations.items():
            print(fix_id, *fix_data, sep=",", file=outfile)

    print("All done. Have a nice day :)")

# EOF
