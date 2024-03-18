# take a participant ID and append the grades to the end of the master file.

import os
import sys

def append_grades(participant_data_dir):
    STUDIES = ('thinkaloud', 'tracking')

    participant_id = os.path.split(participant_data_dir)[1]

    print("Participant:", participant_id)

    for study in STUDIES:
        print("  study: ", study, "...", end="", sep="")

        master_csv = os.path.join("processed_data", study + "_grades.csv")
        master_exists = True
        if not os.path.exists(master_csv):
            print("INFO: master file does not exist (creating):", master_csv)
            master_exists = False

        study_dir = os.path.join(participant_data_dir, study)
        if not os.path.isdir(study_dir):
            print("WARN: no data for " + study + " (skipping)")
            continue

        grades_csv = os.path.join(study_dir, "grades.csv")
        if not os.path.exists(grades_csv):
            print("WARN: no grades data for " + study + " (skipping)")
            continue

        lines_to_append = []
        with open(grades_csv, 'r') as gradesfile:
            lines_to_append += [line.strip() for line in gradesfile]

        # only add the header if the file doesn't exist already
        header = lines_to_append.pop(0)
        header = "subject_id," + header

        # add to the file
        with open(master_csv, 'a') as ofile:
            if not master_exists:
                print(header, file=ofile)

            for l in lines_to_append:
                line = str(participant_id) + "," + l
                print(line, file=ofile)

        print("done")

if __name__ == '__main__':
    def printUsage():
        print("Usage:", __file__, "<participant_data_dir>")

    if len(sys.argv) < 2:
        printUsage()
        sys.exit(1)

    participant_data_dir = sys.argv[1]
    if not os.path.isdir(participant_data_dir):
        raise ValueError("participant_data_dir does not exist: " + participant_data_dir)

    append_grades(participant_data_dir)

    print("All done. Have a nice day :)")

# EOF
