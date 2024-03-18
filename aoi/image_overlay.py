# take two images and paint the second one over the first

import cv2
import os
import sys

def image_overlay(base_bmp, overlay_png, outfile_png):
    # base image - everything will be painted over this one (not overwritten)
    canvas = cv2.imread(base_bmp)
    canvas = cv2.cvtColor(canvas, cv2.COLOR_BGR2BGRA)

    # overlay image
    overlay = cv2.imread(overlay_png, cv2.IMREAD_UNCHANGED)

    # create a mask from the overlay
    mask = 255 - overlay[:,:,3]
    mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGBA)

    # clear any canvas pixels that are white in the mask
    canvas = cv2.bitwise_and(canvas, mask)

    # and paint the overlay onto the canvas
    canvas += overlay

    # all done! write to file and get out of here
    print("Writing overlayed image to", outfile_png)
    cv2.imwrite(outfile_png, canvas)

if __name__ == '__main__':
    def printUsage():
        print("Usage:", __file__, "<base_bmp> <overlay_png> <outfile_png>")

    if len(sys.argv) < 4:
        printUsage()
        sys.exit(1)

    base_bmp = sys.argv[1]
    if not os.path.exists(base_bmp):
        raise ValueError("base_bmp does not exist: " + base_bmp)

    overlay_png = sys.argv[2]
    if not os.path.exists(overlay_png):
        raise ValueError("overlay_png does not exist: " + overlay_png)

    outfile_png = sys.argv[3]

    # do the overlay and write to disk
    image_overlay(base_bmp, overlay_png, outfile_png)

    print("All done! Have a nice day:)")

# EOF
