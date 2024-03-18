# Take a black and white image file and create a new black and white image file
# where every white pixel is converted into a filled circle of radius `a`,
# which is the accuracy in pixels of the measurement.

import cv2
import numpy as np
import os
import sys

if __name__ == '__main__':
    def printUsage():
        print("Usage:", __file__, "<outfile_bmp> <accuracy_px> <mask_bmp> [<mask_bmp> [...]]")

    ### command line parsing ###

    if len(sys.argv) < 4:
        printUsage()
        sys.exit(1)

    accuracy_px = int(sys.argv[2])
    if not accuracy_px > 0:
        raise ValueError("accuracy_px needs to be a positive integer: " + accuracy_px)

    outfile_bmp = sys.argv[1]

    mask_bmps = set()
    for mask_bmp in sys.argv[3:]:
        if not os.path.exists(mask_bmp):
            raise ValueError("mask_bmp does not exist: " + mask_bmp)
        mask_bmps.add(mask_bmp)

    # we do the set -> list dance to ensure no duplicates
    mask_bmps = list(mask_bmps)

    ### open the mask file and make sure it's valid ###
    print("Opening", mask_bmps[0], "to create the canvas...", end="")
    mask_data = cv2.imread(mask_bmps[0], cv2.IMREAD_GRAYSCALE)
    print("done.")

    if mask_data is None:
        raise ValueError("could not load mask_bmp")

    rows = len(mask_data)
    cols = len(mask_data[0])

    ### our new canvas ###
    new_canvas = np.zeros((rows, cols), dtype=np.uint8)
    assert(len(new_canvas) == rows)
    assert(len(new_canvas[0]) == cols)

    # loop through all of the masks and add them to our new canvas
    for mask_bmp in mask_bmps:
        print("Extracting mask data from", mask_bmp)
        mask_data = cv2.imread(mask_bmp, cv2.IMREAD_GRAYSCALE)

        # find all of the white pixels and draw a white circle at that position
        # on the new canvas
        white_pixels = 0
        for y in range(rows):
            for x in range(cols):
                if mask_data[y][x] != 0:
                    white_pixels += 1

                    # white pixel! Draw the circle on the new canvas
                    # Note: the last argument is thickness, -1 means fill
                    cv2.circle(new_canvas, (x,y), accuracy_px, (255), -1)

        print(white_pixels, "pixels found and converted")

    cv2.imwrite(outfile_bmp, new_canvas)

    print("New image written to", outfile_bmp)
    print("All done. Have a nice day :)")

# EOF
