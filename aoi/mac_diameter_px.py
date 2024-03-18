# The macula lutea is 5.5mm in diameter [1], and the distance from the disc to
# the fovea is 4.76mm [2]. We have the disc and mac coordinates for each image,
# so we can calculate the diameter of the macula lutea in pixels for each image
# and use this in our AOI region calculations.
#
# 1:    Remington, L.A.; Remington, L.A. Clinical Anatomy and Physiology of the Visual System.; Third edit.; Elsevier/Butterworth-Heinemann, 2012; ISBN 1437719260.
# 2:    Jonas, R.A.; Wang, Y.X.; Yang, H.; Li, J.J.; Xu, L.; Panda-Jonas, S.; Jonas, J.B. Optic Disc - Fovea Distance, Axial Length and Parapapillary Zones. The Beijing Eye Study 2011. PLoS One 2015, 10, e0138701.

import csv
from math import hypot
import os
import re
import sys

DISC_FOVEA_MM = 4.76
MAC_LUTEA_MM = 5.5

# given a coordinates file and filename regex, return a dictionary of diameters
# in millimeters (key: filename, value: [diameter, coords])
# note: we assume the coordinates file exists and is a CSV file with columns
#       <filename>,<nerve_x>,<nerve_y>,<fovea_x>,<fovea_y>
def getMacLuteaDiameters(coordinates_csv, filename_regex):
    diameters = {}

    with open(coordinates_csv, 'r') as csvfile:
        csvdata = csv.reader(csvfile, delimiter=',')
        next(csvdata) # skip the header

        regex = None
        try:
            regex = re.compile(filename_regex)
        except e:
            print("ERROR: invalid regular expression:", filename_regex)
            return diameters
            
        for row in csvdata:
            filename = row[0]
            if regex.match(filename) is not None:
                # we have a match!
                nerve_coords = (int(row[1]), int(row[2]))
                fovea_coords = (int(row[3]), int(row[4]))

                # calculate the disc-fovea distance using pythagoras
                disc_fovea_px = hypot(abs(nerve_coords[0] - fovea_coords[0]),
                                      abs(nerve_coords[1] - fovea_coords[1]))

                # now, assuming this pixel distance is DISC_FOVEA_MM, figure
                # out how many pixels MAC_LUTEA_MM is
                mac_diameter_px = round((disc_fovea_px / DISC_FOVEA_MM) * MAC_LUTEA_MM)

                # and that's it!
                diameters[filename] = (mac_diameter_px, fovea_coords)

    return diameters

if __name__ == '__main__':
    def printUsage():
        print("Usage:", __file__, "<coordinates_csv> [<filename_regex>]")

    if len(sys.argv) < 2:
        printUsage()
        sys.exit(1)

    coordinates_csv = sys.argv[1]
    if not os.path.exists(coordinates_csv):
        print("ERROR: coordinates CSV file does not exist:", coordinates_csv,
              file=sys.stderr)
        sys.exit(1)

    filename_regex = ".*"
    if len(sys.argv) > 2:
        filename_regex = sys.argv[2]

    print("Coordinates CSV file:", coordinates_csv)
    print("Filename regex:", filename_regex)
    print()

    diameters = getMacLuteaDiameters(coordinates_csv, filename_regex)

    if len(diameters) == 0:
        print("No filenames match the given regex:", filename_regex)

    for (filename, (diameter, coords)) in diameters.items():
        print(filename, ": ", diameter, "px at (",
              coords[0], ",", coords[1], ")", sep="")

# EOF
