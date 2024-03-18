# Stats that can't be done with Excel (anything more complicated than mean).

import argparse
import csv
import krippendorff
from math import isnan
import matplotlib.pyplot as plt
import numpy as np
import os
from scipy.stats import bootstrap, kstest, mannwhitneyu, norm, shapiro, linregress
from statistics import mean, stdev
import sys

# yuck
sys.path.append(os.path.join("..", "aoi"))
from stats import do_kruskal

UNGRADABLE = 100
THINKALOUD = "thinkaloud"
TRACKING = "tracking"
ALL_DATA = "all"
CORRECT = "correct"
INCORRECT = "incorrect"

STUDIES = (TRACKING)
EXPERTS = ("Optometrist", "Ophthalmologist")

MAX_ZOOM = 5.0

def run_krippendorff(matrix, domain=range(-1,5)):
    # convert our matrix to show value counts (number of graders giving each
    # score, which avoids needing NaN)
    # this gives the same results as just using matrix, but is easier to check
    # for issues, and doesn't throw for some bad data instances
    vc = np.zeros((len(matrix[0]), len(domain)), dtype=int)

    for i in range(len(matrix)):
        for j in range(len(matrix[0])):
            grade = matrix[i][j]

            if isnan(grade):
                continue

            # Will throw if the grade isn't in the list. If that happens, we've
            # done something wrong so we don't want to catch it.
            grade_index = domain.index(grade)

            vc[j][grade_index] += 1

    alpha = krippendorff.alpha(value_counts=vc, level_of_measurement="ordinal")
    # alpha = krippendorff.alpha(reliability_data=matrix, level_of_measurement="ordinal")

    return alpha

