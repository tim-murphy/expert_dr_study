# Combine all of the fixation stats into one giant file for graphing.
# Will look for files in the format "*_fixation_string.stats.csv"

import csv
import glob
import os
import sys

from create_fixation_string import get_score

# only include optoms and ophthals
EXCLUDE_IDS = (1461, 1854, 1894)

if __name__ == '__main__':
    def printUsage():
        print("Usage:", __file__, "<results_dir> <grades_csv> <output_csv>")

    if len(sys.argv) < 4:
        printUsage()
        sys.exit(1)

    results_dir = sys.argv[1]
    if not os.path.isdir(results_dir):
        print("ERROR: invalid results_dir:", results_dir, file=sys.stderr)
        sys.exit(1)

    grades_csv = sys.argv[2]
    if not os.path.exists(grades_csv):
        print("ERROR: grades_csv does not exist:", grades_csv, file=sys.stderr)
        sys.exit(1)

    output_csv = sys.argv[3]

    # find any fixation string stats files in the directory
    string_lines = []
    for f in glob.glob(os.path.join(results_dir, "**", "*_fixation_string.stats.csv"),
                       recursive=True):
        # from the filename we can extract the image and subject_id
        path_hier = os.path.normpath(f).split(os.path.sep)
        image_name = path_hier[-3]
        subject_id = path_hier[-2]

        if int(subject_id) in EXCLUDE_IDS:
            continue

        # calculate a grading score for this participant
        score, grade = get_score(f, grades_csv)
        if score is None:
            score = -100 # magic number :(

        # also calculate a refer score
        score_refer, _ = get_score(f, grades_csv, True)
        if score_refer is None:
            score_refer = -100

        with open(f, 'r') as csvfile:
            header = next(csvfile)
            if len(string_lines) == 0:
                string_lines.append("image,subject_id,grade,score,refer_score," + header)

            reader = csv.DictReader(csvfile, fieldnames=header.split(','))
            for row in reader:
                # only add AOIs that were actually visited
                if int(row['fixation_count']) > 0:
                    string_lines.append(','.join((image_name, subject_id,
                                                  str(grade), str(score),
                                                  str(score_refer),
                                                  *row.values(), '\n')))

    # and write it all to file
    with open(output_csv, 'w') as ofile:
        for l in string_lines:
            print(l, end="", file=ofile)

    print(len(string_lines), "lines written to", output_csv)
    print("All done! Have a nice day :)")

# EOF
