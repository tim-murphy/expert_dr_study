import glob
import os
import sys

from postprocess_subject import postprocess_subject

if __name__  == '__main__':
    if len(sys.argv) < 3:
        print("Usage:", __file__, "<resultsdir> <outdir>")
        sys.exit(1)

    datadir = sys.argv[1]
    if not os.path.exists(datadir):
        print("ERROR: data directory does not exist:", datadir)
        sys.exit(1)

    outdir = sys.argv[2]
    if not os.path.exists(outdir):
        os.mkdir(outdir)

    for subj in glob.glob(os.path.join(datadir, '*')):
        if os.path.isdir(subj):
            subj_id = os.path.split(subj)[1]
            print("   #####", subj, "#####")
            postprocess_subject(subj, os.path.join(outdir, subj_id))
            print("")

    # collate the results
    for exp in ('thinkaloud', 'tracking'): # hardcoded goodness because lazy
        exp_grading_csv = os.path.join(outdir, exp + '_grades.csv')
        with open(exp_grading_csv, 'w') as ofile:
            print("subject_id,file,dr_graded,dmo_graded,dr_actual,dmo_actual", file=ofile)

            for subjdir in glob.glob(os.path.join(outdir, '*')):
                if not os.path.isdir(subjdir):
                    continue

                subj_id = os.path.split(subjdir)[1]

                with open(os.path.join(subjdir, exp, 'grades.csv'), 'r') as ifile:
                    next(ifile) # skip the header row
                    for line in ifile:
                        print(subj_id, line, sep=",", end="", file=ofile)

# EOF
