# take a list of fixations and a directory of AOI masks and generate a gazepath
# string.

import csv
import cv2
import glob
import os
import sys

from AOI import AOI
from Fixation import Fixation
from gazepoint_utils import fraction_to_pixel

if __name__ == '__main__':
    NO_AOI_STRING="other"

    def printUsage():
        print("Usage:", __file__, "<fixations_csv> <aoi_masks_dir> <outfile_csv>")
        print("      ", "AOI masks are bitmap files")

    if len(sys.argv) < 4:
        printUsage()
        sys.exit(1)

    ### parse command line arguments ###
    fixations_csv = sys.argv[1]
    if not os.path.exists(fixations_csv):
        raise ValueError("fixations_csv does not exist: " + fixations_csv)

    aoi_masks_dir = sys.argv[2]
    if not os.path.isdir(aoi_masks_dir):
        raise ValueError("aoi_masks_dir is not a valid directory: " + aoi_masks_dir)

    # we have two outfiles: one for the fixation string, and one for stats
    # (note that the stats can be derived from the fixation string output)
    outfile_csv = sys.argv[3]
    outfile_stats_csv = outfile_csv[:-3] + "stats.csv"

    ### load in the fixation data ###
    aoi_masks = {}
    rows = None
    cols = None
    for aoi in glob.glob(os.path.join(aoi_masks_dir, "*.bmp")):
        # this python magic converts "my/file/path/AOI.bmp" into "AOI"
        description = (os.path.split(aoi)[1])[:-4]

        aoi_masks[description] = cv2.imread(aoi, cv2.IMREAD_GRAYSCALE)
        if aoi_masks[description] is None:
            raise ValueError("Could not load AOI mask file: " + aoi)

        if len(aoi_masks) == 1:
            # first mask loaded, use these dimensions
            rows = len(aoi_masks[description])
            cols = len(aoi_masks[description][0])
        else:
            # make sure all files have the same dimensions
            if (rows != len(aoi_masks[description])) or (cols != len(aoi_masks[description][0])):
                raise ValueError(aoi + " is the wrong size, needs to be (" + cols + " x " + rows + ")")

    if len(aoi_masks) == 0:
        print("No mask files found in directory. Make sure they are bitmap files")
        sys.exit(1)

    print(len(aoi_masks), "AOI masks loaded:")
    for m in aoi_masks.keys():
        print(" ", m)

    print()
    print("===")
    print()

    ### fixation analysis ###
    fixation_stats = {}
    for aoi in list(aoi_masks.keys()) + [NO_AOI_STRING]:
        fixation_stats[aoi] = AOI(aoi) 

    # array of Fixation objects
    fixation_string = []
    with open(fixations_csv, 'r') as csvfile:
        csvreader = csv.DictReader(csvfile, delimiter=",")
        last_aoi = []
        for line in csvreader:
            # convert the fractional positions to pixels
            x_frac = float(line['x_frac'])
            y_frac = float(line['y_frac'])
            (x_px, y_px) = fraction_to_pixel(x_frac, y_frac, cols, rows)

            # make sure we are within bounds
            if y_px < 0 or y_px > rows or x_px < 0 or x_px > cols:
                print("WARN: ignoring out-of-bounds fixation: (", x_px,
                      ",", y_px, ")", sep="")
                continue

            matched_aois = []
            for aoi, mask in aoi_masks.items():
                if mask[y_px][x_px] > 0:
                    matched_aois.append(aoi)

                    fixation_stats[aoi].addFixation(
                        float(line['fixation_duration']),
                        (aoi not in last_aoi))

            if len(matched_aois) > 0:
                # this fixation lies over at least one mapped AOI
                for aoi in matched_aois:
                    fix = Fixation(line['fixation_id'],
                                   line['fixation_start'],
                                   line['fixation_duration'],
                                   x_px, y_px,
                                   aoi)
                    fixation_string.append(fix)
                print(*matched_aois, sep=" ", end="")
                print(" (duration:", line['fixation_duration'], "seconds)")
            else:
                # this fixation does not overlay an AOI
                if len(last_aoi) > 0:
                    fix = Fixation(line['fixation_id'],
                                   line['fixation_start'],
                                   line['fixation_duration'],
                                   x_px, y_px,
                                   NO_AOI_STRING)
                    fixation_string.append(fix)

                    print("[fixation without AOI]")

                fixation_stats[NO_AOI_STRING].addFixation(
                    float(line['fixation_duration']),
                    (len(last_aoi) > 0))

            last_aoi = matched_aois

    print()
    print("===")
    print()

    # write the fixation string to file
    with open(outfile_csv, 'w') as ofile:
        print(Fixation.csvHeader(), file=ofile)
        for fix in fixation_string:
            print(fix, file=ofile)

    # also write the stats
    with open(outfile_stats_csv, 'w') as ofile:
        print(AOI.csvHeader(), file=ofile)
        for aoi in fixation_stats.values():
            print(aoi, file=ofile)

    print("AOI stats")
    for aoi in fixation_stats.values():
        print(aoi.name)
        print("  total fixations = ", aoi.fixation_count, sep="")
        print("  visits = ", aoi.visits, sep="")
        print("  total time = ", aoi.total_time_sec, " seconds", sep="")

# EOF
