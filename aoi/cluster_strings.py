# Take a CSV file of eye movement strings and cluster them using affinity
# propagation.

import csv
import Levenshtein
import numpy as np
import os
from pyymatcher import PyyMatcher
from scipy.stats import mannwhitneyu
from sklearn.cluster import AffinityPropagation
import sys
from textdistance import DamerauLevenshtein, JaroWinkler, MLIPNS, StrCmp95, NeedlemanWunsch, Gotoh, SmithWaterman

UNGRADABLE=-100
NUM_EXAMPLES=-1 # -1 to show all

# The distance algorithm to use
ALL_ALGORITHMS = ("levenshtein", "gestalt", "dameraulevenshtein", "jarowinkler",
                  "mlipns", "strcmp95", "needlemanwunsch", "gotoh", "smithwaterman")
ALGORITHM = "levenshtein"

if ALGORITHM not in ALL_ALGORITHMS:
    raise ValueError("bad algorithm!")

# Affinity propagation configuration
AFF_DAMPING=0.75 # must be >= 0.5
AFF_MAX_ITER=2500
AFF_RAND_SEED=2024

# __line__ macro equivalent
from inspect import currentframe
class LineNo:
    def __str__(self):
        return str(currentframe().f_back.f_lineno)
__line__ = LineNo()

# convert an aoi string to a char unique to that aoi.
# note: expecting aoi to be in strings
def AOIToChar(strings, aoi):
    return chr(ord('a') + strings.index(aoi))

# convert a char back to the aoi it refers to.
# note: expecting char to be a valid reference
def charToAOI(strings, char):
    index = ord(char) - ord('a')
    return strings[index]

def aoiToLabel(aoi):
    if aoi == "macula":
        return 'm'
    elif aoi == "arcade_superior":
        return 's'
    elif aoi == "arcade_inferior":
        return 'i'
    elif aoi == "optic_disc":
        return 'o'

    # unknown AOI - just keep it as-is
    return aoi

