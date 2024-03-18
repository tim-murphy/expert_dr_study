# create a coloured matrix showing the DR severity grade given to each image
# by each participant

import argparse
import csv
import numpy as np
import os
from matplotlib.colors import ListedColormap
import matplotlib.lines as mlines
import matplotlib.pyplot as plt
from statistics import mean
import sys

NOT_GRADED = -2
UNGRADABLE = -1

# custom colouring for the graph
MATRIX_CMAP_LEN = 6
MATRIX_CMAP = ListedColormap(['#aaaaaaff', '#3a6fb5ff', '#5fa55bff', '#f8d26aff', '#eda76dff', '#d76364ff'])

GRADE_LABELS = ("Ungradable", "No DR", "Mild NPDR", "Moderate NPDR", "Severe NPDR", "Proliferative DR")

# colouring for grade scores
MATRIX_CMAP_SCORE_LEN = 10
MATRIX_CMAP_SCORE = ListedColormap(['white',
                                    'grey',
                                    '#3a6fb5ff',
                                    '#4ca588ff',
                                    '#5fa55bff',
                                    '#abbb62ff',
                                    '#f8d26aff',
                                    '#f2bc6cff',
                                    '#eda76dff',
                                    '#d76364ff'])
SCORE_LABELS = ("Ungradable", "-4", "-3", "-2", "-1", "0", "1", "2", "3", "4")

# colouring for referable / not referable
MATRIX_CMAP_REFER_LEN = 3
MATRIX_CMAP_REFER = ListedColormap(['#aaaaaaff', '#f8d26aff', '#d76364ff'])
REFER_LABELS = ("Ungradable", "Referable", "Not referable")

