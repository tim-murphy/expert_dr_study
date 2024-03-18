from hmmlearn import hmm

import contextlib
import csv
import cv2
from enum import Enum
from matplotlib.cm import get_cmap
import matplotlib.pyplot as plt
import numpy as np
import os
import shutil
import sys

from gazepoint_utils import fraction_to_pixel
from image_overlay import image_overlay

# constants
MAX_ITERATIONS = 10
OUTPUT_RESOLUTION_PX = (1140, 848)
K_MAX_LIST = (4, 5)
COLOURMAP = get_cmap("Set1")

# how we score each model
class ModelScoring(Enum):
    LIKELIHOOD_RATIO = 1
    AIC = 2
    BIC = 3

# common paths (should always exist)
PROCESSED_DATA_DIR = os.path.join("..", "processed_data")
IMAGE_DIR = os.path.join("..", "images")
RESULTS_DIR = "results"
for path in [PROCESSED_DATA_DIR, IMAGE_DIR, RESULTS_DIR]:
    if not os.path.exists(path):
        raise ValueError("common path does not exist: " + path)

# HMM config
HMM_SCORING = ModelScoring.BIC
HMM_ITERATIONS = 1000
HMM_COVARIANCE = "diag"
HMM_ALGORITHM = "viterbi"
HMM_SEED = 2023

# gaze position circle
POS_RADIUS = 10
POS_THICKNESS = 2

# label attributes
ADD_LABELS = True
BACKGROUND_MAX_GREY = 0x10 # considered background when converted to grey
CORRECT_COLOUR = (0x04, 0x3A, 0x03) # BGR
WRONG_COLOUR = (0x03, 0x04, 0x3A) # BGR
LABEL_FONT = cv2.FONT_HERSHEY_DUPLEX
LABEL_SCALE = 2.0
LABEL_COLOUR = (255, 255, 255)
LABEL_LINEWIDTH = 2 * int(LABEL_SCALE)
LABEL_X_PAD = 5
LABEL_Y_PAD = 5 + (25 * int(LABEL_SCALE))
LABEL_Y_SPACING = 40 * int(LABEL_SCALE)

# return True if the new score is better than the old score
def scoreBetter(old, new, scoreType=HMM_SCORING):
    if scoreType in [ModelScoring.LIKELIHOOD_RATIO]:
        return new > old
    elif scoreType in [ModelScoring.AIC, ModelScoring.BIC]:
        return new < old
    else:
        raise ValueError("Unknown model type: " + str(modelType))

def scoreModel(model, observations, scoreType=HMM_SCORING):
    if scoreType == ModelScoring.LIKELIHOOD_RATIO:
        return model.score(observations)
    elif scoreType == ModelScoring.AIC:
        return model.aic(observations)
    elif scoreType == ModelScoring.BIC:
        return model.bic(observations)

    raise ValueError("Unknown model type: " + str(modelType))

# returns a GaussianHMM model instance
def categorise_observations(observations, k_max):
    # Because fit tends to land in a local maxima, try to fit it a bunch of
    # times and take the best one.
    best_model = None
    best_score = None

    for i in range(MAX_ITERATIONS):
        model = hmm.GaussianHMM(n_components=k_max,
                                n_iter=HMM_ITERATIONS,
                                covariance_type=HMM_COVARIANCE,
                                algorithm=HMM_ALGORITHM,
                                random_state=HMM_SEED)

        # because we're using raw gaze data (and not fixations), we are much
        # more likely to transition to the same state (i.e. identity matrix)
        model.transmat_ = np.identity(k_max, dtype=float)

        # assume we are equally as likely to start in any of the states
        model.startprob_ = [1/k_max] * k_max

        # hackety hack: hide "model not converging" errors
        # yes I know that means the data don't fit the model very well :(
        with open(os.devnull, 'w') as devnull:
            with contextlib.redirect_stderr(devnull):
                model.fit(observations)

        # score using Bayesian Information Theory so we can directly compare
        # models with different k_max values
        score = scoreModel(model, observations)

        if best_model is None or scoreBetter(best_score, score):
            best_model = model
            best_score = score

    return best_score, best_model

