# Given a fixation string CSV file, infer a fixation string.

import csv
from math import sqrt
import matplotlib.pyplot as plt
import networkx as nx
import os
import sys

IGNORED_AOI = ['other']
AOI_SEPARATOR = "#"
PLOT_RESOLUTION=(1920,1080)
PLOT_DPI=100
PLOT_DIMS_INCHES=(PLOT_RESOLUTION[0] / PLOT_DPI,
                  PLOT_RESOLUTION[1] / PLOT_DPI)
PLOT_NODE_COLOURS={'macula_nasal': "red",
                   'macula_temporal': "yellow",
                   'optic_disc': "blue",
                   'arcade_superior': "green",
                   'arcade_inferior': "purple"}

# note: we assume grades_csv is an existing csv file with (at least) these
#       columns:
#         - subject_id
#         - file
#         - dr_graded
#         - dr_actual
#       we also assume fixation_string_csv is a file name in this format:
#         .../<image_without_extension>/<subject_id>/*.csv
#         e.g. ./results/tracking/007-0028-000_1140x848/1214/1214_fixation_string.csv
# returns None if no score could be found, or the image was deemed ungradable
def get_score(fixation_string_csv, grades_csv, refer=False):
    # pull out the relevant information from the file path
    path_hier = os.path.normpath(fixation_string_csv).split(os.path.sep)
    image_bmp = path_hier[-3] + ".bmp"
    subject_id = path_hier[-2]

    score = None
    grade = None

    # we can now look for the results in the file
    with open(grades_csv, 'r') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=",")
        for row in reader:
            if subject_id == row['subject_id'] and image_bmp == row['file']:
                # normal grading
                grade = int(row['dr_actual'])
                score = int(row['dr_graded']) - grade

                # special case: ungradable
                if int(row['dr_graded']) == -1:
                    score = None
                elif refer:
                    # referable
                    refer_graded = (1 if int(row['dr_graded']) >= 2 else 0)
                    refer_actual = (1 if int(row['dr_actual']) >= 2 else 0)
                    score = refer_graded - refer_actual
                    grade = refer_actual

                break

    return score, grade