def run_mannwhitney(label_1, scores_1, label_2, scores_2):
    mann = mannwhitneyu(scores_1, scores_2)
    print("Mann-Whitney U test: U = ", mann.statistic,
          ", p = ", mann.pvalue, sep="")

    for (label, vals) in ((label_1, scores_1),
                          (label_2, scores_2)):
        print(label, "::",
              "n =", len(vals),
              "mean =", mean(vals),
              "stdev =", stdev(vals))

    if mann.pvalue < 0.05:
        print()
        print("####################################### significant #######################################")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw_results_csv', default="raw_results.csv",
                        help="CSV file created by extract_data.py")

    args = parser.parse_args()

    # validate the command line arguments
    if not os.path.isfile(args.raw_results_csv):
        print("ERROR: raw results CSV file does not exist: \"",
              raw_results_csv, "\". Did you forget to run extract_data.py?",
              file=sys.stderr, sep="")
        sys.exit(1)

    ## start the processing ##

    # Extract the data as a bunch of hashmaps.
    # Note that there is data duplication here to make the code easier to write
    # and understand.
    # scores: [str]expert_group -> [dict] {
    #           "thinkaloud":   { [dict]{[int]grade -> [list[int]]scores },
    #           "tracking":     { as above },
    #           "all":          { as above }}
    # scores_refer is the same as scores but with 0=not referable, 1=referable
    # correct hashmaps use the same structure as above but 1 for correct and
    #   0 for incorrect.
    scores = { ALL_DATA: { THINKALOUD: { ALL_DATA: [] },
                           TRACKING: { ALL_DATA: [] },
                           ALL_DATA: { ALL_DATA: [] } } }
    scores_refer = { ALL_DATA: { THINKALOUD: { ALL_DATA: [] },
                                 TRACKING: { ALL_DATA: [] },
                                 ALL_DATA: { ALL_DATA: [] } } }
    correct_0 = { ALL_DATA: { THINKALOUD: { ALL_DATA: [] },
                              TRACKING: { ALL_DATA: [] },
                              ALL_DATA: { ALL_DATA: [] } } }
    correct_01 = { ALL_DATA: { THINKALOUD: { ALL_DATA: [] },
                               TRACKING: { ALL_DATA: [] },
                               ALL_DATA: { ALL_DATA: [] } } }
    correct_refer = { ALL_DATA: { THINKALOUD: { ALL_DATA: [] },
                                  TRACKING: { ALL_DATA: [] },
                                  ALL_DATA: { ALL_DATA: [] } } }

    # zoom stats
    # zooms_0 = [int]participant_id -> [dict] {
    #             "correct"/"incorrect" ->
    #                   list(tuple([float]zoom_level, [float]fraction)) }
    # same for zooms_01 and zooms_refer
    zooms_0 = { }
    zooms_01 = { }
    zooms_refer = { }

    # zooms per grade: [int]grade ->
    #                       [dict]{[float]zoom_level ->
    #                           [dict]{CORRECT: []
    #                                  INCORRECT: []}}
    zooms_per_grade = {}

    # other data
    # expert_group: [int]participant_id -> [str]expert_group
    # participant_grades: [int]participant_id ->
    #                           [dict]{ [str]image -> [int]grade }
    expert_group = {}
    participant_grades = {}
    participant_grades_refer = {}

    # laziness
    all_groups = set({ALL_DATA})
    all_scores = set({ALL_DATA})
    all_scores_refer = set({ALL_DATA})
    all_studies = set({ALL_DATA})
    all_participants = set()
    all_images = { ALL_DATA: set() }
    all_zooms = set()
    all_grades = list(range(0, 5)) + [ALL_DATA]

    # for age/experience and accuracy scatterplot
    # dict of participant_id -> (age, experience, list(correct=1, incorrect=0))
    scatter_data = {}

    with open(args.raw_results_csv, 'r') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=",")
        for row in reader:
            participant_id = int(row['participant_id'])
            image = row['image']
            study = row['study']
            group = row['expert_group']
            age = int(row['age'])
            experience = int(row['experience'])

            if study not in STUDIES:
                continue

            if group not in EXPERTS:
                continue

            all_participants.add(participant_id)
            all_images[ALL_DATA].add(image)

            # paranoia
            if study not in (THINKALOUD, TRACKING):
                print("ERROR: invalid study:", study, file=sys.stderr)
                continue

            all_groups.add(group)
            all_studies.add(study)

            # expert group
            expert_group[participant_id] = group

            # dr grading
            dr_score = int(row['dr_score'])
            dr_grade = int(row['dr_grade'])
            dr_actual = (dr_score if dr_score == UNGRADABLE else (dr_grade - dr_score))

            all_scores.add(dr_score)

            if not dr_actual in all_images:
                all_images[dr_actual] = set()

            all_images[dr_actual].add(image)

            # scatterplot data
            if not participant_id in scatter_data:
                scatter_data[participant_id] = { "age": age,
                                                 "experience": experience,
                                                 "results": [] }
            scatter_data[participant_id]["results"].append(1 if dr_score == 0 else 0)

            # add our data to the big data stores
            if not participant_id in participant_grades:
                participant_grades[participant_id] = {}

            participant_grades[participant_id][image] = \
                (np.nan if dr_grade not in range(0,5) else dr_grade)

            if not group in scores:
                scores[group] = { THINKALOUD: { ALL_DATA: [] },
                                  TRACKING: { ALL_DATA: [] },
                                  ALL_DATA: { ALL_DATA: [] } }
                correct_0[group] = { THINKALOUD: { ALL_DATA: [] },
                                     TRACKING: { ALL_DATA: [] },
                                     ALL_DATA: { ALL_DATA: [] } }
                correct_01[group] = { THINKALOUD: { ALL_DATA: [] },
                                      TRACKING: { ALL_DATA: [] },
                                      ALL_DATA: { ALL_DATA: [] } }

            for e in (group, ALL_DATA):
                for s in (study, ALL_DATA):
                    if s not in scores[e]:
                        scores[e][s] = {}
                        correct_0[e][s] = {}
                        correct_01[e][s] = {}

                    for g in (dr_actual, ALL_DATA):
                        if not g in scores[e][s]:
                            scores[e][s][g] = []
                            correct_0[e][s][g] = []
                            correct_01[e][s][g] = []

                        if dr_score != UNGRADABLE:
                            scores[e][s][g].append(dr_score)

                        correct_0[e][s][g].append(1 if dr_score == 0 else 0)
                        correct_01[e][s][g].append(1 if dr_score in (0, 1) else 0)

            # zooms
            if not participant_id in zooms_0:
                zooms_0[participant_id] = { CORRECT: [], INCORRECT: [] }
                zooms_01[participant_id] = { CORRECT: [], INCORRECT: [] }
                zooms_refer[participant_id] = { CORRECT: [], INCORRECT: [] }

            these_zooms = []
            zooms_count = 0
            max_zoom_count = 0
            for k, v in row.items():
                if k[:5] == "zoom_":
                    zoom_level = float(k[5:])
                    zoom_count = float(v)
                    zooms_count += zoom_count

                    all_zooms.add(zoom_level)

                    if zoom_level > MAX_ZOOM:
                        max_zoom_count += zoom_count
                    else:
                        these_zooms.append((zoom_level, zoom_count))

            these_zooms.append((MAX_ZOOM, max_zoom_count))
            all_zooms.add(MAX_ZOOM)

            # referable grading
            dr_actual_refer = (dr_actual if dr_actual == UNGRADABLE else (
                                0 if dr_actual < 2 else 1))
            dr_grade_refer = (0 if dr_grade == UNGRADABLE else (
                                0 if dr_grade < 2 else 1))
            dr_score_refer = (dr_score if dr_score == UNGRADABLE else (
                                dr_actual_refer - dr_grade_refer))

            all_scores_refer.add(dr_score_refer)

            if not participant_id in participant_grades_refer:
                participant_grades_refer[participant_id] = {}

            participant_grades_refer[participant_id][image] = \
                (np.nan if dr_grade_refer not in (0,1) else dr_grade_refer)

            if not group in scores_refer:
                scores_refer[group] = { THINKALOUD: { ALL_DATA: [] },
                                        TRACKING: { ALL_DATA: [] },
                                        ALL_DATA: { ALL_DATA: [] } }
                correct_refer[group] = { THINKALOUD: { ALL_DATA: [] },
                                         TRACKING: { ALL_DATA: [] },
                                         ALL_DATA: { ALL_DATA: [] } }

            for e in (group, ALL_DATA):
                for s in (study, ALL_DATA):
                    if s not in scores_refer[e]:
                        scores_refer[e][s] = {}
                        correct_refer[e][s] = {}

                    for g in (dr_actual_refer, ALL_DATA):
                        if not g in scores_refer[e][s]:
                            scores_refer[e][s][g] = []
                            correct_refer[e][s][g] = []

                        if dr_score_refer != UNGRADABLE:
                            scores_refer[e][s][g].append(dr_score_refer)

                        correct_refer[e][s][g].append(1 if dr_score_refer == 0
                                                      else 0)

            # now convert the zoom count to a fraction and add it to the dict
            for (zoom_level, zoom_count) in these_zooms:
                zoom_frac = zoom_count / zooms_count

                zooms_0[participant_id] \
                    [(CORRECT if dr_score == 0 else INCORRECT)].append(
                        (zoom_level, zoom_frac))

                zooms_01[participant_id] \
                    [(CORRECT if dr_score in(0, 1) else INCORRECT)].append(
                        (zoom_level, zoom_frac))

                zooms_refer[participant_id] \
                    [(CORRECT if dr_score_refer == 0 else INCORRECT)].append(
                        (zoom_level, zoom_frac))
 
                # all zooms data
                if not dr_grade in zooms_per_grade:
                    zooms_per_grade[dr_grade] = {}

                if not zoom_level in zooms_per_grade[dr_grade]:
                    zooms_per_grade[dr_grade][zoom_level] \
                        = {CORRECT: [], INCORRECT: []}

                zooms_per_grade[dr_grade][zoom_level] \
                    [CORRECT if dr_score == 0 else INCORRECT].append(zoom_frac)

    # zooms!
    for label, zooms in (("Correct (0)", zooms_0),
                         ("Correct (0/1)", zooms_01),
                         ("Referable", zooms_refer)):
        # dict of "correct"/"incorrect" -> [dict] {
        #       [float]zoom_level -> list([float]fraction of time) }
        zoom_fractions = { CORRECT: { ALL_DATA: [] },
                           INCORRECT: { ALL_DATA: [] } }

        for zoom_level in all_zooms:
            zoom_fractions[CORRECT][zoom_level] = []
            zoom_fractions[INCORRECT][zoom_level] = []

        # zooms_0 = [int]participant_id -> [dict] {
        #             "correct"/"incorrect" ->
        #                   list(tuple([float]zoom_level, [float]fraction)) }
        for _, zoom_groups in zooms.items():
            for correct_label, zoom_details in zoom_groups.items():
                for (zoom_level, zoom_frac) in zoom_details:
                    zoom_fractions[correct_label][zoom_level].append(zoom_frac)
                    zoom_fractions[correct_label][ALL_DATA].append(zoom_frac)

        for zoom_level in all_zooms:
            print("&&& zoom", label, "&&", zoom_level, "&&&")
            do_kruskal({CORRECT: zoom_fractions[CORRECT][zoom_level],
                        INCORRECT: zoom_fractions[INCORRECT][zoom_level]})

    # now do zoom stats for each grade
    for g in all_grades:
        if not g in zooms_per_grade:
            continue

        for z in all_zooms:
            if not z in zooms_per_grade[g]:
                continue

            print("%%% zoom", z, "%%% grade", g, "%%%")

            do_kruskal(zooms_per_grade[g][z])

    # grade matrix, with graders as rows and images as columns.
    grade_matrices = {}
    refer_matrices = {}
    for g in all_grades:
        grade_matrices[g] = np.ndarray((len(all_participants), len(all_images[g])),
                                  dtype=float)
        refer_matrices[g]= np.ndarray((len(all_participants), len(all_images[g])),
                                  dtype=float)

    # this is a very inefficient way to do this, but whatever.
    for g in all_grades:
        for j, image in enumerate(all_images[g]):
            for i, participant in enumerate(all_participants):
                # grade matrix
                grade = np.nan # exclude those not graded
                if image in participant_grades[participant]:
                    grade = participant_grades[participant][image]

                # keep things ordinal (-1) or ignore ungradable (np.nan)
                if grade == UNGRADABLE:
                    grade = np.nan

                grade_matrices[g][i][j] = grade

                # refer matrix
                refer = np.nan
                if image in participant_grades_refer[participant]:
                    refer = participant_grades_refer[participant][image]

                if refer == UNGRADABLE:
                    refer = np.nan

                refer_matrices[g][i][j] = refer

    for g in all_grades:
        print("&&& Grade", g, "&&&")

        if g == ALL_DATA:
            print("Inter-grader agreement (grades)")
            print("Krippendorff:", run_krippendorff(grade_matrices[g]))

            print("Inter-grader agreement (refer)")
            print("Krippendorff:", run_krippendorff(refer_matrices[g], domain=range(-1,2)))
        else:
            # figure out how many graders had this value
            print("Inter-grader agreement (grades)")
            print(round(np.count_nonzero(grade_matrices[g] == float(g)) /
                        np.count_nonzero(~np.isnan(grade_matrices[g])) * 100, 2),
                  "%", sep="")

            print("Inter-grader agreement (refer)")
            refer_grade = (0 if g < 2 else 1)
            print(round(np.count_nonzero(refer_matrices[g] == float(refer_grade)) /
                        np.count_nonzero(~np.isnan(refer_matrices[g])) * 100, 2),
                  "%", sep="")

        print()

    """ FIXME do bootstrapping here
    # grade_matrix_flat = list(grade_matrix.flatten())
    grade_matrix_flat = grade_matrix # FIXME .tolist().copy()
    print(run_krippendorff(grade_matrix_flat))
    ci = bootstrap((grade_matrix_flat,), run_krippendorff, confidence_level=0.95,
                   random_state=2024, n_resamples=10, axis=0, vectorized=False,
                   method="percentile", alternative="two-sided").confidence_interval
    print(ci)
    sys.exit()
    """

    # now do some stats with these data
    for (grading_label, grading_data) in (# ("Grade score", scores),
                                          # ("Referable score", scores_refer),
                                          ("Correct (0)", correct_0),
                                          ("Correct (0/1)", correct_01),
                                          ("Correct (refer)", correct_refer)):
        print("!!!!! --", grading_label, "-- !!!!!")
        print()

        for study in all_studies:
            print("**", grading_label, "::", study, "**")
            print()

            for e1, expert_1 in enumerate(all_groups):
                for e2, expert_2 in enumerate(all_groups):
                    # don't compare things twice
                    if e2 <= e1:
                        continue

                    print("==", expert_1, "vs", expert_2, "==")

                    for grade in all_grades:
                        print("$$", grade, "$$")

                        if grade not in grading_data[expert_1][study]:
                            print(" <no data for ", expert_1, ">", sep="")
                        elif grade not in grading_data[expert_2][study]:
                            print(" <no data for ", expert_2, ">", sep="")
                        else:
                            scores_1 = grading_data[expert_1][study][grade]
                            scores_2 = grading_data[expert_2][study][grade]

                            run_mannwhitney(expert_1, scores_1,
                                            expert_2, scores_2)

                        print()

            print("** ** **")
            print()

        for expert in all_groups:
            print("@@", grading_label, "::", expert, "@@")

            for s1, study_1 in enumerate(all_studies):
                for s2, study_2 in enumerate(all_studies):
                    # don't compare things twice
                    if s2 <= s1:
                        continue

                    print("==", study_1, "vs", study_2, "==")
                    scores_1 = grading_data[expert][study_1][ALL_DATA]
                    scores_2 = grading_data[expert][study_2][ALL_DATA]

                    run_mannwhitney(study_1, scores_1,
                                    study_2, scores_2)

                    print()

            print("@@ @@ @@")
            print()

    # scores normal distribution
    scores_raw = []
    for s in scores[ALL_DATA][ALL_DATA][ALL_DATA]:
        if s != UNGRADABLE:
            scores_raw.append(s)

    print("Grade scores normal distribution (excluding ungradable)")
    sha = shapiro(scores_raw)
    print("Shapiro-Wilk test: W = ", sha.statistic, ", p = ", sha.pvalue, sep="")

    print()

    # plot the scatter data
    ages = []
    experiences = []
    accuracies = []
    for participant_id, participant_data in scatter_data.items():
        ages.append(participant_data["age"])
        experiences.append(participant_data["experience"])
        accuracies.append(mean(participant_data["results"]))

    for label, xdat, colour, marker in (("Age", ages, 'b', 'o'),
                                        ("Experience", experiences, 'r', '+')):
        regr = linregress(xdat, accuracies)
        r2 = regr.rvalue ** 2

        # plot points
        plt.plot(xdat, accuracies, colour + marker, label=(label + " ($R^2$ = %.6f)" % r2))

        # add regression line
        print(regr)
        x = np.linspace(min(xdat), max(xdat), 2)
        plt.plot(x, regr.intercept + (regr.slope * x), colour)

    plt.title("Accuracy per age and experience")
    plt.xlabel("Age/experience (years)")
    plt.ylabel("Accuracy")
    plt.legend(loc="lower right")
    plt.ylim(0.0, 1.0)

    plt.show()

# EOF
