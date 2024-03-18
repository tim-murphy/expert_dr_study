# take a folder of masks (filename as mask descriptors) and merge them into a
# uint64 matrix of the same dimensions with each element as a bitmask showing
# where AOIs exist (and overlap). This can be used to identify which AOI(s)
# a given fixation is linked to.

import cv2
import glob
import numpy as np
import os
import sys

if __name__ == '__main__':
    def printUsage():
        print("Usage:", __file__, "<mask_dir> <outfile_dat>")

    if len(sys.argv) < 3:
        printUsage()
        sys.exit(1)

    ### parse command line arguments ###
    mask_dir = sys.argv[1]
    if not os.path.isdir(mask_dir):
        raise ValueError("mask_dir is not a valid directory")

    outfile_dat = sys.argv[2]
    mask_files = glob.glob(os.path.join(mask_dir, "*.bmp"))

    if len(mask_files) == 0:
        print("No bitmap files found in mask directory")
        printUsage()
        sys.exit(1)

    print(len(mask_files), "mask files found")

    # mask data
    rows = None
    cols = None
    matrix = None
    bitmask = 0x1
    masks = []

    for f in mask_files:
        mask = cv2.imread(f, cv2.IMREAD_GRAYSCALE)
        if mask is None:
            raise ValueError("Could not load mask: " + f)

        # make sure the masks all have the same dimensions
        if matrix is None:
            rows = len(mask)
            cols = len(mask[0])
            matrix = np.zeros((rows, cols), dtype=np.uint64)
        elif (len(mask) != rows) or (len(mask[0]) != cols):
            raise ValueError(f + " image dimensions do not match: should be (" + cols + "," + rows + ")")

        # this python magic converts "my/file/path/AOI.bmp" into "AOI"
        description = (os.path.split(f)[1])[:-4]
        masks.append(description)

        # add this mask to the matrix
        for y in range(rows):
            for x in range(cols):
                if mask[y][x] != 0:
                    matrix[y][x] |= np.uint64(bitmask)

        # shift the bitmask along
        bitmask <<= 1

    # write to disk
    with open(outfile_dat, 'w') as of:
        matrix.tofile(of)

# EOF
