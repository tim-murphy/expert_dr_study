# take a raw fixation file and filter out noise to generate a string

import os
import sys

if __name__ == '__main__':
    def printUsage():
        print("Usage:", __file__, "<fix_string_csv> <outfile_csv>")

    if len(sys.argv) < 3:
        printUsage()
        sys.exit(1)

    ### parse command line args ###
    fix_string_csv = sys.argv[1]
    if not os.path.exists(fix_string_csv):
        raise ValueError("fix_string_csv does not exist: " + fix_string_csv)

    outfile_csv = sys.argv[2]
    good_data = []

    # remove entries where there is only one fixation for that AOI
    with open(fix_string_csv, 'r') as raw_data:
        good_data.append(next(raw_data))
        prev_aoi = None
        prev_aoi_count = 0

        for line in raw_data:
            # get the last column and strip the trailing newline character
            aoi = (line.split(",")[-1])[:-1]

            if prev_aoi != aoi and prev_aoi_count == 1:
                # single fixation for this AOI - remove it
                prev_aoi = aoi
                continue

            if prev_aoi != aoi:
                prev_aoi = aoi
                prev_aoi_count = 0

            prev_aoi_count += 1

            good_data.append(line)

    with open(outfile_csv, 'w') as ofile:
        for line in good_data:
            print(line, file=ofile, end="")

    print("All done, have a nice day :)")

# EOF
