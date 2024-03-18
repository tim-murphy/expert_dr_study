# find all strings.csv files in a directory and join them all together

import glob
import os
import sys

if __name__ == '__main__':
    def printUsage():
        print("Usage:", __file__, "<directory> <outfile_csv>")

    if len(sys.argv) < 3:
        printUsage()
        sys.exit(1)

    directory = sys.argv[1]
    if not os.path.isdir(directory):
        print("ERROR: invalid directory:", directory, file=sys.stderr)
        sys.exit(1)

    outfile_csv = sys.argv[2]

    string_lines = []
    for f in glob.glob(os.path.join(directory, "**", "strings.csv"),
                       recursive=True):
        dirname = os.path.split(f)[0]

        with open(f, 'r') as csvfile:
            header = next(csvfile)
            if len(string_lines) == 0:
                string_lines.append(header)

            for row in csvfile:
                string_lines.append(dirname + "##" + row)

    with open(outfile_csv, 'w') as outfile:
        for line in string_lines:
            print(line, file=outfile, end="")

    print(len(string_lines), "written to", outfile_csv)
    print("All done. Have a nice day :)")

# EOF