def plot_observations(observations, categories, transition_matrix, outfile_png):
    def get_colour(category):
        num_colours = len(COLOURMAP.colors)
        if category >= num_colours:
            print("WARN: more categories than colours (will have duplicates)")

        # take our next colour (in float BGR format) and convert it to int RGBA
        colour = list(COLOURMAP.colors[category % num_colours])
        float_to_int = lambda b, g, r : (int(round(r * 255.0)),
                                         int(round(g * 255.0)),
                                         int(round(b * 255.0)),
                                         255) # add the alpha channel
        return float_to_int(*colour)

    if len(observations) != len(categories):
        raise ValueError("The number of observations (" + str(len(observations))
                         + ") does not match the number of categories ("
                         + str(len(categories)) + ")")

    # the 4 is the number of channels (RGBA)
    canvas = np.zeros((*reversed(OUTPUT_RESOLUTION_PX), 4), np.uint8)

    for i, coords_frac in enumerate(observations):
        # convert the fractional coordinates into pixels
        (x_px, y_px) = fraction_to_pixel(*coords_frac, *OUTPUT_RESOLUTION_PX)

        if (x_px > OUTPUT_RESOLUTION_PX[0] or x_px < 0 or
            y_px > OUTPUT_RESOLUTION_PX[1] or y_px < 0):

            # data points are out of bounds
            continue

        plot_colour = get_colour(categories[i])

        # add the position to the canvas
        cv2.circle(canvas, (x_px, y_px), POS_RADIUS, plot_colour, POS_THICKNESS)

    # write overlay to file
    cv2.imwrite(outfile_png, canvas)
    print("Overlay written to:", outfile_png)

    # write the transition matrix to file
    outfile_matrix_csv = (outfile_png[:-3]) + "matrix.csv"
    with open(outfile_matrix_csv, 'w') as ofile:
        for line in transition_matrix:
            print(*line, sep=",", file=ofile)

    print("Transition matrix written to:", outfile_matrix_csv)