def refer_grade(grade):
    if grade < 0:
        return grade

    return 0 if grade < 2 else 1

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_png", required=False)
    parser.add_argument("--grades_csv", default=os.path.join("..", "processed_data", "tracking_grades.csv"))
    parser.add_argument("--exclude_ids", type=int, nargs='*', default=[1461, 1854, 1894],
                        help="participant IDs to exclude from the matrix") # optom/ophthal only by default
    parser.add_argument("--output_width_px", default=1000, type=int)
    parser.add_argument("--output_height_px", default=600, type=int)
    parser.add_argument("--dpi", default=100, type=int)
    parser.add_argument("--grade_score", action="store_true")
    parser.add_argument("--referable", action="store_true")
    args = parser.parse_args()

    # validate command line arguments
    if not os.path.isfile(args.grades_csv):
        print("ERROR: grades CSV file does not exist:", args.grades_csv,
              file=sys.stderr)
        sys.exit(1)

    # raw results are stored in this hashmap
    # some duplication of storage here to save on code (read: lazy)
    all_images = {} # dict of sets: [int]grade -> set([str]image)
    all_participants = set() # set of IDs
    grades_raw = {} # dict of [str]image -> (tuple([int]participant -> [int]grade))
    ordering_grades_raw = {} # like above, but used for ordering calculations
    scores_raw = {} # dict of [str]image -> (tuple([int]participant -> [int]score))
    participant_group_1 = {} # dict of [int]participant_id -> [bool]group_1
    all_participants_1 = set() # set of IDs for participants in group 1

    with open(args.grades_csv, 'r') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=",")
        for row in reader:
            participant_id = int(row['subject_id'])
            image = os.path.splitext(row['file'])[0]
            dr_grade = int(row['dr_graded'])
            ordering_grade = dr_grade
            dr_actual = int(row['dr_actual'])

            if participant_id in args.exclude_ids:
                continue

            if not participant_id in participant_group_1:
                participant_group_1[participant_id] = False

            if image == "007-0028-000_1140x848":
                participant_group_1[participant_id] = True
                all_participants_1.add(participant_id)

            # if we are doing refer/not refer, mess with the scores
            if args.referable:
                dr_grade = refer_grade(dr_grade)
                dr_actual = refer_grade(dr_actual)

            # score: positive if too high, negative if too low
            dr_score = (None if dr_grade < 0 else dr_grade - dr_actual)

            if not dr_actual in all_images:
                all_images[dr_actual] = set()

            if not image in grades_raw:
                grades_raw[image] = {}
                ordering_grades_raw[image] = {}

            if not image in scores_raw:
                scores_raw[image] = {}

            all_images[dr_actual].add(image)
            all_participants.add(participant_id)
            grades_raw[image][participant_id] = dr_grade
            scores_raw[image][participant_id] = dr_score
            ordering_grades_raw[image][participant_id] = ordering_grade

    # now construct a matrix with the grades
    # x-axis: participant, y-axis: image (ordered by grade)
    fig, axes = plt.subplots(1, 2)
    fig.suptitle("Grader agreement (severity grade)")
    if args.referable:
        fig.suptitle("Grader agreement (referable)")

    fig.set_size_inches(args.output_width_px / args.dpi,
                        args.output_height_px / args.dpi)

    for group_1 in (True, False):
        participants = all_participants_1
        if not group_1:
            participants = all_participants.difference(all_participants_1)

        # get the average grade for each image, and order the table by that number
        # [str]image -> [float]average_grade
        average_grade = {}

        for (image, part) in ordering_grades_raw.items():
            grades = []
            for (p_id, grade) in part.items():
                if p_id in participants:
                    grades.append(grade)

            # remove ungradables
            grades = [ g for g in grades if not g < 0 ]

            if len(grades):
                average_grade[image] = mean(grades)

        ordered_images = list(dict(sorted(average_grade.items(),
                                   key=lambda i: i[1])).keys())

        num_images = sum([len(i) for i in all_images.values()]) / 2
        matrix = np.zeros((int(num_images), len(participants)), dtype=int)

        i = 0
        for image in ordered_images:
            if args.grade_score:
                # grade scores
                for j, participant_id in enumerate(sorted(participants)):
                    score = -5
                    if participant_id in grades_raw[image]:
                        score = scores_raw[image][participant_id]

                    matrix[i][j] = score

                i += 1
            else:
                # grades
                for j, participant_id in enumerate(sorted(participants)):
                    grade = NOT_GRADED
                    if participant_id in grades_raw[image]:
                        grade = grades_raw[image][participant_id]

                    matrix[i][j] = grade

                i += 1

        # create the plot
        ax = axes[int(not group_1)]
        ax.set_title("Image group " + ("1" if group_1 else "2"))
        ax.invert_yaxis() # pcolormesh has (0,0) in the bottom left

        # colour map
        matrix_cmap = (MATRIX_CMAP_SCORE if args.grade_score else (
                        MATRIX_CMAP_REFER if args.referable else MATRIX_CMAP))
        matrix_cmap_len = (MATRIX_CMAP_SCORE_LEN if args.grade_score else (
                            MATRIX_CMAP_REFER_LEN if args.referable else
                            MATRIX_CMAP_LEN))

        ax.pcolormesh(matrix, edgecolors='black', linewidth=0.5,
                       cmap=matrix_cmap)
        ax.set_aspect("equal")

        # legend - needs to be custom since this is using a cmap
        if not group_1:
            legend_labels = (SCORE_LABELS if args.grade_score else (
                                REFER_LABELS if args.referable else GRADE_LABELS))
            legend_handles = []
            for i, label in enumerate(legend_labels):
                colour = matrix_cmap(i / matrix_cmap_len)
                legend_handles.append(mlines.Line2D([], [], color='#00000000', markersize=12,
                                      markerfacecolor=colour, marker='s', label=label))
            fig.subplots_adjust(right=0.8)
            ax.legend(handles=legend_handles,
                      loc="center left",
                      bbox_to_anchor=(0.80, 0.5),
                      bbox_transform=fig.transFigure)

        ax.axis("off")

    if args.output_png is None:
        plt.show()
    else:
        fname = os.path.splitext(args.output_png)
        plt.savefig(args.output_png, transparent=True, pad_inches=0)

# EOF
