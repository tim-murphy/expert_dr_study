# For each participant, go through each result and extract the zoom statistics
# and grades.
# Store these results in a giant CSV file to be assessed later.

import argparse
import csv
import glob
import os
import re
import sys

KEY_GROUP = "expert_group"
KEY_IMAGES = "images"
KEY_AGE = "age"
KEY_EXPERIENCE = "experience"

# "Actual" zoom levels. We compare the "recorded" zoom levels to this list
# to avoid rounding errors (yay floating point).
ZOOM_LEVELS = [ 1.0 ]
for _ in range(10): # more than actually used, but paranoia
    ZOOM_LEVELS.append(ZOOM_LEVELS[-1] * 1.5)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--outfile_csv', required=True)
    parser.add_argument('--overwrite', required=False, action='store_true')
    parser.add_argument('--results_dir',
                        default=os.path.join("..", "processed_data"))
    parser.add_argument('--qualtrics_csv', default="qualtrics.csv",
                        help="qualtrics filename, relative to results_dir")
    parser.add_argument('--grades_csv', default="all_grades.csv",
                        help="grades filename, relative to results_dir")

    args = parser.parse_args()

    # validate the arguments
    if os.path.isfile(args.outfile_csv) and not args.overwrite:
        print("ERROR: output file exists: \"", args.outfile_csv, "\". To "
              "overwrite, use --overwrite", file=sys.stderr, sep="")
        sys.exit(1)

    if not os.path.isdir(args.results_dir):
        print("ERROR: results directory does not exist: \"", args.results_dir,
              "\"", file=sys.stderr, sep="")
        sys.exit(1)

    qualtrics_csv = os.path.join(args.results_dir, args.qualtrics_csv)
    if not os.path.isfile(qualtrics_csv):
        print("ERROR: qualtrics CSV file does not exist: \"", qualtrics_csv,
              "\"", file=sys.stderr, sep="")
        sys.exit(1)

    grades_csv = os.path.join(args.results_dir, args.grades_csv)
    if not os.path.isfile(grades_csv):
        print("ERROR: grades CSV file does not exist: \"", grades_csv, "\"",
              file=sys.stderr, sep="")
        sys.exit(1)

    ## start the processing ##

    # hashmap of [int]parcitipant_id -> hashmap { "group": [str]expert_group,
    #                                             "age": [int]age,
    #                                             "experience: [int]experience,
    #                                             "images": hashmap {...} }
    expert_data = {}
    with open(qualtrics_csv, 'r') as csvfile:
        # This file has three header rows. We use the first as the column names
        # and ignore the other two.
        header_row = next(csvfile).split(",")
        next(csvfile)
        next(csvfile)

        reader = csv.DictReader(csvfile, fieldnames=header_row, delimiter=",")
        for row in reader:
            expert_data[int(row['ID'])] = \
                { KEY_GROUP: row['ExpertGroup'],
                  KEY_AGE: int(row['Age']),
                  KEY_EXPERIENCE: int(row['Years']),
                  KEY_IMAGES: {} }

    # add hashmap of hashmaps: [int]participant_id ->
    #                               [str]image_name ->
    #                                   "dr_grade" -> [int]dr_grade,
    #                                   "dmo_grade" -> [int]dmo_grade,
    #                                   "dr_score" -> [int]dr_score,
    #                                   "dmo_score" -> [int]dmo_score
    with open(grades_csv, 'r') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=",")
        for row in reader:
            participant_id = int(row['subject_id'])
            image_name = os.path.splitext(row['file'])[0] # remove .bmp
            dr_grade = int(row['dr_graded'])
            dr_score = dr_grade - int(row['dr_actual'])
            dmo_grade = int(row['dmo_graded'])
            dmo_score = dmo_grade - int(row['dmo_actual'])

            # ungradable scores
            if dr_grade == -1:
                dr_score = 100;
            if dmo_grade == -1:
                dmo_score = 100;

            if not participant_id in expert_data:
                print("unknown participant:", participant_id)
                continue

            expert_data[participant_id][KEY_IMAGES][image_name] = \
                { "dr_score": dr_score, "dmo_score": dmo_score,
                  "dr_grade": dr_grade, "dmo_grade": dmo_grade }

    # add to the previous hashmap with "study" = tracking/thinkaloud, and
    # a "zooms" hashmap of [float]zoom -> [int]count
    all_zoom_levels = set()
    for participant_dir in glob.glob(os.path.join(args.results_dir, "*")):
        if not os.path.isdir(participant_dir):
            continue

        participant_id = int(os.path.split(participant_dir)[1])
        for study_dir in glob.glob(os.path.join(participant_dir, "*")):
            if not os.path.isdir(study_dir):
                continue

            # zoom data. This also contains study info.
            study = os.path.split(study_dir)[1]
            for zooms_csv in glob.glob(os.path.join(study_dir, "*.zooms.csv")):
                image_name = os.path.split(zooms_csv)[1].replace(".bmp.zooms.csv", "")

                if image_name not in expert_data[participant_id][KEY_IMAGES]:
                    print("unknown image", image_name, "for participant", participant_id)
                    continue
 
                # hashmap of [float]zoom -> [int]count
                zooms = {}
                with open(zooms_csv, 'r') as csvfile:
                    for row in csvfile.readlines():
                        # because of rounding errors, we can still get duplicates.
                        # match this to the "actual" zoom levels.
                        zoom = min(ZOOM_LEVELS, key=lambda i: abs(i - float(row)))

                        all_zoom_levels.add(zoom)

                        if not zoom in zooms:
                            zooms[zoom] = 0

                        zooms[zoom] += 1

                # add it all to the results hashmap
                expert_data[participant_id][KEY_IMAGES][image_name]["study"] = study
                expert_data[participant_id][KEY_IMAGES][image_name]["zooms"] = zooms

            # extract the total time from the raw data
            for results_txt in glob.glob(os.path.join(study_dir, "*.processed.txt")):
                image_name = os.path.split(results_txt)[1].replace(".bmp.processed.txt", "")

                if image_name not in expert_data[participant_id][KEY_IMAGES]:
                    print("unknown image", image_name, "for participant", participant_id)
                    continue

                elapsed_time = -1
                regex = re.compile(r"^<REC.*TIME=\"(\d*\.\d*)\".* />$")
                with open(results_txt, 'r') as txtfile:
                    lines = txtfile.readlines()
                    start_time = None
                    while start_time is None:
                        if not len(lines):
                            print("no data for image", image_name,
                                  "for participant", participant_id)
                            break

                        match = re.match(regex, lines.pop(0))
                        if match is not None:
                            start_time = float(match.group(1))

                    if start_time is None:
                        continue

                    end_time = None
                    while end_time is None:
                        if not len(lines):
                            # edge case: only one record
                            end_time = start_time
                            break

                        match = re.match(regex, lines.pop(-1))
                        if match is not None:
                            end_time = float(match.group(1))

                    elapsed_time = end_time - start_time

                expert_data[participant_id][KEY_IMAGES][image_name]["time"] = elapsed_time
                        

    # Write it all to a CSV file!
    header_row = ["participant_id", "expert_group", "age", "experience",
                  "image", "study", "dr_score", "dmo_score", "dr_grade",
                  "dmo_grade", "time_sec" ]
    for zoom_level in sorted(all_zoom_levels):
        header_row.append("zoom_" + str(zoom_level))

    output_data = [header_row]
    for participant_id, participant_data in expert_data.items():
        for image, image_data in participant_data[KEY_IMAGES].items():
            row = [
                    participant_id,
                    participant_data[KEY_GROUP],
                    participant_data[KEY_AGE],
                    participant_data[KEY_EXPERIENCE],
                    image,
                    image_data["study"],
                    image_data["dr_score"],
                    image_data["dmo_score"],
                    image_data["dr_grade"],
                    image_data["dmo_grade"],
                    image_data["time"]
                ]

            for zoom_level in all_zoom_levels:
                zoom_count = 0
                if zoom_level in image_data["zooms"]:
                    zoom_count = image_data["zooms"][zoom_level]

                row.append(zoom_count)

            output_data.append(row)

    with open(args.outfile_csv, 'w') as csvfile:
        for row in output_data:
            print(",".join(str(r) for r in row), file=csvfile)

    print(len(output_data), "rows written to", args.outfile_csv)
    print("All done! Have a nice day :)")

# EOF