if __name__ == '__main__':
    def printUsage():
        print("Usage:", __file__, "<participant_id> <img_name_bmp> <study=(tracking|thinkaloud)> <outfile_png>")
        print("       e.g.:", __file__, "1234 007-0028-000_1148x848.bmp tracking new_image.png")

    if len(sys.argv) < 5:
        printUsage()
        sys.exit(1)

    # parse and check command line args
    participant_id = sys.argv[1]
    img_name_bmp = sys.argv[2]
    study = sys.argv[3]
    outfile_png = sys.argv[4]

    if study not in ("tracking", "thinkaloud"):
        raise ValueError("Invalid study (must be 'tracking' or 'thinkaloud')")

    raw_coords_csv = os.path.join(RESULTS_DIR, study,
                                  img_name_bmp[:-4], # strip the extension
                                  participant_id,
                                  participant_id + "_raw_coords.csv")
    orig_img_bmp = os.path.join(IMAGE_DIR, img_name_bmp)
    qualtrics_csv = os.path.join(PROCESSED_DATA_DIR, "qualtrics.csv")
    grades_csv = os.path.join(PROCESSED_DATA_DIR, study + "_grades.csv")

    for (var, name) in [(raw_coords_csv, "raw_coords_csv"),
                        (orig_img_bmp, "orig_img_bmp"),
                        (qualtrics_csv, "qualtrics_csv"),
                        (grades_csv, "grades_csv")]:
        if not os.path.exists(var):
            raise ValueError(name + " does not exist: " + var)

    # pull out the coordinates from the file
    observations = []
    with open(raw_coords_csv, 'r') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=",")

        for line in reader:
            observations.append((float(line['x_frac']), float(line['y_frac'])))

    # categorise using hidden Markov modeling
    # we will do multiple K_max values
    best_score = None
    best_model = None
    for k_max in K_MAX_LIST:
        print(" === K_max", k_max, "===")

        score, model = categorise_observations(observations, k_max)
        _, categories = model.decode(observations)
        transition_matrix = model.transmat_

        # and plot it
        outfile_kmax = outfile_png[:-3] + str(k_max) + outfile_png[-4:]
        plot_observations(observations, categories, transition_matrix, outfile_kmax)

        # create an overlay while we're here
        outfile_kmax_overlay = outfile_png[:-4] + "_overlay." + str(k_max) + outfile_png[-4:]
        image_overlay(orig_img_bmp, outfile_kmax, outfile_kmax_overlay)
        print()

        if best_model is None or scoreBetter(best_score, score):
            best_score = score
            best_model = model

    # copy the "best" results as a new image
    best_outdir, best_outfile = os.path.split(outfile_png)
    k_max_best = best_model.n_components
    print(" !! best model:", k_max_best, "!!")
    outfile_kmax = outfile_png[:-3] + str(k_max_best) + outfile_png[-4:]
    outfile_kmax_best = best_outfile[:-3] + "best" + best_outfile[-4:]
    shutil.copy2(outfile_kmax, os.path.join(best_outdir, "..", outfile_kmax_best))

    # best overlays, with labels
    outfile_kmax_overlay = outfile_png[:-4] + "_overlay." + str(k_max_best) + outfile_png[-4:]
    outfile_kmax_overlay_best = best_outfile[:-4] + "_overlay.best" + best_outfile[-4:]

    # get the participant details to print on the image
    grade_int = None
    actual_grade = None
    job_str = None
    training_str = None

    label_grade = ""
    label_job = ""
    label_training = []

    # get the occupation and training info
    with open(qualtrics_csv, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['ID'] == participant_id:
                job_str = row['ExpertGroup']
                training_str = (row['Training'])
                break

    if job_str is None or training_str is None:
        raise LookupError("No Qualtrics data for participant: " + participant_id)

    # get the DR severity grade this participant gave for this image
    with open(grades_csv, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['subject_id'] == participant_id and row['file'] == img_name_bmp:
                grade_int = int(row['dr_graded'])
                actual_grade = int(row['dr_actual'])
                break

    if grade_int is None:
        raise LookupError("No grading data for participant: " + participant_id)

    # format the labels to fit on the image
    if grade_int == 0:
        label_grade = "No DR"
    elif grade_int == 1:
        label_grade = "Mild"
    elif grade_int == 2:
        label_grade = "Moderate"
    elif grade_int == 3:
        label_grade = "Severe"
    elif grade_int == 4:
        label_grade = "PDR"
    elif grade_int == -1:
        label_grade = "Ungradable"
    else:
        raise ValueError("Unknown DR severity: " + grade_int)

    if job_str == "Optometrist":
        label_job = "Optom"
    elif job_str == "Ophthalmologist":
        label_job = "Ophthal"
    elif job_str == "DR Screener":
        label_job = "Grader"
    elif job_str == "Ophthalmology Registrar":
        label_job = "Reg"
    else:
        raise ValueError("Unknown profession: " + job_str)

    label_training = (training_str.replace("Vitreoretinal fellowship", "VR")\
                                  .replace("Medical retina fellowship", "MR")\
                                  .replace("Specialty practice with a focus on, or large number of patients with, diabetes", "SP")\
                                  .replace("PhD related to diabetic retinopathy", "PhD")\
                                  .replace("Other training or experience relevant to DR treatment or management (please specify)", "Other"))\
                                  .split(",")

    # finally time to write the image
    best_image = cv2.imread(outfile_kmax_overlay)

    # replace the background colour with red if incorrect, or green if correct
    new_background = (WRONG_COLOUR if grade_int != actual_grade else CORRECT_COLOUR)

    # convert to grayscale to make the processing easier
    img_gray = cv2.cvtColor(best_image, cv2.COLOR_BGR2GRAY)

    # create a binary mask, where pixels which are not BACKGROUND_MAX_GREY
    # are converted to white
    _, mask = cv2.threshold(img_gray, BACKGROUND_MAX_GREY, 255, cv2.THRESH_BINARY)
    background_pixels = np.where(mask == 0)
    best_image[background_pixels[0], background_pixels[1], :] = new_background

    if (ADD_LABELS):
        for line, text in enumerate([label_grade, label_job, *label_training]):
            pos = (LABEL_X_PAD, LABEL_Y_PAD + (line * LABEL_Y_SPACING))
            cv2.putText(best_image, text, pos, LABEL_FONT, LABEL_SCALE,
                        LABEL_COLOUR, LABEL_LINEWIDTH)

    cv2.imwrite(os.path.join(best_outdir, "..", outfile_kmax_overlay_best), best_image)

    print("best images saved to disk:", outfile_kmax_overlay_best)
    print()

    print("All done! Have a nice day :)")

# EOF
