# take a raw gazepoint output file and convert it to X,Y coordinates

import os
import re
import sys

if __name__ == '__main__':
    CSV_HEADER = ("x_frac", "y_frac")

    def printUsage():
        print("Usage:", __file__, "<input_txt> <output_csv>")

    if len(sys.argv) < 3:
        printUsage()
        sys.exit(1)

    input_txt = sys.argv[1]
    if not os.path.exists(input_txt):
        raise ValueError("input_txt does not exist: " + input_txt)

    output_csv = sys.argv[2]

    ### extract the coordinates ###
    csv_data = [CSV_HEADER]
    regex_string = r'BPOGX="([0-9\.]+)" BPOGY="([0-9\.]+)" BPOGV="1"'
    with open(input_txt, 'r') as rawfile:
        for line in rawfile:
            matches = re.search(regex_string, line)

            if matches is None:
                continue

            # if we get here, we have a valid coordinate
            fpogx = float(matches.group(1))
            fpogy = float(matches.group(2))

            csv_data.append((fpogx, fpogy))

    print(len(csv_data) - 1, "data points extracted")

    # data extracted! Write it to file
    with open(output_csv, 'w') as ofile:
        for coords in csv_data:
            print(",".join(map(str, coords)), file=ofile)

    print("data written to file:", output_csv)
    print("All done. Have a nice day :)")

# EOF
