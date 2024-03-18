import csv
import cv2
import numpy as np
import os
import sys

from gazepoint_utils import fraction_to_pixel

# constants
OUTPUT_RESOLUTION_PX = (1140, 848)

# gaze position circle
POS_RADIUS = 10
POS_THICKNESS = 2
POS_COLOUR = (255, 255, 255, 255)

def plot_fixations(fixations, outfile_png):
    # the 4 is the number of channels (RGBA)
    canvas = np.zeros((*reversed(OUTPUT_RESOLUTION_PX), 4), np.uint8)

    for coords_frac in fixations:
        # convert the fractional coordinates into pixels
        (x_px, y_px) = fraction_to_pixel(*coords_frac, *OUTPUT_RESOLUTION_PX)

        if (x_px > OUTPUT_RESOLUTION_PX[0] or x_px < 0 or
            y_px > OUTPUT_RESOLUTION_PX[1] or y_px < 0):

            print("WARN: ignoring out of bounds data point:", (x_px, y_px))
            continue

        # add the position to the canvas
        cv2.circle(canvas, (x_px, y_px), POS_RADIUS, POS_COLOUR, POS_THICKNESS)

    cv2.imwrite(outfile_png, canvas)

if __name__ == '__main__':
    def printUsage():
        print("Usage:", __file__, "<fixations_csv> <outfile_png>")

    if len(sys.argv) < 3:
        printUsage()
        sys.exit(1)

    fixations_csv = sys.argv[1]
    if not os.path.exists(fixations_csv):
        raise ValueError("fixations_csv does not exist: " + fixations_csv)

    outfile_png = sys.argv[2]

    # pull out the coordinates from the file
    fixations = []
    with open(fixations_csv, 'r') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=",")

        for line in reader:
            fixations.append((float(line['x_frac']), float(line['y_frac'])))

    plot_fixations(fixations, outfile_png)

# EOF