# note: we assume fixation_string_csv is a path to an existing csv file
#       containing (at least) these columns:
#         - fixation_id
#         - aoi
def create_fixation_string(fixation_string_csv, output_graph_png=None):
    # intermediate step: unfiltered fixation data
    fixation_string_raw = []
    dwells_raw = []
    string_length = 0

    # get all of the AOIs for this ID, and add it to fixation_string_raw
    # if it's different from the previous one
    with open(fixation_string_csv, 'r') as csvfile:
        reader = csv.DictReader(csvfile)

        this_id = None
        last_aoi = []
        this_aoi = []
        this_dwell = 0

        last_pos = None # used to calculate string length
        for row in reader:
            fixation_id = row['fixation_id']
            aoi = row['aoi']
            duration = float(row['duration_sec'])
            pos = (int(row['x_pos_px']), int(row['y_pos_px']))

            if (this_id is not None) and (fixation_id != this_id):
                # add to the string length
                if last_pos is not None:
                    # ye olde Pythagoras
                    saccade_length = sqrt(pow(pos[0] - last_pos[0], 2) + \
                                          pow(pos[1] - last_pos[1], 2))
                    string_length += saccade_length

                last_pos = pos

                this_aoi.sort()
                if last_aoi != this_aoi and len(this_aoi):
                    fixation_string_raw.append(this_aoi)
                    dwells_raw.append(this_dwell)

                last_aoi = this_aoi
                this_aoi = []
                this_dwell = 0

            this_id = fixation_id
            if aoi not in IGNORED_AOI:
                this_aoi.append(aoi)
                this_dwell += duration

        # don't forget the last element
        if len(this_aoi):
            fixation_string_raw.append(this_aoi)
            dwells_raw.append(this_dwell)

    # next, convert the raw strings into a DAG
    # to do this, we use each AOI at each fixation as a node, with connection
    # weights set to 1 if the AOIs are different, or 0 if they are the same.
    dag = nx.DiGraph()
    colour_map = []
    parent = None

    # for layout purposes, what is the largest fixation group?
    max_group = max([len(l) for l in fixation_string_raw])

    for level, fixation in enumerate(fixation_string_raw):
        # add the node positions first
        for col, f_node in enumerate(fixation):
            x_pos = ((float(max_group) - 1) / float(len(fixation) + 1)) * (col + 1)
            dag.add_node(f_node + AOI_SEPARATOR + str(level),
                         pos=(level, x_pos))

            # colours yay
            colour = ("grey" if f_node not in PLOT_NODE_COLOURS else PLOT_NODE_COLOURS[f_node])
            colour_map.append(colour)

        if parent is not None:
            for p_node in parent:
                for f_node in fixation:
                    weight = (1 if p_node != f_node else 0)
                    p_label = p_node + AOI_SEPARATOR + str(level - 1)
                    f_label = f_node + AOI_SEPARATOR + str(level)

                    dag.add_edge(p_label, f_label, weight=weight)

        parent = fixation

    if output_graph_png is not None:
        fig = plt.figure(0, figsize=PLOT_DIMS_INCHES, dpi=PLOT_DPI)
        pos = nx.get_node_attributes(dag, "pos")
        nx.draw_networkx(dag, pos=pos, node_color=colour_map, with_labels=False)
        nx.draw_networkx_edge_labels(dag, pos, nx.get_edge_attributes(dag, "weight"))
        plt.tight_layout()
        plt.savefig(output_graph_png)

    # We now need to find the shortest path(s) from any first AOIs to any final
    # AOIs. This means comparing all options and taking the best.
    shortest_paths = []
    shortest_path_cost = None

    last_aoi_index = len(fixation_string_raw) - 1
    for start_aoi in fixation_string_raw[0]:
        for finish_aoi in fixation_string_raw[last_aoi_index]:
            start_label = start_aoi + AOI_SEPARATOR + "0"
            finish_label = finish_aoi + AOI_SEPARATOR + str(last_aoi_index)

            # note: if there are multiple best paths, this will only return one.
            cost, path = nx.bidirectional_dijkstra(dag, start_label, finish_label, weight="weight")

            if shortest_path_cost is None or cost < shortest_path_cost:
                shortest_paths = [path]
                shortest_path_cost = cost
            elif cost == shortest_path_cost:
                shortest_paths.append(path)

    # Now that we have the paths, clean them up to make them readable
    fixation_strings = [] # array of tuples: (string, dwells)
    unique_strings = set()
    
    for path in shortest_paths:
        p = []
        dwells = []

        for i, aoi in enumerate(path):
            aoi_clean = aoi[:aoi.find(AOI_SEPARATOR)]

            if not len(p):
                p = [aoi_clean]
                dwells = [dwells_raw[i]]
            elif aoi_clean != p[-1]:
                p.append(aoi_clean)
                dwells.append(dwells_raw[i])
            else:
                dwells[-1] += dwells_raw[i]

        if tuple(p) not in unique_strings:
            unique_strings.add(tuple(p))
            fixation_strings.append((p, dwells))

    return int(string_length), fixation_strings

if __name__ == '__main__':
    def printUsage():
        print("Usage:", __file__, "<fixation_string_csv> <grades_csv> <output_csv> [<output_graph_png>]")
        print("Note: results will be appended to output_csv if it already exists")

    if len(sys.argv) < 4:
        printUsage()
        sys.exit(1)

    fixation_string_csv = sys.argv[1]
    grades_csv = sys.argv[2]
    output_csv = sys.argv[3]
    output_graph_png = None

    if len(sys.argv) > 4:
        output_graph_png = sys.argv[4]

    if not os.path.exists(fixation_string_csv):
        print("ERROR: fixation_string_csv does not exist:", fixation_string_csv)
        sys.exit(1)

    if not os.path.exists(grades_csv):
        print("ERROR: grades_csv does not exist:", grades_csv)
        sys.exit(1)

    # First, calculate the score for this record, from the grades_csv file.
    # This is a delta, with 0 meaning correct, +1 meaning graded too severely,
    # and -1 meaning graded too mildly.
    score, _ = get_score(fixation_string_csv, grades_csv)
    if score is None:
        # big penalty for not grading, or if not found, so that we don't use it
        score = -100                    

    # get the fixation strings...
    string_length, fixation_strings = create_fixation_string(fixation_string_csv, output_graph_png)

    # ...and write them to the output file
    if not os.path.exists(output_csv):
        # header for new files
        with open(output_csv, 'w') as ofile:
            print("subject,score,string_len,string,dwells", file=ofile)

    with open(output_csv, 'a') as ofile:
        for f, d in fixation_strings:
            print(os.path.split(fixation_string_csv)[1], score, string_length,
                  ":".join(f), ":".join(str(dwell) for dwell in d),
                  sep=",", file=ofile)

# EOF
