# run stats on our ... stats

import csv
import matplotlib.pyplot as plt
import os
import pandas as pd
import scikit_posthocs as sp
from scipy import stats
import statistics
import sys

from cluster_strings import dataFromStringsCSV, UNGRADABLE

USE_UNGRADABLE = False

# the columns we want to check
STAT_COLS = ("fixation_count", "visits", "total_time_sec")
DWELLS_COL = "dwell_time"
STRING_LENGTH_COL = "fixation_string_length"
ALL_GRADES = range(0, 5)

def do_kruskal(scores):
    no_data = False
    for label, s in scores.items():
        if len(s) == 0:
            print("(no data for ", label, ")", sep="")
            no_data = True

    if no_data:
        print()
        return

    if len(scores) > 2:
        kw = stats.kruskal(*scores.values())
        print(" kruskal wallis =", kw.statistic, ":: pvalue =", kw.pvalue)
        if kw.pvalue < 0.05:
            print(" !!! values are different !!!")
            dunn = sp.posthoc_dunn([*scores.values()], 'bonferroni')
            dunn.columns = scores.keys()
            dunn.index = scores.keys()
            pd.options.display.float_format = '{:,.5f}'.format
            print(dunn)
    else:
        mann = stats.mannwhitneyu(*scores.values())
        print(" Mann-Whitney U test: U = ", mann.statistic,
              ", p = ", mann.pvalue, sep="")
        if mann.pvalue < 0.05:
            print(" !!! values are different !!!")

    print("")

    for score, values in scores.items():
        print("  =", score, "=")
        print("  n =", len(values))
        print("  mean = %.2f" % statistics.mean(values))
        print("  median = %.2f" % statistics.median(values))
        print("  sd = %.2f" % statistics.stdev(values))
        print("  var = %.2f" % statistics.variance(values))
        print("")