# from a CSV file containing a score and string of strings, extract the strings
# and the dwells
# format: [<skipped_cols>,]<score>,<string_length>,<string_1>[:<string_2>[...]],<dwell_1>[:<dwell_2>[...]]
# if include_scores is set, only use scores in that list
# if exclude_scores is set, ignore scores in that list
def dataFromStringsCSV(strings_csv,
                       include_scores=None, exclude_scores=None):
    strings = []
    dwells = []
    image_names = []
    participant_ids = []
    string_lengths = []

    with open(strings_csv, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        next(reader) # ignore header row
        for row in reader:
            if len(row) < 4:
                continue

            # yuck
            image_name = row[0].split("##")[0].split("\\")[-1]
            participant_id = int(row[0].split("##")[1][:4])

            score = float(row[1])
            string_len = int(row[2])

            # ignore scores if on the black list and/or not on the white list
            add_score = True
            if include_scores is not None and score not in include_scores:
                add_score = False
            elif exclude_scores is not None and score in exclude_scores:
                add_score = False

            if add_score:
                strings.append(row[3].split(":"))
                dwells.append([float(d) for d in row[4].split(":")])
                string_lengths.append(string_len)
                image_names.append(image_name)
                participant_ids.append(participant_id)

    return participant_ids, image_names, dwells, strings, string_lengths

def extractClusterExemplars(strings_csv,
                            include_scores=None,
                            exclude_scores=None,
                            algorithm=ALGORITHM,
                            seed=AFF_RAND_SEED):

    _, _, _, strings, _ = dataFromStringsCSV(strings_csv,
                                             include_scores=include_scores,
                                             exclude_scores=exclude_scores)

    if len(strings) == 0:
        print("ERROR: no strings found in CSV file:", strings_csv)
        sys.exit(1)

    # get all of the strings and put them into a unique list
    # doing the set -> list hack to remove duplicates
    all_strings = set()
    for string in strings:
        for aoi in set(string):
            all_strings.add(aoi)
    all_strings = list(all_strings)

    # convert each string of AOIs into a string of characters so we can use
    # numpy for the clustering
    char_strings = []
    for string in strings:
        char_string = ""
        for aoi in string:
            char_string += AOIToChar(all_strings, aoi)
        char_strings.append(char_string)
    char_strings = np.asarray(char_strings)

    # calculate similarities between all strings
    similarities = None

    if algorithm == "gestalt":
        # PyyMatcher uses the Gestalt pattern matching algorithm
        similarities = np.array([[PyyMatcher(s1, s2).ratio() for s1 in char_strings] for s2 in char_strings])
    elif algorithm == "levenshtein":
        similarities = np.array([[Levenshtein.distance(s1, s2) for s1 in char_strings] for s2 in char_strings])
    elif algorithm == "dameraulevenshtein":
        similarities = np.array([[DamerauLevenshtein().distance(s1, s2) for s1 in char_strings] for s2 in char_strings])
    elif algorithm == "jarowinkler":
        similarities = np.array([[JaroWinkler().distance(s1, s2) for s1 in char_strings] for s2 in char_strings])
    elif algorithm == "mlipns":
        similarities = np.array([[MLIPNS().distance(s1, s2) for s1 in char_strings] for s2 in char_strings])
    elif algorithm == "strcmp95":
        similarities = np.array([[StrCmp95().distance(s1, s2) for s1 in char_strings] for s2 in char_strings])
    elif algorithm == "needlemanwunsch":
        similarities = np.array([[NeedlemanWunsch().distance(s1, s2) for s1 in char_strings] for s2 in char_strings])
    elif algorithm == "gotoh":
        similarities = np.array([[Gotoh().distance(s1, s2) for s1 in char_strings] for s2 in char_strings])
    elif algorithm == "smithwaterman":
        similarities = np.array([[SmithWaterman().distance(s1, s2) for s1 in char_strings] for s2 in char_strings])
    else:
        print("ERROR: invalid algorithm:", algorithm, "::", __file__, ":", __line__)
        sys.exit(1)

    exemplars = []
    affprop = AffinityPropagation(max_iter=AFF_MAX_ITER, damping=AFF_DAMPING, random_state=seed).fit(similarities)
    for cluster_id in np.unique(affprop.labels_):
        cluster_indices = affprop.cluster_centers_indices_
        if cluster_id < 0 or cluster_id > len(cluster_indices):
            print("ERROR: invalid cluster id (ignoring):", cluster_id, "::", __file__, ":", __line__)
            continue

        exemplar_char = char_strings[affprop.cluster_centers_indices_[cluster_id]]
        cluster = np.unique(char_strings[np.nonzero(affprop.labels_==cluster_id)])

        # convert back to a list of AOIs
        exemplar = []
        for char in exemplar_char:
            exemplar.append(charToAOI(all_strings, char))

        # and save the results
        exemplars.append((exemplar, len(cluster)))

    exemplars.sort(key=lambda x: x[1], reverse=True)
    return exemplars

if __name__ == '__main__':
    def printUsage():
        print("Usage:", __file__, "<strings_csv>")

    if len(sys.argv) < 2:
        printUsage()
        sys.exit(1)

    strings_csv = sys.argv[1]
    if not os.path.exists(strings_csv):
        print("ERROR: strings_csv does not exist:", strings_csv, file=sys.stderr)
        sys.exit(1)

    # extract the strings
    lengths = {}
    for (label, includes, excludes) in [("Correct", (0,), None),
                                        ("Incorrect", None, (0,UNGRADABLE)),
                                        ("Ungradable", (UNGRADABLE,), None)]:

        print("===", label, "===")
        exemplars = extractClusterExemplars(strings_csv,
                                            include_scores=includes,
                                            exclude_scores=excludes,
                                            algorithm=ALGORITHM,
                                            seed=AFF_RAND_SEED)

        for (string, n) in (exemplars[:NUM_EXAMPLES] if NUM_EXAMPLES != -1 else exemplars):
            print(" ", n, ",", ",".join([aoiToLabel(a) for a in string]), sep="")

        print("")

        lengths[label] = [len(e[0]) for e in exemplars]

    print("=== Comparing string lengths ===")
    print(lengths) 
    print(mannwhitneyu(lengths["Correct"], lengths["Incorrect"]))

    print()
    print("All done. Have a nice day :)")

# EOF