if __name__ == '__main__':
    def printUsage():
        print("Usage:", __file__, "[<stats_csv=all_stats.csv> [<strings_csv=all_strings.csv>]]")

    # show usage if argument is --help or -help
    if len(sys.argv) > 1 and sys.argv[1][-5:] == "-help":
        printUsage()
        sys.exit(1)

    stats_csv = "all_stats.csv"
    if len(sys.argv) > 1:
        stats_csv = sys.argv[1]

    strings_csv = "all_strings.csv"
    if len(sys.argv) > 2:
        strings_csv = sys.argv[2]

    if not os.path.exists(stats_csv):
        print("ERROR: stats_csv file does not exist:", stats_csv)
        printUsage()
        sys.exit(1)

    if not os.path.exists(strings_csv):
        print("ERROR: strings_csv file does not exist:", strings_csv)
        printUsage()
        sys.exit(1)

    # dwell statistics
    # image_dwells is a dict of [participant][image][aoi] -> list(dwells)
    image_dwells = {}
    string_lengths = {} # dict of participant -> list(lengths)
    participants, images, dwells, strings, lengths = dataFromStringsCSV(strings_csv)

    for s, string in enumerate(strings):
        p = participants[s]
        i = images[s]
        for a, aoi in enumerate(string):
            # update the image dwell stats
            if not p in image_dwells:
                image_dwells[p] = {}

            if not i in image_dwells[p]:
                image_dwells[p][i] = {}

            if not aoi in image_dwells[p][i]:
                image_dwells[p][i][aoi] = []

            image_dwells[p][i][aoi].append(dwells[s][a])

        # string lengths (not AOI dependent)
        if not p in string_lengths:
            string_lengths[p] = {}

        string_lengths[p][i] = lengths[s]

    # stats preparation
    # our container will look something like:
    #  raw_data[<stat_col>][<score>][aoi] = [1, 1, 3, ...]
    raw_data = {}

    # raw_data_grade[<grade>][<stat_col>][<score (0|1)>][<aoi>] = [1, 2, 1, ...]
    raw_data_grade = {}

    # also analyse as correct/incorrect[/ungradable]
    # correct could be score = 0 or score = 0 or 1
    raw_data_grouped_0 = { }
    raw_data_grouped_01 = { }
    raw_data_grouped_refer = { }

    for g in ALL_GRADES:
        raw_data_grade[g] = { }

    for s in list(STAT_COLS) + [DWELLS_COL, STRING_LENGTH_COL]:
        raw_data[s] = {}
        raw_data_grouped_0[s] = { }
        raw_data_grouped_01[s] = { }
        raw_data_grouped_refer[s] = { }

        for g in ALL_GRADES:
            raw_data_grade[g][s] = { }

    with open(stats_csv, 'r') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',')
        for row in reader:
            for s in STAT_COLS:
                grade = int(row["grade"])
                score = int(row["score"])
                score_refer = int(row["refer_score"])
                aoi = row["name"]
                participant = int(row["subject_id"])
                image = row["image"]

                # raw data
                if not score in raw_data[s]:
                    raw_data[s][score] = {}

                if not aoi in raw_data[s][score]:
                    raw_data[s][score][aoi] = []

                raw_data[s][score][aoi].append(float(row[s]))

                correct = ("Correct" if score == 0 else "Incorrect")
                if not correct in raw_data_grade[grade][s]:
                    raw_data_grade[grade][s][correct] = {}

                if not aoi in raw_data_grade[grade][s][correct]:
                    raw_data_grade[grade][s][correct][aoi] = []

                raw_data_grade[grade][s][correct][aoi].append(float(row[s]))

                # also add the dwell data here
                if not score in raw_data[DWELLS_COL]:
                    raw_data[DWELLS_COL][score] = {}

                if not aoi in raw_data[DWELLS_COL][score]:
                    raw_data[DWELLS_COL][score][aoi] = []

                if not correct in raw_data_grade[grade][DWELLS_COL]:
                    raw_data_grade[grade][DWELLS_COL][correct] = {}

                if not aoi in raw_data_grade[grade][DWELLS_COL][correct]:
                    raw_data_grade[grade][DWELLS_COL][correct][aoi] = []

                if aoi in image_dwells[participant][image]:
                    raw_data[DWELLS_COL][score][aoi] += image_dwells[participant][image][aoi]
                    raw_data_grade[grade][DWELLS_COL][correct][aoi] += image_dwells[participant][image][aoi]

                # and string lengths
                if not score in raw_data[STRING_LENGTH_COL]:
                    raw_data[STRING_LENGTH_COL][score] = []

                raw_data[STRING_LENGTH_COL][score].append(string_lengths[participant][image])

                if not correct in raw_data_grade[grade][STRING_LENGTH_COL]:
                    raw_data_grade[grade][STRING_LENGTH_COL][correct] = []

                raw_data_grade[grade][STRING_LENGTH_COL][correct].append(string_lengths[participant][image])

                # grouped data
                for correct_vals, raw_data_grouped, group_score in (
                    ((0,), raw_data_grouped_0, score),
                    ((0, 1), raw_data_grouped_01, score),
                    ((0,), raw_data_grouped_refer, score_refer)):
                    
                    group = "ungradable"
                    if (group_score in correct_vals):
                        group = "correct"
                    elif (group_score != -100):
                        group = "incorrect"
                    elif (not USE_UNGRADABLE):
                        continue # we are ignoring ungradable values

                    if not group in raw_data_grouped[s]:
                        raw_data_grouped[s][group] = {}

                    if not aoi in raw_data_grouped[s][group]:
                        raw_data_grouped[s][group][aoi] = []

                    raw_data_grouped[s][group][aoi].append(float(row[s]))

                    # and dwells
                    if not group in raw_data_grouped[DWELLS_COL]:
                        raw_data_grouped[DWELLS_COL][group] = {}

                    if not aoi in raw_data_grouped[DWELLS_COL][group]:
                        raw_data_grouped[DWELLS_COL][group][aoi] = []

                    if aoi in image_dwells[participant][image]:
                        raw_data_grouped[DWELLS_COL][group][aoi] += image_dwells[participant][image][aoi]

                    # and string lengths
                    if not group in raw_data_grouped[STRING_LENGTH_COL]:
                        raw_data_grouped[STRING_LENGTH_COL][group] = []

                    raw_data_grouped[STRING_LENGTH_COL][group].append(string_lengths[participant][image])

    # sort the raw data to make it easier to analyse
    for label, scores in raw_data.items():
        raw_data[label] = dict(sorted(scores.items()))

    for dataset_label, dataset in (#("raw data", raw_data),
                                   ("grade 0", raw_data_grade[0]),
                                   ("grade 1", raw_data_grade[1]),
                                   ("grade 2", raw_data_grade[2]),
                                   ("grade 3", raw_data_grade[3]),
                                   ("grade 4", raw_data_grade[4]),
                                   ("correct (0)", raw_data_grouped_0),
                                   ("correct (01)", raw_data_grouped_01),
                                   ("correct (refer)", raw_data_grouped_refer)):
        print("@@", dataset_label, "@@")

        for label, stat_data in dataset.items():
            print("---", dataset_label, "--", label, "---")

            if label == STRING_LENGTH_COL:
                # not split over AOI
                do_kruskal(stat_data)
                
            else:
                # first compare across all AOIs
                all_scores = {}
                for score_label, aois in stat_data.items():
                    for _, score_values in aois.items():
                        if not score_label in all_scores:
                            all_scores[score_label] = []

                        all_scores[score_label] += score_values

                print("**** all values ****")
                do_kruskal(all_scores)

                # next, compare a single AOI across all scores
                aoi_values = {}
                for score_label, aois in stat_data.items():
                    for aoi_label, score_values in aois.items():
                        if not aoi_label in aoi_values:
                            aoi_values[aoi_label] = {}

                        if not score_label in aoi_values[aoi_label]:
                            aoi_values[aoi_label][score_label] = []

                        aoi_values[aoi_label][score_label] += score_values

                for aoi_label, scores in aoi_values.items():
                    print("****", dataset_label, "::", label, "::", aoi_label, "****")
                    try:
                        do_kruskal(scores)
                    except Exception as e:
                        print("(insufficient data: ", e, ")", sep="")
                        print()

    print("All done. Have a nice day :)")

# EOF
